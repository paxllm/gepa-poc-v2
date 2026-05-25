import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useLocation, useNavigate, Link } from 'react-router-dom';

import {
  listJobs,
  scoreCandidate,
  recordDecision,
  getTrainingStatus,
} from '../api/client';

export default function ScoreCandidatePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [jobId, setJobId] = useState(location.state?.jobId || null);
  const [jobs, setJobs] = useState([]);
  const [file, setFile] = useState(null);
  const [candidateName, setCandidateName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [training, setTraining] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(false);

  useEffect(() => {
    listJobs()
      .then((res) => {
        setJobs(res.data);
        if (!jobId && res.data.length > 0) setJobId(res.data[0].id);
      })
      .catch(() => setError('Failed to load jobs'));
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    getTrainingStatus(jobId)
      .then((res) => setTraining(res.data))
      .catch(() => {});
  }, [jobId, result]);

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) {
      setFile(accepted[0]);
      if (!candidateName) {
        const base = accepted[0].name.replace(/\.[^.]+$/, '');
        setCandidateName(base);
      }
    }
  }, [candidateName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: false,
  });

  const handleScore = async () => {
    if (!file || !candidateName.trim()) {
      setError('Please provide a candidate name and a resume file.');
      return;
    }
    setError('');
    setSubmitting(true);
    setResult(null);
    try {
      const res = await scoreCandidate(jobId, file, candidateName.trim());
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Scoring failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecision = async (label) => {
    if (!result) return;
    setDecisionLoading(true);
    try {
      const res = await recordDecision(jobId, result.resume_id, label, null);
      setDecisionLoading(false);
      if (res.data.auto_retrain_triggered) {
        navigate('/dashboard', { state: { jobId } });
      } else {
        setResult(null);
        setFile(null);
        setCandidateName('');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record decision.');
      setDecisionLoading(false);
    }
  };

  const predictionBadgeClass = (pred) =>
    pred === 'Hired' ? 'badge badge--success' : 'badge badge--danger';

  return (
    <div>
      <h1 className="page-title">Score Candidate</h1>
      <p className="page-subtitle">
        Run a new resume against the current best prompt set.{' '}
        {training && (
          <span>
            Decisions since last train: <strong>{training.decisions_since_last_train}</strong>{' '}
            / {training.auto_retrain_threshold}. Active prompts:{' '}
            <strong>{training.has_active_best_prompts ? 'evolved' : 'seed'}</strong>.
          </span>
        )}
      </p>

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

      {!result && (
        <div className="card">
          <div className="card__header">
            <h2 className="card__title">New candidate</h2>
            <span className="card__subtitle">
              Upload a resume and we will score it against the active prompts.
            </span>
          </div>

          <div className="form-group">
            <label className="form-label">Candidate name</label>
            <input
              className="form-input"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="Jane Doe"
            />
          </div>

          <div
            {...getRootProps()}
            className={`file-uploader mb-6 ${isDragActive ? 'file-uploader--active' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="file-uploader__icon">📄</div>
            <p className="file-uploader__text">
              {file ? (
                <strong>{file.name}</strong>
              ) : (
                <>
                  <strong>Drop a resume here</strong> or click to browse
                  <br />
                  PDF, DOCX, or TXT
                </>
              )}
            </p>
          </div>

          {error && (
            <div className="card mb-6" style={{ borderColor: 'var(--color-danger)' }}>
              {error}
            </div>
          )}

          <button
            className="btn btn--primary btn--lg"
            onClick={handleScore}
            disabled={submitting || !file || !candidateName.trim() || !jobId}
          >
            {submitting ? 'Scoring…' : 'Score candidate'}
          </button>
        </div>
      )}

      {result && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">{result.candidate_name}</h2>
            <span className="card__subtitle">
              Scored against <code>{result.candidate_set_id_used}</code>
            </span>
          </div>

          <div className="metric-grid mb-6">
            <div className="metric-card">
              <div className="metric-card__label">Aggregate score</div>
              <div className="metric-card__value">
                {result.aggregate_score.toFixed(2)}
                <span style={{ fontSize: '1rem', opacity: 0.6 }}> / 5</span>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-card__label">Prediction</div>
              <div className="metric-card__value">
                <span className={predictionBadgeClass(result.prediction)}>
                  {result.prediction === 'Hired' ? 'Likely Hire' : 'Likely Reject'}
                </span>
              </div>
              <div className="metric-card__trend">
                threshold = {result.hire_threshold}
              </div>
            </div>
          </div>

          <table className="data-table mb-6">
            <thead>
              <tr>
                <th>Prompt</th>
                <th>Score</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {result.prompt_scores.map((p) => (
                <tr key={p.prompt_index}>
                  <td><strong>#{p.prompt_index}</strong></td>
                  <td>{p.score.toFixed(2)} / 5</td>
                  <td style={{ whiteSpace: 'pre-wrap' }}>{p.rationale}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              className="btn btn--primary"
              onClick={() => handleDecision('Hired')}
              disabled={decisionLoading}
            >
              Record decision: Hire
            </button>
            <button
              className="btn btn--danger"
              onClick={() => handleDecision('Rejected')}
              disabled={decisionLoading}
            >
              Record decision: Reject
            </button>
            <Link to="/pending" className="btn btn--ghost">
              View pending decisions
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
