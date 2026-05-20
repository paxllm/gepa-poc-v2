import { useState, useEffect, useCallback } from 'react';
import { listJobs, getOptimizationResults, getOptimizationStatus } from '../api/client';
import { displayPromptText } from '../utils/promptDisplay';

const SEED_AUTHORED_SET_ID = 'seed_authored';

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

  const filteredLog = selectedPromptIndex !== null
    ? evolutionLog.filter((e) => e.prompt_index === selectedPromptIndex)
    : evolutionLog;

  const seedPrompts = allPrompts
    .filter(
      (p) => p.generation === 'seed' && p.candidate_set_id !== SEED_AUTHORED_SET_ID
    )
    .sort((a, b) => a.prompt_index - b.prompt_index);

  const filteredSeedPrompts =
    selectedPromptIndex !== null
      ? seedPrompts.filter((p) => p.prompt_index === selectedPromptIndex)
      : seedPrompts;

  const interimPrompts =
    isRunning && status?.interim_best_prompts?.length > 0
      ? status.interim_best_prompts
      : null;

  const filteredInterimPrompts =
    interimPrompts && selectedPromptIndex !== null
      ? interimPrompts.filter((p) => p.prompt_index === selectedPromptIndex)
      : interimPrompts;

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
                    {status.total_metric_calls} / {status.max_metric_calls} val evaluations ·{' '}
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
        {[1, 2, 3, 4, 5].map((idx) => (
          <button
            key={idx}
            className={`btn ${selectedPromptIndex === idx ? 'btn--primary' : 'btn--secondary'}`}
            onClick={() => setSelectedPromptIndex(idx)}
          >
            Prompt {idx}
          </button>
        ))}
      </div>

      {isRunning && filteredSeedPrompts.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Seed Prompts (current)</h3>
            <span className="badge badge--info">Baseline</span>
          </div>
          <p
            style={{
              color: 'var(--color-text-muted)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--spacing-4)',
            }}
          >
            Job description and core values are shared context injected at evaluation time.
          </p>
          {filteredSeedPrompts.map((lens) => (
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

      {filteredInterimPrompts && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Current Best Prompts</h3>
            <span className="badge badge--success">Interim</span>
          </div>
          {filteredInterimPrompts.map((lens) => (
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
              <span className="badge badge--success" style={{ fontSize: 'var(--font-size-xs)' }}>
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

      {candidateSetList.length > 0 && (
        <div className="card mb-6">
          <div className="card__header">
            <h3 className="card__title">Candidate Sets</h3>
            <span className="card__subtitle">{candidateSetList.length} sets generated</span>
          </div>
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
                    background: set.generation === 'evolved'
                      ? 'var(--gradient-subtle)'
                      : 'var(--color-bg-card)',
                  }}
                >
                  <div className="flex justify-between items-center mb-4">
                    <span className={`badge ${set.generation === 'seed' ? 'badge--info' : 'badge--success'}`}>
                      {set.generation}
                    </span>
                    {set.fitness != null && set.fitness !== undefined && (
                      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        Score: {(set.fitness * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', wordBreak: 'break-all', marginBottom: 'var(--spacing-3)' }}>
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
      )}

      {filteredLog.length > 0 ? (
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
                  <span className="badge badge--warning">
                    Iteration {entry.iteration}
                  </span>
                  <span className="badge badge--info">
                    Prompt {entry.prompt_index}
                  </span>
                </div>
              </div>

              <div className="prompt-diff">
                <div className="prompt-diff__panel">
                  <div className="prompt-diff__label prompt-diff__label--before">
                    Before
                  </div>
                  <div className="prompt-diff__text">
                    {displayPromptText(entry.original_prompt) || 'N/A'}
                  </div>
                </div>
                <div className="prompt-diff__panel">
                  <div className="prompt-diff__label prompt-diff__label--after">
                    After
                  </div>
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
                    💡 GEPA Reflection
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
      ) : (
        <div className="card text-center" style={{ padding: 'var(--spacing-12)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-4)', opacity: 0.3 }}>
            🧬
          </div>
          <div style={{ color: 'var(--color-text-secondary)' }}>
            {isRunning
              ? 'No prompt evolutions recorded yet — mutations will appear here as GEPA runs.'
              : results
                ? 'No prompt evolutions recorded yet.'
                : 'Select a job to view evolution history.'}
          </div>
        </div>
      )}
    </div>
  );
}
