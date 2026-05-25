import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';

import {
  listJobs,
  listPendingCandidates,
  recordDecision,
  getTrainingStatus,
} from '../api/client';

export default function PendingDecisionsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [jobId, setJobId] = useState(location.state?.jobId || null);
  const [jobs, setJobs] = useState([]);
  const [pending, setPending] = useState([]);
  const [training, setTraining] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    listJobs().then((res) => {
      setJobs(res.data);
      if (!jobId && res.data.length > 0) setJobId(res.data[0].id);
    });
  }, [jobId]);

  const refresh = useCallback(async () => {
    if (!jobId) return;
    try {
      const [pendingRes, trainingRes] = await Promise.all([
        listPendingCandidates(jobId),
        getTrainingStatus(jobId),
      ]);
      setPending(pendingRes.data);
      setTraining(trainingRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load pending candidates.');
    }
  }, [jobId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleDecision = async (resumeId, label) => {
    setBusyId(resumeId);
    setError('');
    try {
      const res = await recordDecision(jobId, resumeId, label, null);
      await refresh();
      if (res.data.auto_retrain_triggered) {
        navigate('/dashboard', { state: { jobId } });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record decision.');
    } finally {
      setBusyId(null);
    }
  };

  const predictionBadge = (pred) =>
    pred === 'Hired' ? 'badge badge--success' : 'badge badge--danger';

  return (
    <div>
      <h1 className="page-title">Pending Decisions</h1>
      <p className="page-subtitle">
        Candidates scored via the live endpoint, awaiting a hire/reject decision.
      </p>

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
            <div className="metric-card__label">Decisions since last train</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>
              {training.decisions_since_last_train} / {training.auto_retrain_threshold}
            </div>
            <div className="metric-card__trend">
              Auto-retrain fires when this hits the threshold.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {training.run_status === 'running' && (
              <span className="badge badge--info">Re-training…</span>
            )}
            <Link to="/score" className="btn btn--primary">
              Score another candidate
            </Link>
          </div>
        </div>
      )}

      {error && (
        <div className="card mb-6" style={{ borderColor: 'var(--color-danger)' }}>
          {error}
        </div>
      )}

      {jobs.length > 1 && (
        <div className="card mb-6">
          <label className="form-label">Job</label>
          <select
            className="form-select"
            value={jobId || ''}
            onChange={(e) => setJobId(Number(e.target.value))}
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="card">
        <div className="card__header">
          <h2 className="card__title">
            {pending.length} candidate{pending.length === 1 ? '' : 's'} pending
          </h2>
        </div>

        {pending.length === 0 ? (
          <p style={{ opacity: 0.7 }}>
            Nothing pending. Score a candidate from the{' '}
            <Link to="/score">Score Candidate</Link> page.
          </p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Prediction</th>
                <th>Score</th>
                <th>Scored against</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((c) => (
                <tr key={c.resume_id}>
                  <td>{c.candidate_name}</td>
                  <td>
                    {c.prediction ? (
                      <span className={predictionBadge(c.prediction)}>
                        {c.prediction === 'Hired' ? 'Likely Hire' : 'Likely Reject'}
                      </span>
                    ) : (
                      <span className="badge badge--info">—</span>
                    )}
                  </td>
                  <td>{c.aggregate_score != null ? `${c.aggregate_score.toFixed(2)} / 5` : '—'}</td>
                  <td><code>{c.candidate_set_id_used || '—'}</code></td>
                  <td style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="btn btn--primary"
                      disabled={busyId === c.resume_id}
                      onClick={() => handleDecision(c.resume_id, 'Hired')}
                    >
                      Hire
                    </button>
                    <button
                      className="btn btn--danger"
                      disabled={busyId === c.resume_id}
                      onClick={() => handleDecision(c.resume_id, 'Rejected')}
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
