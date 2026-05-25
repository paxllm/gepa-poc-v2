import { useState, useEffect, useCallback, useMemo } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine,
} from 'recharts';
import {
  listJobs,
  getOptimizationStatus,
  getOptimizationResults,
  getTrainingStatus,
  retrain as retrainApi,
} from '../api/client';
import { displayPromptText } from '../utils/promptDisplay';

const SEED_AUTHORED_SET_ID = 'seed_authored';

function promptsEqual(a, b) {
  return displayPromptText(a) === displayPromptText(b);
}

function OutcomeBadge({ label, variant, title }) {
  return (
    <span className={`badge badge--${variant}`} title={title}>
      {label}
    </span>
  );
}

export default function DashboardPage() {
  const location = useLocation();
  const [jobId, setJobId] = useState(location.state?.jobId || null);
  const [jobs, setJobs] = useState([]);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [pollEnabled, setPollEnabled] = useState(true);
  const [runStartedAt, setRunStartedAt] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [training, setTraining] = useState(null);
  const [retrainBusy, setRetrainBusy] = useState(false);
  const [retrainError, setRetrainError] = useState('');

  useEffect(() => {
    setPollEnabled(true);
  }, [jobId, location.key]);

  useEffect(() => {
    if (isRunning && !runStartedAt) {
      setRunStartedAt(Date.now());
    }
    if (!isRunning) {
      setRunStartedAt(null);
      setElapsedSeconds(0);
    }
  }, [isRunning, runStartedAt]);

  useEffect(() => {
    if (!isRunning || !runStartedAt) return;
    const tick = () => setElapsedSeconds(Math.floor((Date.now() - runStartedAt) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [isRunning, runStartedAt]);

  useEffect(() => {
    listJobs()
      .then((res) => {
        setJobs(res.data);
        if (!jobId && res.data.length > 0) {
          setJobId(res.data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const refreshData = useCallback(async () => {
    if (!jobId) return;

    try {
      const [statusRes, resultsRes, trainingRes] = await Promise.all([
        getOptimizationStatus(jobId),
        getOptimizationResults(jobId),
        getTrainingStatus(jobId).catch(() => ({ data: null })),
      ]);
      setStatus(statusRes.data);
      setResults(resultsRes.data);
      setTraining(trainingRes.data);
      const running = statusRes.data.status === 'running';
      setIsRunning(running);
      if (running) {
        setPollEnabled(true);
      } else {
        setPollEnabled(false);
      }
    } catch {
      setIsRunning(false);
    }
  }, [jobId]);

  const handleRetrain = async () => {
    if (!jobId || retrainBusy || isRunning) return;
    setRetrainBusy(true);
    setRetrainError('');
    try {
      await retrainApi(jobId);
      setPollEnabled(true);
      refreshData();
    } catch (err) {
      setRetrainError(err.response?.data?.detail || 'Failed to start re-training.');
    } finally {
      setRetrainBusy(false);
    }
  };

  useEffect(() => {
    if (!jobId || !pollEnabled) return;

    refreshData();

    const interval = setInterval(refreshData, 3000);
    return () => clearInterval(interval);
  }, [jobId, refreshData, pollEnabled]);

  useEffect(() => {
    if (!jobId || pollEnabled) return;
    refreshData();
  }, [jobId, pollEnabled, refreshData]);

  const splitSummary = results?.split_summary || status?.split_summary;
  const finalMetrics = isRunning ? null : results?.final_metrics;
  const overfitGap = isRunning
    ? status?.overfit_gap
    : (results?.overfit_gap ?? finalMetrics?.overfit_gap);
  const overfitThreshold = results?.overfit_gap_threshold ?? 0.15;
  const showOverfitWarning =
    !isRunning && overfitGap != null && overfitGap > overfitThreshold;

  const metricsData =
    (isRunning ? status?.metrics_history : results?.metrics_history)?.map((m) => ({
      iteration: m.iteration,
      valAccuracy: Number((m.val_accuracy ?? m.accuracy) * 100).toFixed(1),
    })) || [];

  const interimPrompts =
    isRunning && status?.interim_best_prompts?.length > 0
      ? status.interim_best_prompts
      : null;

  const seedByIndex = useMemo(() => {
    const map = {};
    (results?.all_prompts || [])
      .filter(
        (p) => p.generation === 'seed' && p.candidate_set_id !== SEED_AUTHORED_SET_ID
      )
      .forEach((p) => {
        map[p.prompt_index] = p.prompt_text;
      });
    return map;
  }, [results?.all_prompts]);

  const interimMatchesSeed =
    interimPrompts?.length > 0 &&
    interimPrompts.every((p) =>
      promptsEqual(p.prompt_text, seedByIndex[p.prompt_index] ?? p.prompt_text)
    );

  const currentBestByIndex = useMemo(() => {
    const map = {};
    if (interimPrompts) {
      interimPrompts.forEach((p) => {
        map[p.prompt_index] = p.prompt_text;
      });
    } else if (results?.best_prompts?.length) {
      results.best_prompts.forEach((p) => {
        map[p.prompt_index] = p.prompt_text;
      });
    }
    return map;
  }, [interimPrompts, results?.best_prompts]);

  const recentEvolutions = (results?.evolution_log || []).slice(-3).reverse();

  const trainAccFinal = isRunning
    ? null
    : (results?.train_accuracy ?? finalMetrics?.train_accuracy);
  const testAccFinal = isRunning
    ? null
    : (results?.test_accuracy ?? finalMetrics?.test_accuracy);

  const bestValAccuracy = isRunning
    ? (status?.best_accuracy != null
        ? (status.best_accuracy * 100).toFixed(1)
        : '—')
    : (results?.best_accuracy != null
        ? (results.best_accuracy * 100).toFixed(1)
        : status?.best_accuracy != null
          ? (status.best_accuracy * 100).toFixed(1)
          : '—');

  const formatPct = (v) => (v != null ? `${(v * 100).toFixed(1)}%` : '—');

  const stopReason = isRunning
    ? status?.stop_reason
    : (results?.stop_reason || status?.stop_reason);
  const stopReasonLabel = stopReason
    ? stopReason.replace(/_/g, ' ')
    : '—';

  const seedLensCount =
    results?.all_prompts?.filter((p) => p.generation === 'seed').length ||
    (isRunning ? 5 : results?.all_prompts?.length || 0);
  const totalEvolutions = results?.evolution_log?.length || 0;

  const maxMetricCalls = status?.max_metric_calls ?? results?.max_metric_calls;
  const hireThreshold = status?.hire_threshold ?? results?.hire_threshold;
  const totalMetricCalls = status?.total_metric_calls ?? 0;
  const progressPct =
    maxMetricCalls && maxMetricCalls > 0
      ? Math.min(100, (totalMetricCalls / maxMetricCalls) * 100)
      : 0;

  const seedProgress =
    status?.seed_eval_completed != null && status?.seed_eval_total != null
      ? `Evaluating resume ${status.seed_eval_completed} / ${status.seed_eval_total}`
      : null;

  const phaseLabel =
    status?.phase === 'seed_evaluation' || status?.phase === 'starting'
      ? seedProgress ||
        'Evaluating seed candidate on validation set — this may take a few minutes…'
      : status?.phase === 'optimizing'
        ? 'Evolving prompts on the training set…'
        : null;

  const formatElapsed = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const liveEvalOutcomesRaw = isRunning ? (status?.live_eval_outcomes || []) : [];
  const liveEvalOutcomes =
    isRunning && status?.phase === 'optimizing'
      ? liveEvalOutcomesRaw.filter((o) => !o.split || o.split === 'val')
      : liveEvalOutcomesRaw;
  const liveEvalScored = liveEvalOutcomes.filter((o) => !o.eval_error);
  const liveEvalFailed = liveEvalOutcomes.length - liveEvalScored.length;
  const liveEvalCorrect = liveEvalScored.filter((o) => o.is_correct).length;

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">GEPA optimization results &amp; generalization metrics</p>
        </div>
        <div className="flex gap-2 items-center">
          <select
            id="select-job"
            className="form-select"
            value={jobId || ''}
            onChange={(e) => setJobId(parseInt(e.target.value))}
            style={{ width: '250px' }}
          >
            <option value="">Select a job...</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title}
              </option>
            ))}
          </select>
          {status?.status === 'running' && (
            <span className="badge badge--warning flex gap-2 items-center">
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
              Running...
            </span>
          )}
          {isRunning && (
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
              }}
            >
              Live · updates every 3s
            </span>
          )}
          <button
            className="btn btn--secondary"
            onClick={handleRetrain}
            disabled={
              !jobId ||
              isRunning ||
              retrainBusy ||
              !training?.has_active_best_prompts
            }
            title={
              !training?.has_active_best_prompts
                ? 'Run /optimize first to produce an active best prompt set'
                : 'Warm-start a new GEPA run seeded with the current best prompts'
            }
          >
            {retrainBusy ? 'Starting…' : 'Re-train now'}
          </button>
        </div>
      </div>

      {retrainError && (
        <div className="card mb-6" style={{ borderColor: 'var(--color-danger)' }}>
          {retrainError}
        </div>
      )}

      {training && (
        <div
          className="card mb-6"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div className="metric-card__label">Live candidates</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
              {training.decisions_since_last_train} / {training.auto_retrain_threshold}{' '}
              decisions since last train
            </div>
            <div className="metric-card__trend">
              {training.last_optimized_at
                ? `Last optimized at ${new Date(training.last_optimized_at).toLocaleString()}`
                : 'No optimization run yet.'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <Link to="/score" className="btn btn--primary">
              Score new candidate
            </Link>
            <Link to="/pending" className="btn btn--ghost">
              Pending decisions
            </Link>
          </div>
        </div>
      )}

      {splitSummary && (
        <div className="card mb-6">
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Dataset split:{' '}
            <strong>{splitSummary.train}</strong> train /{' '}
            <strong>{splitSummary.val}</strong> val /{' '}
            <strong>{splitSummary.test}</strong> test
            {!splitSummary.assigned && ' (splits assigned at optimization start)'}
          </div>
        </div>
      )}

      {status?.status === 'running' && (
        <div className="card mb-6 animate-pulse-glow">
          <div className="flex items-center gap-4">
            <div className="spinner" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>Optimization in Progress</div>
              {(maxMetricCalls != null || hireThreshold != null) && (
                <div
                  style={{
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-muted)',
                    marginTop: 'var(--spacing-1)',
                  }}
                >
                  {maxMetricCalls != null && (
                    <>Max metric calls: <strong>{maxMetricCalls}</strong></>
                  )}
                  {maxMetricCalls != null && hireThreshold != null && ' · '}
                  {hireThreshold != null && (
                    <>Hire threshold: <strong>{hireThreshold}</strong></>
                  )}
                </div>
              )}
              {phaseLabel && (
                <div
                  style={{
                    color: 'var(--color-text-accent)',
                    fontSize: 'var(--font-size-sm)',
                    marginTop: 'var(--spacing-1)',
                  }}
                >
                  {phaseLabel}
                </div>
              )}
              <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--spacing-1)' }}>
                {runStartedAt != null && (
                  <>Elapsed {formatElapsed(elapsedSeconds)}. </>
                )}
                {status.current_iteration != null && (
                  <>Iteration {status.current_iteration}. </>
                )}
                {status.total_metric_calls != null && maxMetricCalls != null && (
                  <>
                    {status.total_metric_calls} / {maxMetricCalls} metric calls used.
                    {' '}
                  </>
                )}
                {status.best_accuracy != null && (
                  <>Best val accuracy {(status.best_accuracy * 100).toFixed(1)}%.</>
                )}
              </div>
              {maxMetricCalls != null && maxMetricCalls > 0 && (
                <div style={{ marginTop: 'var(--spacing-3)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-text-muted)',
                      marginBottom: 'var(--spacing-1)',
                    }}
                  >
                    <span>Budget used</span>
                    <span>{progressPct.toFixed(0)}%</span>
                  </div>
                  <div
                    style={{
                      height: 8,
                      borderRadius: 4,
                      background: 'var(--color-bg-input)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${progressPct}%`,
                        background: 'var(--color-primary)',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {isRunning && liveEvalOutcomes.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">
              {status?.phase === 'optimizing'
                ? 'Live Validation Outcomes'
                : 'Live Evaluation Outcomes'}
            </h3>
            <span className="card__subtitle">
              {liveEvalCorrect} / {liveEvalScored.length} correct
              {status?.phase === 'optimizing' ? ' on validation set' : ' so far'}
              {liveEvalFailed > 0 && ` · ${liveEvalFailed} failed`}
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Candidate</th>
                {status?.phase === 'optimizing' && <th>Split</th>}
                <th>Predicted</th>
                <th>Actual</th>
                <th>Score</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {[...liveEvalOutcomes].reverse().map((outcome, idx) => (
                <tr key={`${outcome.resume_id ?? 'unknown'}-${liveEvalOutcomes.length - idx}`}>
                  <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                    {liveEvalOutcomes.length - idx}
                  </td>
                  <td>{outcome.candidate_name || `Resume ${outcome.resume_id ?? '?'}`}</td>
                  {status?.phase === 'optimizing' && (
                    <td style={{ fontSize: 'var(--font-size-xs)', textTransform: 'capitalize' }}>
                      {outcome.split || '—'}
                    </td>
                  )}
                  <td>
                    <OutcomeBadge
                      label={outcome.prediction}
                      variant={outcome.prediction === 'Hired' ? 'success' : 'danger'}
                    />
                  </td>
                  <td>
                    <OutcomeBadge
                      label={outcome.actual_label}
                      variant={outcome.actual_label === 'Hired' ? 'success' : 'danger'}
                    />
                  </td>
                  <td style={{ fontSize: 'var(--font-size-sm)' }}>
                    {outcome.eval_error
                      ? '—'
                      : outcome.aggregate_score != null
                        ? outcome.aggregate_score.toFixed(2)
                        : '—'}
                  </td>
                  <td>
                    {outcome.eval_error ? (
                      <OutcomeBadge label="Error" variant="warning" title={outcome.eval_error} />
                    ) : (
                      <OutcomeBadge
                        label={outcome.is_correct ? 'Correct' : 'Wrong'}
                        variant={outcome.is_correct ? 'success' : 'danger'}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isRunning && metricsData.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Live Validation Accuracy</h3>
            <span className="badge badge--warning">In progress</span>
          </div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(244, 156, 38, 0.15)" />
                <XAxis
                  dataKey="iteration"
                  stroke="#6b7071"
                  fontSize={12}
                  label={{ value: 'Iteration', position: 'insideBottom', offset: -5, fill: '#6b7071' }}
                />
                <YAxis
                  stroke="#6b7071"
                  fontSize={12}
                  domain={[0, 100]}
                  label={{ value: 'Accuracy %', angle: -90, position: 'insideLeft', fill: '#6b7071' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid rgba(244, 156, 38, 0.4)',
                    borderRadius: '8px',
                    color: '#1f2324',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="valAccuracy"
                  name="Val accuracy"
                  stroke="#F49C26"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#F49C26' }}
                  activeDot={{ r: 6, fill: '#B76900' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {isRunning && interimPrompts && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Current Best Prompts</h3>
            <span className={`badge ${interimMatchesSeed && totalEvolutions > 0 ? 'badge--warning' : 'badge--info'}`}>
              {interimMatchesSeed && totalEvolutions > 0 ? 'Seed (still best on val)' : 'Interim'}
            </span>
          </div>
          {interimMatchesSeed && totalEvolutions > 0 && (
            <p
              style={{
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-sm)',
                marginBottom: 'var(--spacing-4)',
              }}
            >
              Mutations are being tested on training data; promotion requires beating seed on validation.
            </p>
          )}
          {interimPrompts.map((lens) => (
            <div
              key={lens.prompt_index}
              style={{
                background: 'var(--color-bg-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-4)',
                marginBottom: 'var(--spacing-3)',
              }}
            >
              <span className="badge badge--info" style={{ fontSize: 'var(--font-size-xs)' }}>
                Prompt {lens.prompt_index}
              </span>
              <div
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.7,
                  marginTop: 'var(--spacing-2)',
                }}
              >
                {displayPromptText(lens.prompt_text)}
              </div>
            </div>
          ))}
        </div>
      )}

      {recentEvolutions.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Recent Prompt Mutations</h3>
            <span className="card__subtitle">
              {isRunning ? 'Latest changes as GEPA runs' : 'Mutations from the last run'}
            </span>
          </div>
          {recentEvolutions.map((entry) => {
            const currentBest = currentBestByIndex[entry.prompt_index];
            const isPromoted =
              entry.promoted ??
              (currentBest != null && promptsEqual(entry.evolved_prompt, currentBest));
            return (
            <div
              key={entry.id}
              style={{
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: 'var(--spacing-4)',
                marginBottom: 'var(--spacing-4)',
              }}
            >
              <div className="flex gap-2 mb-2">
                <span className="badge badge--warning">Iteration {entry.iteration}</span>
                <span className="badge badge--info">Prompt {entry.prompt_index}</span>
                <span className={`badge ${isPromoted ? 'badge--success' : 'badge--secondary'}`}>
                  {isPromoted ? 'Promoted' : 'Explored — not yet promoted'}
                </span>
              </div>
              <div
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.6,
                }}
              >
                {displayPromptText(entry.evolved_prompt)}
              </div>
            </div>
            );
          })}
        </div>
      )}

      {status?.status === 'error' && (
        <div className="card mb-6" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <div style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Optimization Failed</div>
          <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: '4px' }}>
            {status.error_message}
          </div>
        </div>
      )}

      {showOverfitWarning && (
        <div className="card mb-6" style={{ borderColor: 'rgba(245, 158, 11, 0.4)' }}>
          <div style={{ color: '#f59e0b', fontWeight: 600 }}>Possible Overfitting</div>
          <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: '4px' }}>
            Train–val gap is {(overfitGap * 100).toFixed(1)}% (threshold {(overfitThreshold * 100).toFixed(0)}%).
            Validation accuracy may not generalize — consider stopping earlier or adding more training data.
          </div>
        </div>
      )}

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-card__label">Best Val Accuracy</div>
          <div className="metric-card__value">{bestValAccuracy}{bestValAccuracy !== '—' ? '%' : ''}</div>
        </div>
        {!isRunning && (
          <>
            <div className="metric-card">
              <div className="metric-card__label">Test Accuracy</div>
              <div className="metric-card__value">{formatPct(testAccFinal)}</div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Overfit Gap</div>
              <div className="metric-card__value">
                {overfitGap != null ? `${(overfitGap * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Stop Reason</div>
              <div className="metric-card__value" style={{ fontSize: 'var(--font-size-lg)', textTransform: 'capitalize' }}>
                {stopReasonLabel}
              </div>
            </div>
          </>
        )}
        {isRunning && (
          <>
            <div className="metric-card">
              <div className="metric-card__label">Max Metric Calls</div>
              <div className="metric-card__value">{maxMetricCalls ?? '—'}</div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Hire Threshold</div>
              <div className="metric-card__value">{hireThreshold ?? '—'}</div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Metric Calls</div>
              <div className="metric-card__value">
                {maxMetricCalls != null
                  ? `${totalMetricCalls} / ${maxMetricCalls}`
                  : totalMetricCalls}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Iteration</div>
              <div className="metric-card__value">{status?.current_iteration ?? 0}</div>
            </div>
          </>
        )}
        <div className="metric-card">
          <div className="metric-card__label">{isRunning ? 'Seed Lenses' : 'Prompt Records'}</div>
          <div className="metric-card__value">{seedLensCount}</div>
        </div>
        <div className="metric-card">
          <div className="metric-card__label">Evolutions</div>
          <div className="metric-card__value">{totalEvolutions}</div>
        </div>
      </div>

      {metricsData.length > 0 && !isRunning && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Validation Accuracy Trend</h3>
            {trainAccFinal != null && testAccFinal != null && (
              <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                Final train {formatPct(trainAccFinal)} · test {formatPct(testAccFinal)}
              </span>
            )}
          </div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(244, 156, 38, 0.15)" />
                <XAxis
                  dataKey="iteration"
                  stroke="#6b7071"
                  fontSize={12}
                  label={{ value: 'Iteration', position: 'insideBottom', offset: -5, fill: '#6b7071' }}
                />
                <YAxis
                  stroke="#6b7071"
                  fontSize={12}
                  domain={[0, 100]}
                  label={{ value: 'Accuracy %', angle: -90, position: 'insideLeft', fill: '#6b7071' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid rgba(244, 156, 38, 0.4)',
                    borderRadius: '8px',
                    color: '#1f2324',
                  }}
                />
                {trainAccFinal != null && (
                  <ReferenceLine
                    y={trainAccFinal * 100}
                    stroke="#22c55e"
                    strokeDasharray="4 4"
                    label={{ value: 'Train (final)', fill: '#22c55e', fontSize: 11 }}
                  />
                )}
                {testAccFinal != null && (
                  <ReferenceLine
                    y={testAccFinal * 100}
                    stroke="#f59e0b"
                    strokeDasharray="4 4"
                    label={{ value: 'Test (final)', fill: '#f59e0b', fontSize: 11 }}
                  />
                )}
                <Line
                  type="monotone"
                  dataKey="valAccuracy"
                  name="Val accuracy"
                  stroke="#F49C26"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#F49C26' }}
                  activeDot={{ r: 6, fill: '#B76900' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {!isRunning && results?.best_prompts?.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Best Evolved Prompts</h3>
            <span className="badge badge--success">
              Set: {results.best_candidate_set_id}
            </span>
          </div>
          {results.best_prompts.map((lens) => (
            <div
              key={lens.id}
              style={{
                background: 'var(--color-bg-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-4)',
                marginBottom: 'var(--spacing-3)',
              }}
            >
              <div className="flex justify-between items-center mb-4">
                <span className="badge badge--info" style={{ fontSize: 'var(--font-size-xs)' }}>
                  Prompt {lens.prompt_index}
                </span>
                <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                  {lens.generation} · Iteration {lens.iteration}
                </span>
              </div>
              <div
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-secondary)',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.7,
                }}
              >
                {displayPromptText(lens.prompt_text)}
              </div>
            </div>
          ))}
        </div>
      )}

      {!isRunning &&
        !results?.metrics_history?.length &&
        !results?.best_prompts?.length &&
        status?.status !== 'running' && (
        <div className="card text-center" style={{ padding: 'var(--spacing-12)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-4)', opacity: 0.3 }}>
            📊
          </div>
          <div style={{ color: 'var(--color-text-secondary)' }}>
            No optimization results yet. Run the Setup Wizard to get started.
          </div>
        </div>
      )}
    </div>
  );
}
