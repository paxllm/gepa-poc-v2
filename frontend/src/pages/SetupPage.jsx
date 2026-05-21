import { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate, Link } from 'react-router-dom';
import {
  createJob,
  createCoreValues,
  uploadResume,
  startOptimization,
  listJobs,
  listCoreValues,
  listResumes,
  listSeedPrompts,
  saveSeedPrompts,
  getAppConfig,
} from '../api/client';
import {
  DEFAULT_JOB_TITLE,
  DEFAULT_JOB_DESCRIPTION,
  DEFAULT_CORE_VALUES,
  DEFAULT_EVALUATION_PROMPTS,
} from '../constants/defaults';

const STEPS = [
  { label: 'Job Description', key: 'job' },
  { label: 'Core Values', key: 'values' },
  { label: 'Resumes', key: 'resumes' },
  { label: 'Prompts', key: 'prompts' },
  { label: 'Launch', key: 'launch' },
];

export default function SetupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Job Description
  const [jobTitle, setJobTitle] = useState(DEFAULT_JOB_TITLE);
  const [jobDescription, setJobDescription] = useState(DEFAULT_JOB_DESCRIPTION);
  const [jobId, setJobId] = useState(null);
  const [existingResumeCount, setExistingResumeCount] = useState(0);
  const [hasExistingCoreValues, setHasExistingCoreValues] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  // Step 2: Core Values
  const [coreValues, setCoreValues] = useState(DEFAULT_CORE_VALUES);

  // Step 3: Resumes
  const [resumeFiles, setResumeFiles] = useState([]); // {file, candidateName, hiringLabel, uploaded}
  const [uploadProgress, setUploadProgress] = useState({});

  // Step 4: Prompts
  const [prompts, setPrompts] = useState([...DEFAULT_EVALUATION_PROMPTS]);
  const promptsTouchedRef = useRef(false);

  // Step 5: Config (defaults loaded from backend / .env)
  const [maxMetricCalls, setMaxMetricCalls] = useState(null);
  const [hireThreshold, setHireThreshold] = useState(null);

  useEffect(() => {
    getAppConfig()
      .then((res) => {
        setMaxMetricCalls(res.data.gepa_max_metric_calls);
        setHireThreshold(res.data.hire_threshold);
      })
      .catch(() => {
        setMaxMetricCalls(150);
        setHireThreshold(3.0);
      });
  }, []);

  useEffect(() => {
    listJobs()
      .then(async (res) => {
        if (res.data.length === 0) return;

        const job = res.data[0];
        setJobId(job.id);
        setJobTitle(job.title);
        setJobDescription(job.description.trim());

        const [cvRes, resumesRes, seedPromptsRes] = await Promise.all([
          listCoreValues(job.id),
          listResumes(job.id),
          listSeedPrompts(job.id).catch(() => ({ data: [] })),
        ]);

        if (cvRes.data.length > 0) {
          setCoreValues(
            cvRes.data.map((cv) => ({ name: cv.name, description: cv.description }))
          );
          setHasExistingCoreValues(true);
        }

        if (seedPromptsRes.data.length === 5 && !promptsTouchedRef.current) {
          const ordered = [...seedPromptsRes.data].sort(
            (a, b) => a.prompt_index - b.prompt_index
          );
          setPrompts(ordered.map((p) => p.prompt_text));
        }

        setExistingResumeCount(resumesRes.data.length);
      })
      .catch(console.error)
      .finally(() => setInitialLoadDone(true));
  }, []);

  // ─── Step 1: Job ───────────────────────────────────────────

  const handleCreateJob = async () => {
    if (!jobTitle.trim() || !jobDescription.trim()) {
      setError('Please fill in both job title and description.');
      return;
    }
    if (jobId) {
      setStep(1);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await createJob(jobTitle, jobDescription);
      setJobId(res.data.id);
      setStep(1);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  // ─── Step 2: Core Values ───────────────────────────────────

  const handleCoreValueChange = (index, field, value) => {
    const updated = [...coreValues];
    updated[index] = { ...updated[index], [field]: value };
    setCoreValues(updated);
  };

  const handleSaveCoreValues = async () => {
    if (coreValues.some((cv) => !cv.name.trim() || !cv.description.trim())) {
      setError('Please fill in all core value names and descriptions.');
      return;
    }
    if (hasExistingCoreValues) {
      setStep(2);
      return;
    }
    setLoading(true);
    setError('');
    try {
      await createCoreValues(jobId, coreValues);
      setStep(2);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save core values');
    } finally {
      setLoading(false);
    }
  };

  // ─── Step 3: Resumes ───────────────────────────────────────

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      candidateName: file.name.replace(/\.[^/.]+$/, ''),
      hiringLabel: 'Hired',
      uploaded: false,
    }));
    setResumeFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
  });

  const handleResumeFieldChange = (index, field, value) => {
    const updated = [...resumeFiles];
    updated[index] = { ...updated[index], [field]: value };
    setResumeFiles(updated);
  };

  const removeResume = (index) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadResumes = async () => {
    if (existingResumeCount >= 2 && resumeFiles.length === 0) {
      setStep(3);
      return;
    }
    if (resumeFiles.length < 2) {
      setError('Please add at least 2 resumes.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      for (let i = 0; i < resumeFiles.length; i++) {
        const rf = resumeFiles[i];
        if (rf.uploaded) continue;

        await uploadResume(
          jobId,
          rf.file,
          rf.candidateName,
          rf.hiringLabel,
          (progress) => setUploadProgress((prev) => ({ ...prev, [i]: progress }))
        );

        setResumeFiles((prev) => {
          const updated = [...prev];
          updated[i] = { ...updated[i], uploaded: true };
          return updated;
        });
      }
      setStep(3);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to upload resumes');
    } finally {
      setLoading(false);
    }
  };

  // ─── Step 4: Prompts ───────────────────────────────────────

  const handlePromptChange = (index, value) => {
    promptsTouchedRef.current = true;
    const updated = [...prompts];
    updated[index] = value;
    setPrompts(updated);
  };

  const persistPrompts = async () => {
    if (!jobId) return;
    await saveSeedPrompts(jobId, prompts);
    promptsTouchedRef.current = false;
  };

  const handleSavePrompts = async () => {
    if (prompts.some((p) => !p.trim())) {
      setError('Please fill in all 5 prompts.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await persistPrompts();
      setStep(4);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save prompts');
    } finally {
      setLoading(false);
    }
  };

  // ─── Step 5: Launch ────────────────────────────────────────

  const handleLaunch = async () => {
    if (prompts.some((p) => !p.trim())) {
      setError('Please fill in all 5 prompts.');
      return;
    }
    if (maxMetricCalls == null || hireThreshold == null) {
      setError('Optimization settings are still loading.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      if (promptsTouchedRef.current) {
        await persistPrompts();
      }
      await startOptimization(jobId, prompts, maxMetricCalls, hireThreshold);
      navigate('/dashboard', { state: { jobId } });
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to start optimization');
    } finally {
      setLoading(false);
    }
  };

  // ─── Render ────────────────────────────────────────────────

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">Setup Wizard</h1>
      <p className="page-subtitle">Configure your hiring intelligence system</p>

      {/* Stepper */}
      <div className="stepper">
        {STEPS.map((s, i) => (
          <div key={s.key} className="stepper__step" style={{ flex: 1 }}>
            <div
              className={`stepper__number ${
                i < step
                  ? 'stepper__number--completed'
                  : i === step
                  ? 'stepper__number--active'
                  : 'stepper__number--pending'
              }`}
            >
              {i < step ? '✓' : i + 1}
            </div>
            <span
              className={`stepper__label ${
                i === step ? 'stepper__label--active' : ''
              }`}
            >
              {s.label}
            </span>
            {i < STEPS.length - 1 && (
              <div
                className={`stepper__connector ${
                  i < step ? 'stepper__connector--completed' : ''
                }`}
              />
            )}
          </div>
        ))}
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

      {/* Step 1: Job Description */}
      {step === 0 && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">Job Description</h2>
            {jobId && initialLoadDone && (
              <span className="badge badge--success">Existing job loaded</span>
            )}
          </div>
          {jobId && initialLoadDone && (
            <p
              style={{
                color: 'var(--color-text-secondary)',
                fontSize: 'var(--font-size-sm)',
                marginBottom: 'var(--spacing-4)',
              }}
            >
              Seeded job data is pre-filled. Edit if needed, then continue to prompts.
              View resumes on the <Link to="/resumes">Resumes</Link> page.
            </p>
          )}
          <div className="form-group">
            <label className="form-label">Job Title</label>
            <input
              id="input-job-title"
              className="form-input"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g., Senior Software Engineer"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              id="input-job-description"
              className="form-textarea"
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description here..."
              rows={8}
            />
          </div>
          <div className="flex justify-between">
            <div />
            <button
              id="btn-next-job"
              className="btn btn--primary"
              onClick={handleCreateJob}
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : 'Next →'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Core Values */}
      {step === 1 && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">Core Values</h2>
            <span className="card__subtitle">Define 5 company core values</span>
            {hasExistingCoreValues && (
              <span className="badge badge--success">Already saved</span>
            )}
          </div>
          {coreValues.map((cv, i) => (
            <div key={i} className="grid-2 mb-4">
              <div className="form-group">
                <label className="form-label">Value {i + 1} Name</label>
                <input
                  id={`input-cv-name-${i}`}
                  className="form-input"
                  value={cv.name}
                  onChange={(e) => handleCoreValueChange(i, 'name', e.target.value)}
                  placeholder="e.g., Technical Excellence"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  id={`input-cv-desc-${i}`}
                  className="form-input"
                  value={cv.description}
                  onChange={(e) =>
                    handleCoreValueChange(i, 'description', e.target.value)
                  }
                  placeholder="Describe what this value means..."
                />
              </div>
            </div>
          ))}
          <div className="flex justify-between">
            <button className="btn btn--ghost" onClick={() => setStep(0)}>
              ← Back
            </button>
            <button
              id="btn-next-values"
              className="btn btn--primary"
              onClick={handleSaveCoreValues}
              disabled={loading}
            >
              {loading ? <span className="spinner" /> : 'Next →'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Resume Upload */}
      {step === 2 && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">Upload Resumes</h2>
            <span className="card__subtitle">
              Upload historical resumes with hiring outcomes
            </span>
          </div>

          {existingResumeCount >= 2 && (
            <div
              className="card mb-6"
              style={{ background: 'var(--gradient-subtle)', border: 'none' }}
            >
              <p style={{ margin: 0, fontSize: 'var(--font-size-sm)' }}>
                <strong>{existingResumeCount} resumes</strong> already loaded for this job
                (from seed data or prior uploads). You can skip upload and continue to prompts,
                or add more files below. Browse them on the{' '}
                <Link to="/resumes">Resumes</Link> page.
              </p>
            </div>
          )}

          <div
            {...getRootProps()}
            className={`file-uploader mb-6 ${isDragActive ? 'file-uploader--active' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="file-uploader__icon">📄</div>
            <p className="file-uploader__text">
              <strong>Drop resume files here</strong> or click to browse
              <br />
              Supports PDF, DOCX, TXT
            </p>
          </div>

          {resumeFiles.length > 0 && (
            <table className="data-table mb-6">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Candidate Name</th>
                  <th>Hiring Decision</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {resumeFiles.map((rf, i) => (
                  <tr key={i}>
                    <td>{rf.file.name}</td>
                    <td>
                      <input
                        className="form-input"
                        value={rf.candidateName}
                        onChange={(e) =>
                          handleResumeFieldChange(i, 'candidateName', e.target.value)
                        }
                        style={{ padding: '4px 8px', fontSize: '0.875rem' }}
                      />
                    </td>
                    <td>
                      <select
                        className="form-select"
                        value={rf.hiringLabel}
                        onChange={(e) =>
                          handleResumeFieldChange(i, 'hiringLabel', e.target.value)
                        }
                        style={{ padding: '4px 8px', fontSize: '0.875rem' }}
                      >
                        <option value="Hired">Hired</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                    </td>
                    <td>
                      {rf.uploaded ? (
                        <span className="badge badge--success">✓ Uploaded</span>
                      ) : uploadProgress[i] !== undefined ? (
                        <div className="progress-bar" style={{ width: '80px' }}>
                          <div
                            className="progress-bar__fill"
                            style={{ width: `${uploadProgress[i]}%` }}
                          />
                        </div>
                      ) : (
                        <span className="badge badge--info">Pending</span>
                      )}
                    </td>
                    <td>
                      {!rf.uploaded && (
                        <button
                          className="btn btn--ghost"
                          onClick={() => removeResume(i)}
                          style={{ padding: '2px 6px' }}
                        >
                          ✕
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="flex justify-between">
            <button className="btn btn--ghost" onClick={() => setStep(1)}>
              ← Back
            </button>
            <div className="flex gap-2">
              {existingResumeCount >= 2 && (
                <button
                  id="btn-skip-resumes"
                  className="btn btn--ghost"
                  onClick={() => setStep(3)}
                  disabled={loading}
                >
                  Skip — use {existingResumeCount} existing →
                </button>
              )}
              <button
                id="btn-upload-resumes"
                className="btn btn--primary"
                onClick={handleUploadResumes}
                disabled={
                  loading ||
                  (resumeFiles.length < 2 && existingResumeCount < 2)
                }
              >
                {loading ? (
                  <span className="spinner" />
                ) : resumeFiles.length > 0 ? (
                  `Upload ${resumeFiles.length} Resumes →`
                ) : existingResumeCount >= 2 ? (
                  'Continue →'
                ) : (
                  `Upload ${resumeFiles.length} Resumes →`
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Prompts */}
      {step === 3 && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">Evaluation Prompts</h2>
            <span className="card__subtitle">
              Write 5 evaluation angles — the LLM will generate tailored seed prompts from
              these plus your job description and core values when you launch
            </span>
          </div>
          {prompts.map((prompt, i) => (
            <div key={i} className="form-group">
              <label className="form-label">Prompt {i + 1}</label>
              <textarea
                id={`input-prompt-${i}`}
                className="form-textarea"
                value={prompt}
                onChange={(e) => handlePromptChange(i, e.target.value)}
                placeholder={`Write evaluation focus ${i + 1}... Describe what this lens should prioritize (e.g. technical depth, culture fit). Job description and core values are injected when the seed candidate is built.`}
                rows={4}
              />
            </div>
          ))}
          <div className="flex justify-between">
            <button className="btn btn--ghost" onClick={() => setStep(2)}>
              ← Back
            </button>
            <button
              className="btn btn--primary"
              onClick={handleSavePrompts}
              disabled={loading || prompts.some((p) => !p.trim())}
            >
              {loading ? <span className="spinner" /> : 'Next →'}
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Launch */}
      {step === 4 && (
        <div className="card animate-fade-in">
          <div className="card__header">
            <h2 className="card__title">Launch Optimization</h2>
            <span className="card__subtitle">
              Review configuration and start GEPA
            </span>
          </div>

          <div className="grid-2 mb-6">
            <div className="form-group">
              <label className="form-label">Max Metric Calls</label>
              <input
                id="input-max-calls"
                className="form-input"
                type="number"
                value={maxMetricCalls ?? ''}
                onChange={(e) => {
                  const parsed = parseInt(e.target.value, 10);
                  if (!Number.isNaN(parsed)) {
                    setMaxMetricCalls(parsed);
                  }
                }}
                min={10}
                max={500}
              />
              <small style={{ color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
                Higher = more optimization budget (slower but potentially better results)
              </small>
            </div>
            <div className="form-group">
              <label className="form-label">Hire Threshold (1-5)</label>
              <input
                id="input-threshold"
                className="form-input"
                type="number"
                value={hireThreshold ?? ''}
                onChange={(e) => {
                  const parsed = parseFloat(e.target.value);
                  if (!Number.isNaN(parsed)) {
                    setHireThreshold(parsed);
                  }
                }}
                min={1}
                max={5}
                step={0.5}
              />
              <small style={{ color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
                Average score ≥ threshold = Hired prediction
              </small>
            </div>
          </div>

          <div
            className="card mb-6"
            style={{ background: 'var(--gradient-subtle)', border: 'none' }}
          >
            <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--spacing-3)' }}>
              Summary
            </h3>
            <div className="grid-2">
              <div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Job</div>
                <div>{jobTitle}</div>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Resumes</div>
                <div>
                  {existingResumeCount > 0
                    ? `${existingResumeCount} existing`
                    : `${resumeFiles.length} to upload`}
                  {resumeFiles.length > 0 && existingResumeCount > 0
                    ? ` + ${resumeFiles.length} new`
                    : ''}
                </div>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', marginBottom: 'var(--spacing-2)' }}>
                  Your evaluation angles
                </div>
                {prompts.map((prompt, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-secondary)',
                      marginBottom: 'var(--spacing-2)',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    <strong>Prompt {i + 1}:</strong>{' '}
                    {prompt.length > 160 ? `${prompt.slice(0, 160)}…` : prompt}
                  </div>
                ))}
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>Core Values</div>
                <div>{coreValues.map((cv) => cv.name).join(', ')}</div>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <button className="btn btn--ghost" onClick={() => setStep(3)}>
              ← Back
            </button>
            <button
              id="btn-launch"
              className="btn btn--primary btn--lg"
              onClick={handleLaunch}
              disabled={loading || maxMetricCalls == null || hireThreshold == null}
            >
              {loading ? (
                <>
                  <span className="spinner" /> Starting...
                </>
              ) : (
                '🚀 Launch GEPA Optimization'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
