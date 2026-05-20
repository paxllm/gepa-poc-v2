import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { listJobs, listResumes } from '../api/client';

function SplitBadge({ split }) {
  if (!split) return <span className="badge badge--warning">Unassigned</span>;
  const labels = { train: 'Train', val: 'Val', test: 'Test' };
  const classes = {
    train: 'badge--info',
    val: 'badge--warning',
    test: 'badge--success',
  };
  return (
    <span className={`badge ${classes[split] || 'badge--info'}`}>
      {labels[split] || split}
    </span>
  );
}

function LabelBadge({ label }) {
  return (
    <span className={`badge ${label === 'Hired' ? 'badge--success' : 'badge--danger'}`}>
      {label}
    </span>
  );
}

export default function ResumesPage() {
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterLabel, setFilterLabel] = useState('all');
  const [filterSplit, setFilterSplit] = useState('all');
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    listJobs()
      .then((res) => {
        setJobs(res.data);
        if (res.data.length > 0) {
          setJobId(res.data[0].id);
        }
      })
      .catch((e) => setError(e.message || 'Failed to load jobs'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!jobId) {
      setResumes([]);
      return;
    }
    setLoading(true);
    setError('');
    setSelectedId(null);
    listResumes(jobId)
      .then((res) => setResumes(res.data))
      .catch((e) => setError(e.response?.data?.detail || 'Failed to load resumes'))
      .finally(() => setLoading(false));
  }, [jobId]);

  const stats = useMemo(() => {
    const hired = resumes.filter((r) => r.hiring_label === 'Hired').length;
    const rejected = resumes.filter((r) => r.hiring_label === 'Rejected').length;
    const bySplit = {
      train: resumes.filter((r) => r.dataset_split === 'train').length,
      val: resumes.filter((r) => r.dataset_split === 'val').length,
      test: resumes.filter((r) => r.dataset_split === 'test').length,
    };
    return { total: resumes.length, hired, rejected, bySplit };
  }, [resumes]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return resumes.filter((r) => {
      if (filterLabel !== 'all' && r.hiring_label !== filterLabel) return false;
      if (filterSplit !== 'all' && r.dataset_split !== filterSplit) return false;
      if (q && !r.candidate_name.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [resumes, search, filterLabel, filterSplit]);

  const selected = resumes.find((r) => r.id === selectedId);

  const selectedJob = jobs.find((j) => j.id === jobId);

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="page-title">Resumes</h1>
          <p className="page-subtitle">Uploaded candidates, labels, and parsed resume text</p>
        </div>
        <select
          className="form-select"
          value={jobId || ''}
          onChange={(e) => setJobId(parseInt(e.target.value, 10))}
          style={{ width: '280px' }}
        >
          <option value="">Select a job...</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--spacing-3) var(--spacing-4)',
            marginBottom: 'var(--spacing-4)',
            color: 'var(--color-danger)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {error}
        </div>
      )}

      {!jobId && !loading && (
        <div className="card">
          <p style={{ color: 'var(--color-text-secondary)' }}>
            No job selected. Run{' '}
            <code>python seed_data.py</code> or complete the{' '}
            <Link to="/">Setup Wizard</Link> first.
          </p>
        </div>
      )}

      {jobId && (
        <>
          <div className="grid-2 mb-6" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>
            <div className="card" style={{ padding: 'var(--spacing-4)' }}>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Total</div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600 }}>{stats.total}</div>
            </div>
            <div className="card" style={{ padding: 'var(--spacing-4)' }}>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Hired</div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600, color: 'var(--color-success)' }}>
                {stats.hired}
              </div>
            </div>
            <div className="card" style={{ padding: 'var(--spacing-4)' }}>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Rejected</div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 600, color: 'var(--color-danger)' }}>
                {stats.rejected}
              </div>
            </div>
            <div className="card" style={{ padding: 'var(--spacing-4)' }}>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Splits</div>
              <div style={{ fontSize: 'var(--font-size-sm)', marginTop: '4px' }}>
                {stats.bySplit.train} train / {stats.bySplit.val} val / {stats.bySplit.test} test
              </div>
            </div>
          </div>

          {selectedJob && (
            <div className="card mb-6">
              <h2 className="card__title" style={{ marginBottom: 'var(--spacing-2)' }}>
                {selectedJob.title}
              </h2>
              <p
                style={{
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--font-size-sm)',
                  whiteSpace: 'pre-wrap',
                  margin: 0,
                }}
              >
                {selectedJob.description.trim()}
              </p>
            </div>
          )}

          <div className="card mb-6">
            <div className="flex gap-4 mb-4" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                className="form-input"
                placeholder="Search by candidate name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ maxWidth: '280px' }}
              />
              <select
                className="form-select"
                value={filterLabel}
                onChange={(e) => setFilterLabel(e.target.value)}
                style={{ width: '140px' }}
              >
                <option value="all">All labels</option>
                <option value="Hired">Hired</option>
                <option value="Rejected">Rejected</option>
              </select>
              <select
                className="form-select"
                value={filterSplit}
                onChange={(e) => setFilterSplit(e.target.value)}
                style={{ width: '140px' }}
              >
                <option value="all">All splits</option>
                <option value="train">Train</option>
                <option value="val">Val</option>
                <option value="test">Test</option>
              </select>
              <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                Showing {filtered.length} of {resumes.length}
              </span>
            </div>

            {loading ? (
              <div className="flex justify-center" style={{ padding: 'var(--spacing-8)' }}>
                <span className="spinner" />
              </div>
            ) : filtered.length === 0 ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>No resumes match your filters.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Label</th>
                    <th>Split</th>
                    <th>Type</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((resume) => (
                    <tr
                      key={resume.id}
                      style={{
                        cursor: 'pointer',
                        background:
                          selectedId === resume.id ? 'rgba(244, 156, 38, 0.12)' : undefined,
                      }}
                      onClick={() => setSelectedId(selectedId === resume.id ? null : resume.id)}
                    >
                      <td>{resume.candidate_name}</td>
                      <td>
                        <LabelBadge label={resume.hiring_label} />
                      </td>
                      <td>
                        <SplitBadge split={resume.dataset_split} />
                      </td>
                      <td style={{ textTransform: 'uppercase', fontSize: 'var(--font-size-xs)' }}>
                        {resume.file_type}
                      </td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                        {selectedId === resume.id ? 'Hide ▲' : 'View ▼'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {selected && (
            <div className="card animate-fade-in">
              <div className="card__header">
                <h2 className="card__title">{selected.candidate_name}</h2>
                <div className="flex gap-2">
                  <LabelBadge label={selected.hiring_label} />
                  <SplitBadge split={selected.dataset_split} />
                </div>
              </div>
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'var(--font-mono, ui-monospace, monospace)',
                  fontSize: 'var(--font-size-sm)',
                  lineHeight: 1.6,
                  color: 'var(--color-text-secondary)',
                  background: 'var(--color-bg-secondary, rgba(0,0,0,0.2))',
                  padding: 'var(--spacing-4)',
                  borderRadius: 'var(--radius-md)',
                  maxHeight: '480px',
                  overflow: 'auto',
                  margin: 0,
                }}
              >
                {selected.parsed_text || '(No parsed text available)'}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
