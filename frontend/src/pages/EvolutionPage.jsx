import { useState, useEffect, useCallback, useMemo } from 'react';
import { listJobs, getOptimizationResults, getOptimizationStatus } from '../api/client';
import { displayPromptText } from '../utils/promptDisplay';

const SEED_AUTHORED_SET_ID = 'seed_authored';
const PROMPT_INDICES = [1, 2, 3, 4, 5];

function promptsEqual(a, b) {
  return displayPromptText(a) === displayPromptText(b);
}

function FlowArrow() {
  return <div className="prompt-flow__arrow" aria-hidden="true">→</div>;
}

function FlowStep({ label, labelClass, badge, text }) {
  return (
    <div className={`prompt-flow__step ${labelClass === 'current' ? 'prompt-flow__step--current' : ''}`}>
      <div className="flex justify-between items-center mb-2">
        <div className={`prompt-flow__label prompt-flow__label--${labelClass}`}>{label}</div>
        {badge}
      </div>
      <div className="prompt-flow__text">{displayPromptText(text)}</div>
    </div>
  );
}

export default function EvolutionPage() {
  const [jobId, setJobId] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [pollEnabled, setPollEnabled] = useState(true);
  const [selectedPromptIndex, setSelectedPromptIndex] = useState(null);

  useEffect(() => {
    setPollEnabled(true);
  }, [jobId]);

  useEffect(() => {
    listJobs()
      .then((res) => {
        setJobs(res.data);
        if (res.data.length > 0) setJobId(res.data[0].id);
      })
      .catch(console.error);
  }, []);

  const refreshData = useCallback(async () => {
    if (!jobId) return;

    try {
      const [statusRes, resultsRes] = await Promise.all([
        getOptimizationStatus(jobId),
        getOptimizationResults(jobId),
      ]);
      setStatus(statusRes.data);
      setResults(resultsRes.data);
      const running = statusRes.data.status === 'running';
      setIsRunning(running);
      setPollEnabled(running);
    } catch {
      setIsRunning(false);
    }
  }, [jobId]);

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

  const evolutionLog = results?.evolution_log || [];
  const allPrompts = results?.all_prompts || [];

  const candidateSets = {};
  allPrompts.forEach((p) => {
    if (p.candidate_set_id === SEED_AUTHORED_SET_ID) return;
    if (!candidateSets[p.candidate_set_id]) {
      candidateSets[p.candidate_set_id] = {
        id: p.candidate_set_id,
        generation: p.generation,
        iteration: p.iteration,
        fitness: p.fitness_score,
        prompts: [],
      };
    }
    candidateSets[p.candidate_set_id].prompts.push(p);
  });

  const candidateSetList = Object.values(candidateSets).sort(
    (a, b) => a.iteration - b.iteration
  );

  const filteredLog =
    selectedPromptIndex !== null
      ? evolutionLog.filter((e) => e.prompt_index === selectedPromptIndex)
      : evolutionLog;

  const seedPrompts = allPrompts
    .filter(
      (p) => p.generation === 'seed' && p.candidate_set_id !== SEED_AUTHORED_SET_ID
    )
    .sort((a, b) => a.prompt_index - b.prompt_index);

  const seedByIndex = useMemo(() => {
    const map = {};
    seedPrompts.forEach((p) => {
      map[p.prompt_index] = p.prompt_text;
    });
    return map;
  }, [seedPrompts]);

  const currentByIndex = useMemo(() => {
    const map = { ...seedByIndex };

    if (isRunning && status?.interim_best_prompts?.length > 0) {
      status.interim_best_prompts.forEach((p) => {
        map[p.prompt_index] = p.prompt_text;
      });
      return map;
    }

    const bestSetId = results?.best_candidate_set_id;
    const finalPrompts = (results?.best_prompts || []).filter(
      (p) => !bestSetId || p.candidate_set_id === bestSetId || p.is_active
    );
    finalPrompts.forEach((p) => {
      map[p.prompt_index] = p.prompt_text;
    });
    return map;
  }, [seedByIndex, isRunning, status?.interim_best_prompts, results?.best_prompts, results?.best_candidate_set_id]);

  const visibleIndices =
    selectedPromptIndex !== null
      ? [selectedPromptIndex]
      : PROMPT_INDICES.filter((idx) => seedByIndex[idx] != null);

  const mutationsByIndex = useMemo(() => {
    const grouped = {};
    filteredLog.forEach((entry) => {
      if (!grouped[entry.prompt_index]) grouped[entry.prompt_index] = [];
      grouped[entry.prompt_index].push(entry);
    });
    Object.values(grouped).forEach((entries) =>
      entries.sort((a, b) => a.iteration - b.iteration)
    );
    return grouped;
  }, [filteredLog]);

  const changedIndices = visibleIndices.filter((idx) => {
    const seed = seedByIndex[idx];
    const current = currentByIndex[idx];
    if (seed == null) return false;
    return !promptsEqual(seed, current ?? seed);
  });

  const exploredIndices = visibleIndices.filter((idx) => {
    const mutations = mutationsByIndex[idx];
    return mutations && mutations.length > 0;
  });

  const hasSeedData = seedPrompts.length > 0;
  const allUnchanged =
    hasSeedData &&
    visibleIndices.length > 0 &&
    visibleIndices.every((idx) => {
      const seed = seedByIndex[idx];
      if (seed == null) return true;
      return promptsEqual(seed, currentByIndex[idx] ?? seed);
    });

  const globalAllUnchanged =
    hasSeedData &&
    PROMPT_INDICES.filter((idx) => seedByIndex[idx] != null).every((idx) =>
      promptsEqual(seedByIndex[idx], currentByIndex[idx] ?? seedByIndex[idx])
    );

  const mutationsOnOtherPrompts =
    selectedPromptIndex !== null &&
    allUnchanged &&
    !globalAllUnchanged &&
    evolutionLog.some((e) => e.prompt_index !== selectedPromptIndex);

  const showFlow = changedIndices.length > 0 || exploredIndices.length > 0;
  const showDiffs = filteredLog.length > 0;
  const showStatusBanner = hasSeedData && (filteredLog.length === 0 || allUnchanged || mutationsOnOtherPrompts);

  const statusBannerMessage = (() => {
    if (mutationsOnOtherPrompts) {
      const otherCount = evolutionLog.filter(
        (e) => e.prompt_index !== selectedPromptIndex
      ).length;
      return `Prompt ${selectedPromptIndex} unchanged; ${otherCount} mutation${otherCount !== 1 ? 's' : ''} on other prompts.`;
    }
    if (filteredLog.length === 0) {
      return isRunning
        ? 'No prompt mutations recorded yet.'
        : 'No prompt mutations were recorded during this run.';
    }
    if (allUnchanged) {
      const count = filteredLog.length;
      return `GEPA explored ${count} mutation${count !== 1 ? 's' : ''}; seed prompts still score highest on the validation set.`;
    }
    return null;
  })();

  const seedProgress =
    status?.seed_eval_completed != null && status?.seed_eval_total != null
      ? `Evaluating resume ${status.seed_eval_completed} / ${status.seed_eval_total}`
      : null;

  const phaseLabel =
    status?.phase === 'generating_seed'
      ? 'Generating seed prompts from your angles, job description, and core values…'
      : status?.phase === 'seed_evaluation' || status?.phase === 'starting'
        ? seedProgress || 'Evaluating seed candidate on validation set…'
        : status?.phase === 'optimizing'
          ? 'Recording prompt mutations as GEPA runs…'
          : null;

  const filterPromptsByIndex = (prompts) =>
    selectedPromptIndex !== null
      ? prompts.filter((p) => p.prompt_index === selectedPromptIndex)
      : prompts;

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="page-title">Prompt Evolution</h1>
          <p className="page-subtitle">Explore how prompts evolved across GEPA iterations</p>
        </div>
        <select
          id="select-job-evo"
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
        {isRunning && (
          <span className="badge badge--warning flex gap-2 items-center">
            <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
            Live updates
          </span>
        )}
      </div>

      {isRunning && (
        <div className="card mb-6 animate-pulse-glow">
          <div className="flex items-center gap-4">
            <div className="spinner" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>Optimization in Progress</div>
              {(status?.max_metric_calls != null || status?.hire_threshold != null) && (
                <div
                  style={{
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-muted)',
                    marginTop: 'var(--spacing-1)',
                  }}
                >
                  {status?.max_metric_calls != null && (
                    <>Max metric calls: <strong>{status.max_metric_calls}</strong></>
                  )}
                  {status?.max_metric_calls != null && status?.hire_threshold != null && ' · '}
                  {status?.hire_threshold != null && (
                    <>Hire threshold: <strong>{status.hire_threshold}</strong></>
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
              <div
                style={{
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--font-size-sm)',
                  marginTop: 'var(--spacing-1)',
                }}
              >
                {status?.total_metric_calls != null && status?.max_metric_calls != null && (
                  <>
                    {status.total_metric_calls} / {status.max_metric_calls} metric calls used ·{' '}
                  </>
                )}
                {filteredLog.length} mutation{filteredLog.length !== 1 ? 's' : ''} recorded so far
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2 mb-6">
        <button
          className={`btn ${selectedPromptIndex === null ? 'btn--primary' : 'btn--secondary'}`}
          onClick={() => setSelectedPromptIndex(null)}
        >
          All Prompts
        </button>
        {PROMPT_INDICES.map((idx) => (
          <button
            key={idx}
            className={`btn ${selectedPromptIndex === idx ? 'btn--primary' : 'btn--secondary'}`}
            onClick={() => setSelectedPromptIndex(idx)}
          >
            Prompt {idx}
          </button>
        ))}
      </div>

      {!jobId && (
        <div className="card text-center" style={{ padding: 'var(--spacing-12)' }}>
          <div style={{ color: 'var(--color-text-secondary)' }}>
            Select a job to view evolution history.
          </div>
        </div>
      )}

      {jobId && !hasSeedData && !isRunning && (
        <div className="card text-center" style={{ padding: 'var(--spacing-12)' }}>
          <div style={{ color: 'var(--color-text-secondary)' }}>
            No optimization run yet. Run the Setup Wizard to start GEPA evolution.
          </div>
        </div>
      )}

      {showStatusBanner && statusBannerMessage && (
        <div className="card mb-6 text-center" style={{ padding: 'var(--spacing-8)' }}>
          <div style={{ color: 'var(--color-text-secondary)' }}>
            {statusBannerMessage}
          </div>
        </div>
      )}

      {showFlow && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Prompt Evolution Flow</h3>
            <span className="badge badge--info">
              {changedIndices.length > 0 ? 'Seed → Current' : 'Explored Mutations'}
            </span>
          </div>
          <p
            style={{
              color: 'var(--color-text-muted)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--spacing-4)',
            }}
          >
            Job description and core values are shared context injected at evaluation time.
            {allUnchanged && exploredIndices.length > 0 && (
              <> Mutations below were explored but did not beat the seed on validation.</>
            )}
          </p>
          {(changedIndices.length > 0 ? changedIndices : exploredIndices).map((idx) => {
            const mutations = mutationsByIndex[idx] || [];
            const seed = seedByIndex[idx];
            const current = currentByIndex[idx] ?? seed;
            const isPromoted = !promptsEqual(seed, current);
            return (
              <div key={idx}>
                <div className="prompt-flow-index-title">Prompt {idx}</div>
                <div className="prompt-flow">
                  <FlowStep
                    label="Seed"
                    labelClass="seed"
                    badge={
                      <span className="badge badge--info" style={{ fontSize: 'var(--font-size-xs)' }}>
                        Baseline
                      </span>
                    }
                    text={seed}
                  />
                  {mutations.map((entry) => (
                    <span key={entry.id} style={{ display: 'contents' }}>
                      <FlowArrow />
                      <FlowStep
                        label={`Iteration ${entry.iteration}`}
                        labelClass="mutation"
                        badge={
                          <span
                            className={`badge ${entry.promoted ? 'badge--success' : 'badge--warning'}`}
                            style={{ fontSize: 'var(--font-size-xs)' }}
                          >
                            {entry.promoted ? 'Promoted' : 'Not promoted'}
                          </span>
                        }
                        text={entry.evolved_prompt}
                      />
                    </span>
                  ))}
                  {isPromoted && (
                    <>
                      <FlowArrow />
                      <FlowStep
                        label={isRunning ? 'Current Best' : 'Final Best'}
                        labelClass="current"
                        badge={
                          <span className="badge badge--success" style={{ fontSize: 'var(--font-size-xs)' }}>
                            {isRunning ? 'Interim' : 'Final'}
                          </span>
                        }
                        text={current}
                      />
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showDiffs && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Evolution History</h3>
            <span className="card__subtitle">{filteredLog.length} mutations</span>
          </div>
          {filteredLog.map((entry) => (
            <div
              key={entry.id}
              className="mb-6 animate-slide-in"
              style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--spacing-6)' }}
            >
              <div className="flex justify-between items-center mb-4">
                <div className="flex gap-2 items-center">
                  <span className="badge badge--warning">Iteration {entry.iteration}</span>
                  <span className="badge badge--info">Prompt {entry.prompt_index}</span>
                  {entry.promoted != null && (
                    <span className={`badge ${entry.promoted ? 'badge--success' : 'badge--secondary'}`}>
                      {entry.promoted ? 'Promoted' : 'Explored only'}
                    </span>
                  )}
                </div>
              </div>

              <div className="prompt-diff">
                <div className="prompt-diff__panel">
                  <div className="prompt-diff__label prompt-diff__label--before">Before</div>
                  <div className="prompt-diff__text">
                    {displayPromptText(entry.original_prompt) || 'N/A'}
                  </div>
                </div>
                <div className="prompt-diff__panel">
                  <div className="prompt-diff__label prompt-diff__label--after">After</div>
                  <div className="prompt-diff__text">
                    {displayPromptText(entry.evolved_prompt)}
                  </div>
                </div>
              </div>

              {entry.reflection_reasoning && (
                <div
                  style={{
                    marginTop: 'var(--spacing-3)',
                    background: 'rgba(244, 156, 38, 0.06)',
                    border: '1px solid rgba(244, 156, 38, 0.2)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--spacing-3)',
                  }}
                >
                  <div
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      fontWeight: 600,
                      color: 'var(--color-text-accent)',
                      marginBottom: 'var(--spacing-1)',
                    }}
                  >
                    GEPA Reflection
                  </div>
                  <div
                    style={{
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-secondary)',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {entry.reflection_reasoning}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {candidateSetList.length > 0 && (
        <details className="advanced-section">
          <summary>Advanced — all candidate sets ({candidateSetList.length})</summary>
          <div className="advanced-section__body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
              {candidateSetList.map((set) => {
                const visiblePrompts = filterPromptsByIndex(
                  [...set.prompts].sort((a, b) => a.prompt_index - b.prompt_index)
                );
                if (visiblePrompts.length === 0) return null;
                return (
                  <div
                    key={set.id}
                    className="card"
                    style={{
                      background:
                        set.generation === 'evolved'
                          ? 'var(--gradient-subtle)'
                          : 'var(--color-bg-card)',
                    }}
                  >
                    <div className="flex justify-between items-center mb-4">
                      <span
                        className={`badge ${set.generation === 'seed' ? 'badge--info' : 'badge--success'}`}
                      >
                        {set.generation}
                      </span>
                      {set.fitness != null && set.fitness !== undefined && (
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                          Score: {(set.fitness * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: 'var(--font-size-xs)',
                        color: 'var(--color-text-muted)',
                        wordBreak: 'break-all',
                        marginBottom: 'var(--spacing-3)',
                      }}
                    >
                      {set.id} · {visiblePrompts.length} prompt{visiblePrompts.length !== 1 ? 's' : ''}
                    </div>
                    {visiblePrompts.map((p) => (
                      <div
                        key={p.id}
                        style={{
                          background: 'var(--color-bg-input)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 'var(--radius-md)',
                          padding: 'var(--spacing-3)',
                          marginBottom: 'var(--spacing-2)',
                        }}
                      >
                        <span className="badge badge--info" style={{ fontSize: 'var(--font-size-xs)' }}>
                          Prompt {p.prompt_index}
                        </span>
                        <div
                          style={{
                            fontSize: 'var(--font-size-sm)',
                            color: 'var(--color-text-secondary)',
                            whiteSpace: 'pre-wrap',
                            lineHeight: 1.6,
                            marginTop: 'var(--spacing-2)',
                            maxHeight: '240px',
                            overflowY: 'auto',
                          }}
                        >
                          {displayPromptText(p.prompt_text)}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </details>
      )}
    </div>
  );
}
