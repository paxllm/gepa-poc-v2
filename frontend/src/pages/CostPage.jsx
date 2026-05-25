import { useState, useEffect, useCallback } from 'react';
import { listJobs, getJobCosts } from '../api/client';

const USD = (n) =>
  n === undefined || n === null
    ? '—'
    : n < 0.0001
    ? `$${n.toFixed(7)}`
    : `$${n.toFixed(4)}`;

const NUM = (n) =>
  n === undefined || n === null ? '—' : n.toLocaleString();

const AVG = (n) =>
  n === undefined || n === null ? '—' : Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

const PCT = (n) =>
  n === undefined || n === null
    ? '—'
    : n >= 0
    ? `↓ ${n.toFixed(1)}%`
    : `↑ ${Math.abs(n).toFixed(1)}%`;

const CALL_TYPE_LABELS = {
  evaluation:      { label: 'Evaluation',      color: '#6366f1', desc: 'Resume scored against each talent lens during training' },
  reflection:      { label: 'Reflection',       color: '#f59e0b', desc: 'LLM reasoning about mismatches to propose prompt mutations' },
  seed_generation: { label: 'Seed Generation',  color: '#10b981', desc: 'Initial LLM call to expand prompts against the job description' },
  scoring:         { label: 'Live Scoring',      color: '#3b82f6', desc: 'On-demand scoring of a new candidate via the Score page' },
  unknown:         { label: 'Other',             color: '#9ca3af', desc: 'Unclassified calls' },
};

const PROVIDER_COLORS = {
  Amazon:    '#f97316',
  Anthropic: '#6366f1',
  Meta:      '#3b82f6',
  Mistral:   '#10b981',
};

function MetricCard({ title, value, sub, accent, badge }) {
  return (
    <div style={{
      background: '#1e1e2e',
      border: `1px solid ${accent || '#374151'}`,
      borderRadius: 10,
      padding: '18px 22px',
      flex: 1,
      minWidth: 140,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</span>
        {badge && <span style={{ fontSize: 10, background: accent + '30', color: accent, borderRadius: 3, padding: '1px 5px', fontWeight: 600 }}>{badge}</span>}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: accent || '#f3f4f6' }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function BarSegment({ pct, color, label, tokens }) {
  if (pct <= 0) return null;
  return (
    <div
      title={`${label}: ${NUM(tokens)} tokens (${pct.toFixed(1)}%)`}
      style={{
        width: `${pct}%`, background: color, height: '100%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 600, color: '#fff',
        overflow: 'hidden', whiteSpace: 'nowrap', minWidth: pct > 8 ? 'auto' : 0,
      }}
    >
      {pct > 8 ? `${pct.toFixed(0)}%` : ''}
    </div>
  );
}

function SectionHeader({ children, accent }) {
  return (
    <h2 style={{
      fontSize: 14, fontWeight: 600, color: accent || '#e5e7eb',
      margin: '32px 0 12px', borderBottom: `1px solid ${accent ? accent + '40' : '#374151'}`,
      paddingBottom: 8, display: 'flex', alignItems: 'center', gap: 8,
    }}>
      {children}
    </h2>
  );
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', padding: '48px 0', color: '#6b7280' }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>📊</div>
      <div style={{ fontSize: 15 }}>No LLM calls recorded yet.</div>
      <div style={{ fontSize: 13, marginTop: 6, color: '#4b5563' }}>
        Token usage appears here after you run an optimisation or score a candidate.
      </div>
    </div>
  );
}

function OpusSection({ analysis }) {
  if (!analysis) return null;
  const { on_demand, batch, token_stats, per_run } = analysis;
  const ts = token_stats || {};
  const hasRuns = per_run && per_run.length > 0;

  const savings = on_demand.total_cost_usd > 0
    ? ((on_demand.total_cost_usd - batch.total_cost_usd) / on_demand.total_cost_usd * 100).toFixed(0)
    : 0;

  return (
    <div style={{
      border: '1px solid #6366f140',
      borderRadius: 12,
      background: 'linear-gradient(135deg, #1e1b4b20, #1e1e2e)',
      padding: 24,
      marginBottom: 8,
    }}>
      {/* Model header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 20 }}>🔮</span>
            <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#a5b4fc' }}>
              Claude Opus 4.5 — AWS Bedrock
            </h3>
            <span style={{ fontSize: 11, background: '#6366f130', color: '#a5b4fc', padding: '2px 8px', borderRadius: 4, fontWeight: 600 }}>
              Frontier Model
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
            Model ID: <code style={{ fontFamily: 'monospace', color: '#9ca3af' }}>anthropic.claude-opus-4-5-20250514-v1:0</code>
          </div>
        </div>
        <a
          href="https://aws.amazon.com/blogs/machine-learning/claude-opus-4-5-now-in-amazon-bedrock/"
          target="_blank"
          rel="noreferrer"
          style={{ fontSize: 11, color: '#6b7280', textDecoration: 'none', border: '1px solid #374151', padding: '4px 10px', borderRadius: 5 }}
        >
          Pricing source ↗
        </a>
      </div>

      {/* Pricing grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        {/* On-demand */}
        <div style={{ background: '#1e1e2e', border: '1px solid #4f46e520', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ fontSize: 12, color: '#818cf8', fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            ⚡ On-Demand
          </div>
          <div style={{ display: 'flex', gap: 20, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>Input</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#e5e7eb' }}>${on_demand.input_per_1m_usd}</div>
              <div style={{ fontSize: 10, color: '#4b5563' }}>per 1M tokens</div>
            </div>
            <div>
              <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>Output</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#e5e7eb' }}>${on_demand.output_per_1m_usd}</div>
              <div style={{ fontSize: 10, color: '#4b5563' }}>per 1M tokens</div>
            </div>
          </div>
          <div style={{ borderTop: '1px solid #374151', paddingTop: 10 }}>
            <div style={{ fontSize: 11, color: '#9ca3af' }}>Estimated total cost</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#818cf8' }}>{USD(on_demand.total_cost_usd)}</div>
          </div>
        </div>

        {/* Batch */}
        <div style={{ background: '#1e1e2e', border: '1px solid #10b98130', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#34d399', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              📦 Batch Mode
            </div>
            <span style={{ fontSize: 11, background: '#10b98120', color: '#34d399', padding: '1px 7px', borderRadius: 4, fontWeight: 700 }}>
              {batch.discount_pct}% off
            </span>
          </div>
          <div style={{ display: 'flex', gap: 20, marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>Input</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#e5e7eb' }}>${batch.input_per_1m_usd}</div>
              <div style={{ fontSize: 10, color: '#4b5563' }}>per 1M tokens</div>
            </div>
            <div>
              <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>Output</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#e5e7eb' }}>${batch.output_per_1m_usd}</div>
              <div style={{ fontSize: 10, color: '#4b5563' }}>per 1M tokens</div>
            </div>
          </div>
          <div style={{ borderTop: '1px solid #374151', paddingTop: 10 }}>
            <div style={{ fontSize: 11, color: '#9ca3af' }}>Estimated total cost</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#34d399' }}>{USD(batch.total_cost_usd)}</div>
            {on_demand.total_cost_usd > 0 && (
              <div style={{ fontSize: 11, color: '#059669', marginTop: 2 }}>
                Save {USD(on_demand.total_cost_usd - batch.total_cost_usd)} vs on-demand
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Token stats */}
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px', marginBottom: hasRuns ? 20 : 0 }}>
        <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 600, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Token Statistics
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Total Records</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#e5e7eb' }}>{NUM(ts.total_records)}</div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>API calls made</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Total Input Tokens</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#93c5fd' }}>{NUM(ts.total_prompt_tokens)}</div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>across all calls</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Total Output Tokens</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#f9a8d4' }}>{NUM(ts.total_completion_tokens)}</div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>across all calls</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Avg Input / Record</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#93c5fd' }}>{AVG(ts.avg_prompt_tokens_per_record)}</div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>tokens per call</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Avg Output / Record</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#f9a8d4' }}>{AVG(ts.avg_completion_tokens_per_record)}</div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>tokens per call</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Input : Output Ratio</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#fcd34d' }}>
              {ts.total_prompt_tokens && ts.total_completion_tokens
                ? `${(ts.total_prompt_tokens / ts.total_completion_tokens).toFixed(1)}:1`
                : '—'}
            </div>
            <div style={{ fontSize: 10, color: '#4b5563' }}>prompt-heavy pipeline</div>
          </div>
        </div>
      </div>

      {/* Per-run breakdown */}
      {hasRuns && (
        <>
          <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Cost Per Optimisation Run
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ color: '#6b7280', borderBottom: '1px solid #374151' }}>
                  <th style={{ textAlign: 'left', padding: '6px 10px', fontWeight: 500 }}>Run</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Records</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Input Tokens</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Output Tokens</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Avg In/Record</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Avg Out/Record</th>
                  <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500, color: '#818cf8' }}>On-Demand</th>
                  <th style={{ textAlign: 'right', padding: '6px 10px', fontWeight: 500, color: '#34d399' }}>Batch</th>
                </tr>
              </thead>
              <tbody>
                {per_run.map((r) => (
                  <tr key={r.run_set_id} style={{ borderBottom: '1px solid #1f2937' }}>
                    <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontSize: 11, color: '#9ca3af' }}>
                      {r.run_set_id}
                    </td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#d1d5db' }}>{NUM(r.records)}</td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#93c5fd' }}>{NUM(r.prompt_tokens)}</td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#f9a8d4' }}>{NUM(r.completion_tokens)}</td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#93c5fd' }}>{AVG(r.avg_prompt_tokens)}</td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#f9a8d4' }}>{AVG(r.avg_completion_tokens)}</td>
                    <td style={{ textAlign: 'right', padding: '8px', color: '#818cf8', fontWeight: 700 }}>{USD(r.on_demand_cost_usd)}</td>
                    <td style={{ textAlign: 'right', padding: '8px 10px', color: '#34d399', fontWeight: 700 }}>{USD(r.batch_cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default function CostPage() {
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listJobs().then((res) => {
      const j = res.data || [];
      setJobs(j);
      if (j.length > 0) setJobId(j[0].id);
    });
  }, []);

  const load = useCallback(() => {
    if (!jobId) return;
    setLoading(true);
    setError('');
    getJobCosts(jobId)
      .then((res) => setData(res.data))
      .catch((e) => setError(e?.response?.data?.detail || e.message || 'Failed to load cost data'))
      .finally(() => setLoading(false));
  }, [jobId]);

  useEffect(() => { load(); }, [load]);

  const s = data?.summary;
  const totalTokens = s?.total_tokens || 0;
  const breakdown = data?.breakdown_by_call_type || [];
  const bedrock = data?.bedrock_comparison || [];
  const runs = data?.breakdown_by_run || [];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 16px', fontFamily: 'inherit' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f3f4f6', margin: 0 }}>LLM Cost Analyser</h1>
          <p style={{ color: '#9ca3af', fontSize: 13, margin: '4px 0 0' }}>
            Token usage, cost breakdown, and AWS Bedrock projections for the GEPA pipeline
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {jobs.length > 1 && (
            <select
              value={jobId || ''}
              onChange={(e) => setJobId(Number(e.target.value))}
              style={{ background: '#1e1e2e', border: '1px solid #374151', color: '#f3f4f6', borderRadius: 6, padding: '6px 12px', fontSize: 13 }}
            >
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
          )}
          <button
            onClick={load}
            disabled={loading}
            style={{ background: '#374151', border: 'none', color: '#f3f4f6', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 13 }}
          >
            {loading ? 'Loading…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #dc2626', borderRadius: 8, padding: '12px 16px', color: '#fca5a5', marginBottom: 20 }}>
          {error}
        </div>
      )}

      {!data && !loading && !error && <EmptyState />}

      {data && (
        <>
          {/* Summary cards */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
            <MetricCard title="Total API Calls" value={NUM(s?.total_calls)} sub={`${NUM(s?.total_prompt_tokens)} in · ${NUM(s?.total_completion_tokens)} out`} />
            <MetricCard title="Total Tokens" value={NUM(s?.total_tokens)} sub={`Model: ${s?.current_model}`} />
            <MetricCard
              title="Current Cost (NIM)"
              value={USD(s?.estimated_current_cost_usd)}
              sub={`$${s?.input_price_per_1m}/1M in · $${s?.output_price_per_1m}/1M out`}
              accent="#6366f1"
            />
            <MetricCard
              title="Cheapest on Bedrock"
              value={USD(s?.cheapest_bedrock_cost_usd)}
              sub={s?.cheapest_bedrock_model || '—'}
              accent="#10b981"
            />
          </div>

          {totalTokens === 0 ? (
            <EmptyState />
          ) : (
            <>
              {/* ── Claude Opus 4.5 section ── */}
              <SectionHeader accent="#818cf8">🔮 Claude Opus 4.5 on AWS Bedrock — Cost Estimate</SectionHeader>
              <OpusSection analysis={data?.opus_45_analysis} />

              {/* Token usage breakdown */}
              <SectionHeader>Token Usage by Call Type</SectionHeader>
              <div style={{ background: '#1e1e2e', borderRadius: 10, padding: 20, border: '1px solid #374151' }}>
                <div style={{ display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', marginBottom: 16 }}>
                  {breakdown.map((b) => {
                    const pct = totalTokens > 0 ? (b.total_tokens / totalTokens) * 100 : 0;
                    const meta = CALL_TYPE_LABELS[b.call_type] || CALL_TYPE_LABELS.unknown;
                    return <BarSegment key={b.call_type} pct={pct} color={meta.color} label={meta.label} tokens={b.total_tokens} />;
                  })}
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ color: '#6b7280', borderBottom: '1px solid #374151' }}>
                      <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 500 }}>Type</th>
                      <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Calls</th>
                      <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Input Tokens</th>
                      <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Output Tokens</th>
                      <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Total Tokens</th>
                      <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>NIM Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {breakdown.map((b) => {
                      const meta = CALL_TYPE_LABELS[b.call_type] || CALL_TYPE_LABELS.unknown;
                      return (
                        <tr key={b.call_type} style={{ borderBottom: '1px solid #1f2937' }} title={meta.desc}>
                          <td style={{ padding: '8px' }}>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                              <span style={{ width: 10, height: 10, borderRadius: 3, background: meta.color, display: 'inline-block' }} />
                              <span style={{ color: '#e5e7eb', fontWeight: 500 }}>{meta.label}</span>
                            </span>
                          </td>
                          <td style={{ textAlign: 'right', color: '#9ca3af', padding: '8px' }}>{NUM(b.calls)}</td>
                          <td style={{ textAlign: 'right', color: '#93c5fd', padding: '8px' }}>{NUM(b.prompt_tokens)}</td>
                          <td style={{ textAlign: 'right', color: '#f9a8d4', padding: '8px' }}>{NUM(b.completion_tokens)}</td>
                          <td style={{ textAlign: 'right', color: '#d1d5db', padding: '8px', fontWeight: 600 }}>{NUM(b.total_tokens)}</td>
                          <td style={{ textAlign: 'right', color: '#a78bfa', padding: '8px', fontWeight: 600 }}>{USD(b.cost_usd)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Per-run cost (NIM) */}
              {runs.length > 0 && (
                <>
                  <SectionHeader>Cost by Optimisation Run (Current NIM Model)</SectionHeader>
                  <div style={{ background: '#1e1e2e', borderRadius: 10, padding: 20, border: '1px solid #374151', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <thead>
                        <tr style={{ color: '#6b7280', borderBottom: '1px solid #374151' }}>
                          <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 500 }}>Run Set ID</th>
                          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Calls</th>
                          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>Total Tokens</th>
                          <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 500 }}>NIM Cost</th>
                          <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 500 }}>Started</th>
                        </tr>
                      </thead>
                      <tbody>
                        {runs.map((r) => (
                          <tr key={r.run_set_id} style={{ borderBottom: '1px solid #1f2937' }}>
                            <td style={{ padding: '8px', color: '#9ca3af', fontFamily: 'monospace', fontSize: 11 }}>{r.run_set_id}</td>
                            <td style={{ textAlign: 'right', color: '#9ca3af', padding: '8px' }}>{NUM(r.calls)}</td>
                            <td style={{ textAlign: 'right', color: '#d1d5db', padding: '8px', fontWeight: 600 }}>{NUM(r.total_tokens)}</td>
                            <td style={{ textAlign: 'right', color: '#a78bfa', padding: '8px', fontWeight: 600 }}>{USD(r.estimated_cost_usd)}</td>
                            <td style={{ padding: '8px', color: '#6b7280', fontSize: 12 }}>
                              {r.started_at ? new Date(r.started_at).toLocaleString() : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {/* Bedrock comparison table */}
              <SectionHeader>All AWS Bedrock Models — Cost Comparison</SectionHeader>
              <p style={{ color: '#6b7280', fontSize: 12, margin: '-8px 0 12px' }}>
                What the same {NUM(s?.total_tokens)} tokens ({NUM(s?.total_prompt_tokens)} input · {NUM(s?.total_completion_tokens)} output) would cost on each model. Sorted cheapest first.
              </p>
              <div style={{ background: '#1e1e2e', borderRadius: 10, border: '1px solid #374151', overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ color: '#6b7280', borderBottom: '1px solid #374151' }}>
                      <th style={{ textAlign: 'left', padding: '10px 16px', fontWeight: 500 }}>Model</th>
                      <th style={{ textAlign: 'left', padding: '10px 8px', fontWeight: 500 }}>Provider</th>
                      <th style={{ textAlign: 'right', padding: '10px 8px', fontWeight: 500 }}>$/1M Input</th>
                      <th style={{ textAlign: 'right', padding: '10px 8px', fontWeight: 500 }}>$/1M Output</th>
                      <th style={{ textAlign: 'right', padding: '10px 8px', fontWeight: 500 }}>Est. Cost</th>
                      <th style={{ textAlign: 'right', padding: '10px 16px', fontWeight: 500 }}>vs Current</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bedrock.map((m, i) => {
                      const pc = PROVIDER_COLORS[m.provider] || '#9ca3af';
                      const isOpus = m.name === 'Claude Opus 4.5';
                      const isCheapest = i === 0;
                      return (
                        <tr
                          key={m.model_id}
                          style={{
                            borderBottom: '1px solid #1f2937',
                            background: isOpus ? '#4f46e510' : isCheapest ? 'rgba(16,185,129,0.05)' : 'transparent',
                          }}
                        >
                          <td style={{ padding: '10px 16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              {isCheapest && <span title="Cheapest">⭐</span>}
                              {isOpus && <span title="Highlighted model">🔮</span>}
                              <div>
                                <div style={{ color: isOpus ? '#a5b4fc' : '#e5e7eb', fontWeight: isOpus ? 700 : 500 }}>{m.name}</div>
                                <div style={{ color: '#4b5563', fontSize: 11, fontFamily: 'monospace' }}>{m.model_id}</div>
                              </div>
                            </div>
                          </td>
                          <td style={{ padding: '10px 8px' }}>
                            <span style={{ background: `${pc}20`, color: pc, padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
                              {m.provider}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right', color: '#9ca3af', padding: '10px 8px' }}>${m.input_per_1m}</td>
                          <td style={{ textAlign: 'right', color: '#9ca3af', padding: '10px 8px' }}>${m.output_per_1m}</td>
                          <td style={{ textAlign: 'right', padding: '10px 8px', fontWeight: 700, color: isOpus ? '#a5b4fc' : isCheapest ? '#34d399' : '#d1d5db' }}>
                            {USD(m.estimated_cost_usd)}
                          </td>
                          <td style={{ textAlign: 'right', padding: '10px 16px' }}>
                            <span style={{ color: m.savings_vs_current_pct >= 0 ? '#34d399' : '#f87171', fontWeight: 600, fontSize: 12 }}>
                              {s?.estimated_current_cost_usd === 0 ? '—' : PCT(m.savings_vs_current_pct)}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Footer note */}
              <div style={{ marginTop: 24, background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: '14px 18px', fontSize: 12, color: '#6b7280', lineHeight: 1.7 }}>
                <strong style={{ color: '#9ca3af' }}>Pricing notes:</strong>
                {' '}Claude Opus 4.5 on-demand: <strong style={{ color: '#9ca3af' }}>$5.00/1M input · $25.00/1M output</strong> (AWS Bedrock, May 2026).
                Batch mode: <strong style={{ color: '#9ca3af' }}>$2.50/1M input · $12.50/1M output</strong> (50% discount, standard AWS Bedrock batch rate).
                Other Bedrock prices reflect public on-demand rates in us-east-1.
                {' '}Token usage is captured from the point instrumentation was added — earlier runs will not appear.
                {' '}Source:{' '}
                <a href="https://aws.amazon.com/blogs/machine-learning/claude-opus-4-5-now-in-amazon-bedrock/" target="_blank" rel="noreferrer" style={{ color: '#4b5563' }}>
                  aws.amazon.com/blogs/machine-learning/claude-opus-4-5-now-in-amazon-bedrock/
                </a>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
