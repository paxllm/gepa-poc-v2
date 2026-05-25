/**
 * API client for communicating with the Resume GEPA backend.
 */

import axios from 'axios';

const API_BASE = 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const getAppConfig = () => api.get('/config');

// ─── Jobs ──────────────────────────────────────────────────────

export const createJob = (title, description) =>
  api.post('/jobs', { title, description });

export const listJobs = () =>
  api.get('/jobs');

export const getJob = (jobId) =>
  api.get(`/jobs/${jobId}`);

// ─── Core Values ───────────────────────────────────────────────

export const createCoreValues = (jobId, coreValues) =>
  api.post(`/jobs/${jobId}/core-values`, { core_values: coreValues });

export const listCoreValues = (jobId) =>
  api.get(`/jobs/${jobId}/core-values`);

// ─── Resumes ───────────────────────────────────────────────────

export const uploadResume = (jobId, file, candidateName, hiringLabel, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('candidate_name', candidateName);
  formData.append('hiring_label', hiringLabel);

  return api.post(`/jobs/${jobId}/resumes`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (e) => onProgress(Math.round((e.loaded * 100) / e.total))
      : undefined,
  });
};

export const listResumes = (jobId) =>
  api.get(`/jobs/${jobId}/resumes`);

export const listSeedPrompts = (jobId) =>
  api.get(`/jobs/${jobId}/seed-prompts`);

export const saveSeedPrompts = (jobId, prompts) =>
  api.put(`/jobs/${jobId}/seed-prompts`, {
    prompts: prompts.map((p) => ({ prompt_text: p })),
  });

// ─── Optimization ──────────────────────────────────────────────

export const startOptimization = (jobId, prompts, maxMetricCalls, hireThreshold, earlyStopPatience, forceResplit) =>
  api.post(`/jobs/${jobId}/optimize`, {
    prompts: {
      prompts: prompts.map((p) => ({ prompt_text: p })),
    },
    max_metric_calls: maxMetricCalls ?? null,
    hire_threshold: hireThreshold ?? null,
    early_stop_patience: earlyStopPatience ?? null,
    force_resplit: forceResplit ?? false,
  });

export const getSplitSummary = (jobId) =>
  api.get(`/jobs/${jobId}/split-summary`);

export const getOptimizationStatus = (jobId) =>
  api.get(`/jobs/${jobId}/optimize/status`);

export const getOptimizationResults = (jobId) =>
  api.get(`/jobs/${jobId}/results`);

export const getMetrics = (jobId) =>
  api.get(`/jobs/${jobId}/metrics`);

export const getEvolutionLog = (jobId) =>
  api.get(`/jobs/${jobId}/evolution`);

// ─── Live loop: score / decision / pending / training-status ───

export const scoreCandidate = (jobId, file, candidateName, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('candidate_name', candidateName);
  return api.post(`/jobs/${jobId}/candidates/score`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (e) => onProgress(Math.round((e.loaded * 100) / e.total))
      : undefined,
  });
};

export const recordDecision = (jobId, resumeId, hiringLabel, note) =>
  api.post(`/jobs/${jobId}/resumes/${resumeId}/decision`, {
    hiring_label: hiringLabel,
    note: note ?? null,
  });

export const listPendingCandidates = (jobId) =>
  api.get(`/jobs/${jobId}/candidates/pending`);

export const getTrainingStatus = (jobId) =>
  api.get(`/jobs/${jobId}/training-status`);

export const retrain = (jobId) =>
  api.post(`/jobs/${jobId}/retrain`);

// ─── Cost analysis ─────────────────────────────────────────────

export const getJobCosts = (jobId) =>
  api.get(`/jobs/${jobId}/costs`);

export const getAllCosts = () =>
  api.get('/costs/summary');

export const getCostPricing = () =>
  api.get('/costs/pricing');

// ─── Health ────────────────────────────────────────────────────

export const healthCheck = () =>
  api.get('/health');

export default api;
