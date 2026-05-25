import { useState, useEffect } from 'react';
import { listJobs } from '../api/client';
import '../styles/TestDataPage.css';

async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result;
      const base64 = dataUrl.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function batchUploadResumes(jobId, resumes, autoRetrain) {
  const items = [];
  for (const resume of resumes) {
    const base64 = await fileToBase64(resume.file);
    items.push({
      candidate_name: resume.name,
      hiring_label: resume.decision,
      file_name: resume.file.name,
      file_content_base64: base64,
    });
  }

  const response = await fetch(`/api/jobs/${jobId}/resumes/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resumes: items,
      auto_retrain: autoRetrain,
    }),
  });

  if (!response.ok) {
    let errorMsg = 'Batch upload failed';
    try {
      const error = await response.json();
      errorMsg = error.detail || errorMsg;
    } catch (e) {
      errorMsg = `Server error (${response.status}): ${response.statusText}`;
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

function DecisionBadge({ decision }) {
  return (
    <span
      className={`badge ${decision === 'Hired' ? 'badge--success' : 'badge--danger'}`}
    >
      {decision}
    </span>
  );
}

export default function TestDataPage() {
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [files, setFiles] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);
  const [autoRetrain, setAutoRetrain] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listJobs()
      .then((res) => {
        setJobs(res.data);
        if (res.data.length > 0) {
          setJobId(res.data[0].id);
        }
      })
      .catch((e) => setError(e.message || 'Failed to load jobs'));
  }, []);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleFileInput = (e) => {
    handleFiles(e.target.files);
  };

  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList);
    const newResumes = newFiles.map((file) => ({
      file,
      name: file.name.replace(/\.[^/.]+$/, ''),
      decision: 'Hired',
      key: `${file.name}-${Date.now()}-${Math.random()}`,
    }));
    setResumes([...resumes, ...newResumes]);
    setError('');
  };

  const updateDecision = (key, decision) => {
    setResumes(
      resumes.map((r) =>
        r.key === key ? { ...r, decision } : r
      )
    );
  };

  const removeResume = (key) => {
    setResumes(resumes.filter((r) => r.key !== key));
  };

  const handleUpload = async () => {
    if (!jobId) {
      setError('Please select a job');
      return;
    }

    if (resumes.length === 0) {
      setError('Please add at least one resume');
      return;
    }

    setUploading(true);
    setError('');
    setUploadResults(null);

    try {
      const results = await batchUploadResumes(jobId, resumes, autoRetrain);
      setUploadResults(results);
      setResumes([]);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const selectedJob = jobs.find((j) => j.id === jobId);

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="page-title">Test Data</h1>
          <p className="page-subtitle">
            Upload diverse test resumes with surprising decisions to trigger GEPA evolution
          </p>
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

      {!jobId && !uploading && !uploadResults && (
        <div className="card" style={{ marginBottom: 'var(--spacing-4)' }}>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Please select a job to continue.
          </p>
        </div>
      )}

      {jobId && selectedJob && !uploadResults && (
        <>
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

          <div className="card mb-6">
            <h3 className="card__title" style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-4)' }}>
              Upload Resumes
            </h3>

            <div
              className={`drop-zone ${dragActive ? 'drop-zone--active' : ''}`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragEnter}
              onDrop={handleDrop}
            >
              <div style={{ textAlign: 'center', padding: 'var(--spacing-8)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: 'var(--spacing-2)' }}>
                  📄
                </div>
                <p style={{ fontWeight: 600, marginBottom: 'var(--spacing-1)' }}>
                  Drop resumes here or click to browse
                </p>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                  Supports PDF, DOCX, and TXT files (up to 10 per batch)
                </p>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileInput}
                  style={{ display: 'none' }}
                  id="file-input"
                />
                <label htmlFor="file-input" style={{ cursor: 'pointer' }}>
                  <button
                    type="button"
                    className="button button--primary"
                    style={{ marginTop: 'var(--spacing-3)' }}
                    onClick={() => document.getElementById('file-input').click()}
                  >
                    Browse Files
                  </button>
                </label>
              </div>
            </div>

            {resumes.length > 0 && (
              <div style={{ marginTop: 'var(--spacing-6)' }}>
                <h4 style={{ marginBottom: 'var(--spacing-3)', fontSize: 'var(--font-size-base)' }}>
                  Resumes to Upload ({resumes.length})
                </h4>
                <div style={{ display: 'grid', gap: 'var(--spacing-2)' }}>
                  {resumes.map((resume) => (
                    <div
                      key={resume.key}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-3)',
                        padding: 'var(--spacing-3)',
                        background: 'var(--color-bg-secondary, rgba(0,0,0,0.05))',
                        borderRadius: 'var(--radius-md)',
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                          {resume.name}
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                          {resume.file.name} · {(resume.file.size / 1024).toFixed(1)} KB
                        </div>
                      </div>
                      <select
                        className="form-select"
                        value={resume.decision}
                        onChange={(e) => updateDecision(resume.key, e.target.value)}
                        style={{ width: '140px' }}
                      >
                        <option value="Hired">Hired</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() => removeResume(resume.key)}
                        style={{ padding: '6px 12px', fontSize: 'var(--font-size-sm)' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: 'var(--spacing-6)', paddingTop: 'var(--spacing-4)', borderTop: '1px solid var(--color-border)' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-4)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={autoRetrain}
                      onChange={(e) => setAutoRetrain(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: 'var(--font-size-sm)' }}>
                      Auto-trigger retrain if threshold is met
                    </span>
                  </label>

                  <div style={{ display: 'flex', gap: 'var(--spacing-3)' }}>
                    <button
                      type="button"
                      className="button button--primary"
                      onClick={handleUpload}
                      disabled={uploading}
                      style={{ minWidth: '140px' }}
                    >
                      {uploading ? (
                        <>
                          <span className="spinner" style={{ marginRight: '8px' }} />
                          Uploading...
                        </>
                      ) : (
                        `Upload ${resumes.length} Resume${resumes.length !== 1 ? 's' : ''}`
                      )}
                    </button>
                    <button
                      type="button"
                      className="button button--ghost"
                      onClick={() => setResumes([])}
                      disabled={uploading}
                    >
                      Clear All
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {uploadResults && (
        <div className="card">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-3)',
              marginBottom: 'var(--spacing-4)',
              paddingBottom: 'var(--spacing-4)',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            <div style={{ fontSize: '2rem' }}>
              {uploadResults.failed === 0 ? '✅' : '⚠️'}
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, marginBottom: '4px' }}>
                Upload Complete
              </h2>
              <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                {uploadResults.successful} succeeded, {uploadResults.failed} failed
              </p>
            </div>
          </div>

          {uploadResults.auto_retrain_triggered && (
            <div
              style={{
                background: 'rgba(34, 197, 94, 0.1)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-3) var(--spacing-4)',
                marginBottom: 'var(--spacing-4)',
                color: 'var(--color-success)',
                fontSize: 'var(--font-size-sm)',
              }}
            >
              🚀 Auto-retrain triggered! GEPA optimization is now running in the background.
            </div>
          )}

          <div style={{ marginBottom: 'var(--spacing-4)' }}>
            <h3 style={{ marginBottom: 'var(--spacing-3)', fontSize: 'var(--font-size-base)' }}>
              Results
            </h3>
            <div style={{ display: 'grid', gap: 'var(--spacing-2)' }}>
              {uploadResults.results.map((result, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-3)',
                    padding: 'var(--spacing-3)',
                    background: 'var(--color-bg-secondary, rgba(0,0,0,0.05))',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 500 }}>
                      {result.candidate_name}
                    </div>
                    {result.error_message && (
                      <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-danger)' }}>
                        {result.error_message}
                      </div>
                    )}
                  </div>
                  {result.status === 'success' ? (
                    <span style={{ color: 'var(--color-success)', fontWeight: 500 }}>✓</span>
                  ) : (
                    <span style={{ color: 'var(--color-danger)', fontWeight: 500 }}>✗</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--spacing-3)' }}>
            <button
              type="button"
              className="button button--primary"
              onClick={() => setUploadResults(null)}
            >
              Upload More
            </button>
            <a href="/dashboard" className="button button--ghost">
              Go to Dashboard
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
