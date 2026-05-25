# CLAUDE.md — gepa-poc-v2

This file briefs future Claude sessions on what this repo is, how it works today, and what it is intended to become.

---

## 1. What this project is

A proof-of-concept for a **self-learning hiring intelligence module**. Given a job description, a small set of company core values, a batch of historical resumes labeled `Hired` / `Rejected`, and 5 human-authored evaluation prompts ("talent lenses"), the system uses [GEPA](https://github.com/gepa-ai/gepa) — a reflection-driven prompt optimizer — to evolve those 5 prompts until they predict the historical hiring decisions as accurately as possible. NVIDIA NIM (via LiteLLM) is the task + reflection LLM.

The POC is the engine. The **intended product** is a Pax module embedded inside an enterprise hiring platform that ingests new resumes + hiring decisions continuously and keeps re-evolving the per-Job prompts in the background. See §7 for the target use case and §8 for the gap.

---

## 2. Repo layout

```
gepa-poc-v2/
├── backend/                      FastAPI + GEPA orchestration
│   ├── main.py                   App entry, CORS, router registration
│   ├── core/                     config, db, llm clients, encoding
│   ├── models/                   SQLAlchemy ORM + Pydantic schemas
│   ├── parser/                   PDF/DOCX/TXT resume parsing
│   ├── routes/                   REST endpoints (jobs, resumes, optimize, ...)
│   ├── gepa_integration/         HiringAdapter, runner, seed gen, splits, metrics callback
│   ├── constants/default_prompts.py   Static seed prompts + core values
│   └── tests/
├── frontend/                     React + Vite SPA
│   └── src/pages/                SetupPage / ResumesPage / DashboardPage / EvolutionPage
├── data/
│   ├── resume_gepa.db            SQLite DB (single-file)
│   ├── uploads/                  Resume files
│   └── gepa_runs/                Per-run GEPA state (checkpoints)
├── seed_data.py                  Demo seed: one job, core values, mock resumes
├── pyproject.toml
└── README.md
```

Key files to know before editing anything: `backend/models/db_models.py`, `backend/gepa_integration/runner.py`, `backend/gepa_integration/hiring_adapter.py`, `backend/gepa_integration/prompt_loader.py`, `backend/routes/optimization.py`, `backend/routes/scoring.py`, `backend/routes/resumes.py`, `backend/constants/default_prompts.py`, `frontend/src/pages/SetupPage.jsx`, `frontend/src/pages/ScoreCandidatePage.jsx`, `frontend/src/pages/PendingDecisionsPage.jsx`.

---

## 3. Domain model in one screen

```
Job (1) ── (N) CoreValue
   │
   ├─ (N) Resume          ← one job applicant, with hiring_label ∈ {Hired, Rejected}
   │       └─ (N) Evaluation, (N) CandidatePrediction
   │
   ├─ (N) TalentLens      ← one prompt within a 5-prompt set
   │       └─ grouped by candidate_set_id; prompt_index 1..5
   │
   ├─ (N) IterationMetrics
   └─ (N) PromptEvolutionLog
```

A `Resume` now carries a `status` (`decided` for historical/labeled rows, `pending_decision` for live-scored candidates awaiting a hire/reject call), `entry_source` (`historical` vs `live`), and `decision_made_at`. `Resume.hiring_label` is nullable while `status='pending_decision'`. `Job` carries `last_optimized_at` and `auto_retrain_threshold` (default 5) which together drive the auto-retrain trigger.

**Critical naming collision — read this once and remember it.** In this codebase "candidate" is overloaded:

- **GEPA "candidate"** = a *set of 5 TalentLens rows* sharing a `candidate_set_id`. This is the thing GEPA evolves.
- **Job "candidate"** = a person who applied for the job. In code this is always a `Resume` row.

When you see `candidate_set_id`, `CandidatePrediction`, or "best candidate", that is the GEPA sense (a prompt set). When you see `candidate_name` on a `Resume`, that is the job-applicant sense.

`candidate_set_id` prefixes carry meaning: `seed_*` = human-authored or LLM-expanded seed, `run_*` = mid-optimization explored candidate, `best_*` = the selected best at end of a run. `is_active=True` on `TalentLens` marks the currently-serving prompt set. `iteration=-1` marks a final/best record in `TalentLens` and `IterationMetrics`.

---

## 4. How GEPA is used

End-to-end optimization flow (orchestrated in `backend/gepa_integration/runner.py`):

1. **Seed** — `seed_generator.py` either uses the 5 wizard prompts verbatim (`DEMO_MODE=true`) or asks the LLM to expand them against the job description + core values.
2. **Split** — `dataset_split.py` does a stratified 70/15/15 train/val/test over all labeled resumes for the job. Splits are sticky (`force_resplit=False` is the default) so incremental data keeps the same evaluation regime.
3. **Optimize** — `gepa.optimize()` runs with `HiringAdapter` (`hiring_adapter.py`). Per resume per candidate prompt set, the adapter scores each of the 5 prompts 1–5, takes the mean, and emits prediction = `Hired` if mean ≥ `hire_threshold` (default 3.0). GEPA score = 1.0 / 0.0 per resume (correct vs mismatch). Reflection runs on mismatches to mutate one prompt at a time. Candidate selection strategy = `pareto`.
4. **Persist** — `MetricsPersistenceCallback` (`metrics_callback.py`) writes per-iteration `IterationMetrics` and `PromptEvolutionLog` rows live.
5. **Final eval** — `final_eval.py` scores the best candidate on train/val/test, computes overfit gap, writes confusion matrix.

Budget is bounded by `gepa_max_metric_calls` (default 150) and `early_stop_patience` (default 10, via `NoImprovementStopper`). GEPA also writes a checkpoint into `data/gepa_runs/<run_dir>/` so a run can be resumed.

---

## 5. LLM / rate-limit setup

- Provider: **NVIDIA NIM** via **LiteLLM** (`backend/core/litellm_client.py`). Model string is `openai/{NVIDIA_MODEL}` — LiteLLM speaks the OpenAI-compatible NIM endpoint.
- Task LM and reflection LM both go through `completion_with_retry()`. Do not bypass it — the global RPM throttle and exponential backoff live there.
- Env knobs (`.env`): `NVIDIA_API_KEY`, `NVIDIA_MODEL`, `LLM_MAX_RPM` (default 35), `LLM_MAX_PARALLEL` (default 1 — sequential per-resume prompt evaluation, avoids 429 bursts), `LLM_RETRY_MAX` (default 6), `LLM_TIMEOUT_SECONDS` (default 300).
- `DEMO_MODE=true` skips the LLM seed-expansion call entirely (still uses LLM for evaluation and reflection). Good for local dev / demos / when you want to control the seed text.

---

## 6. Run & test

```bash
# Python 3.10+ required (the codebase uses X | Y type hints).
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure .env (NVIDIA_API_KEY at minimum), then:
python seed_data.py
uvicorn backend.main:app --reload          # http://localhost:8000

# In a second shell:
cd frontend && npm install && npm run dev  # http://localhost:5173
```

Health check: `GET /api/health`. Tests live under `backend/tests/`.

**Schema-breaking changes**: there is no Alembic yet. After a schema change in `backend/models/db_models.py`, reset local state with `rm data/resume_gepa.db && python seed_data.py`. Plan for Alembic before any non-POC deployment.

---

## 7. Target enterprise use case (the Pax module north star)

This POC is the seed of an enterprise hiring-platform module. The product intent, in the user's words:

- **Customer is an enterprise.** Many simultaneous job openings — multiple `Job` rows per customer.
- **Each Job starts with a fixed set of static initial prompts** (the seed talent lenses).
- **Candidates apply over time.** Resumes flow into the module attached to a `Job`.
- **Hiring managers make hire/reject decisions.** Those decisions are the ground-truth signal.
- **The module continuously learns from new decisions** and re-evolves the per-Job prompts so future scoring keeps improving.
- **The module is embedded inside the hiring platform.** It must (a) score new candidates on demand and (b) silently re-optimize in the background as labeled feedback accumulates.

In one line: *this repo is the learning engine; the platform module wraps it with ingestion, inference, scheduling, and tenancy.*

---

## 7.5. Live loop endpoints (the continuous-learning surface)

The minimum end-to-end loop is wired up: score a new candidate, record a decision, warm-start re-train. Lives in `backend/routes/scoring.py` and `backend/routes/resumes.py`.

| Endpoint | Purpose |
|---|---|
| `POST /api/jobs/{job_id}/candidates/score` | Upload a new (unlabeled) resume; score it against the currently-active best prompt set (falls back to seed if no evolved best exists). Creates a `Resume(status='pending_decision', entry_source='live')` plus a `CandidatePrediction(actual_label=null)`. Returns aggregate score, prediction, per-prompt scores + rationales, and the `candidate_set_id` it used. |
| `POST /api/jobs/{job_id}/resumes/{id}/decision` | Record a hire/reject decision on a pending candidate. Backfills `Resume.hiring_label`, `decision_made_at`, `status='decided'`; updates the matching `CandidatePrediction.actual_label` + `is_correct`. **Auto-triggers a warm-started retrain** when the count of live decisions since `Job.last_optimized_at` ≥ `Job.auto_retrain_threshold` (default 5). |
| `GET /api/jobs/{job_id}/candidates/pending` | List candidates with `status='pending_decision'`, joined to their latest prediction. Used by the Pending Decisions page. |
| `GET /api/jobs/{job_id}/training-status` | Lightweight dashboard summary: `decisions_since_last_train`, `auto_retrain_threshold`, `last_optimized_at`, `has_active_best_prompts`, `run_status`. |
| `POST /api/jobs/{job_id}/retrain` | Manual warm-started retrain. Loads the active best (or seed) prompt set and kicks off `run_optimization_in_background` with `force_resplit=False`. Returns 202. |

Warm-start mechanics: GEPA's `seed_candidate` parameter is what enables warm-start — `runner.run_optimization()` already accepts a `prompts` list and uses it as the seed; `/retrain` just loads the current best and passes it through. The runner now also (a) preserves `IterationMetrics` / `PromptEvolutionLog` from prior runs (deletes are scoped to the current `run_set_id`) and (b) stamps `Job.last_optimized_at` on success. Splits are sticky: `assign_splits` in `dataset_split.py` now does **incremental** assignment when new decided resumes appear, leaving historical assignments untouched.

Frontend wiring: `frontend/src/pages/ScoreCandidatePage.jsx` (`/score`), `frontend/src/pages/PendingDecisionsPage.jsx` (`/pending`), plus a "Re-train now" button and "Live candidates" panel on `DashboardPage.jsx`.

---

## 8. Gap between POC and target

Concrete things the POC does not yet have. Each names the file or table that would change.

1. **No multi-tenancy.** Everything keys on `job_id`. There is no `Organization` / `Customer` / `User` table. Production needs an `organization_id` FK on `Job` (and probably on `Resume`) plus tenant-scoped queries everywhere in `backend/routes/`.
2. **No model versioning / promotion controls.** Each optimization run sets a new `is_active=True` and deactivates the previous one. Historical evolved prompt sets are preserved (as inactive `TalentLens` rows) and `IterationMetrics` / `PromptEvolutionLog` history is now scoped per `run_set_id`, but there is no "v3 was promoted on date X with test accuracy Y, signed off by user Z" workflow. Hiring is regulated — this matters. Likely add a `PromptVersion` table referencing a `candidate_set_id` plus an approval column.
3. **No bias / fairness instrumentation.** `IterationMetrics` tracks accuracy / precision / recall / F1 only. Disparate-impact / four-fifths-rule style metrics need to be added before this is deployable in a regulated hiring context.
4. **SQLite single-file DB.** Fine for the POC. Production needs Postgres + Alembic migrations. The SQLAlchemy ORM should port cleanly; the friction is in migrations + connection pooling + per-tenant isolation. Until Alembic lands, schema changes require `rm data/resume_gepa.db && python seed_data.py`.
5. **NVIDIA NIM is hard-coded.** `backend/core/config.py` and `litellm_client.py` (`openai/{nvidia_model}`) assume one provider for all customers. Enterprise customers will bring their own keys / models — needs a per-tenant LLM config table.
6. **Single-job assumptions in the frontend.** `SetupPage → DashboardPage → EvolutionPage → ScoreCandidatePage → PendingDecisionsPage` all default to the first `Job` returned by `listJobs`. Multi-job dashboards, job switching, per-job nav, and a version-history view are still missing.
7. **Auto-retrain is best-effort only.** The trigger is in-process (FastAPI `BackgroundTasks`) — if the API process restarts mid-decision, no separate scheduler will catch up. Production needs a real queue (e.g. Celery / RQ / Cloud Tasks).

The schema and GEPA orchestration are reusable. The gaps are mostly *around* the engine, not in it.

---

## 9. Suggested evolution path

Not a binding roadmap — a list of the smallest-blast-radius next moves, in roughly the order they unblock each other.

1. **Add an `Organization` table and an `organization_id` FK on `Job`.** Scope all reads/writes in `backend/routes/` by org. (Touches: `backend/models/db_models.py`, every route.)
2. **Add `POST /jobs/{job_id}/score-candidate`.** Loads the active best `TalentLens` set (`is_active=True`, `iteration=-1`), runs `_evaluate_single_resume` from `hiring_adapter.py`, returns prediction + rationale. Persist the prediction so it can later be reconciled against an actual hiring decision.
3. **Capture post-decision feedback.** New table `HiringDecisionFeedback(resume_id, predicted, actual, decided_at, decided_by)` plus a `POST /jobs/{job_id}/feedback` route. This is the fuel for re-learning.
4. **Re-optimize on a trigger.** Background scheduler (APScheduler or a queue worker) that, when ≥ N new feedback rows exist for a job, calls `run_optimization()` with `force_resplit=False` and warm-starts from the prior best `candidate_set_id`. Wire warm-start through `runner.py`'s `gepa.optimize(seed_candidate=...)` call.
5. **Prompt-version promotion.** New `PromptVersion` table. Default promotion = automatic on test-accuracy improvement; allow manual gating. Expose in the frontend as a version-history view.
6. **Postgres migration.** Add Alembic, port the SQLAlchemy schema, switch `backend/core/database.py` over.
7. **Fairness metrics.** Extend `IterationMetrics` (or add a sibling table) and `final_eval.py`. Requires capturing protected-class metadata on `Resume` — a sensitive decision; do not add silently.
8. **Per-tenant LLM config.** A `TenantLLMConfig` table; thread the resolved config through `litellm_client.py` instead of reading globals.

---

## 10. Conventions / quirks to remember

- **"Candidate" is overloaded** — see §3. When in doubt, follow the field name: `candidate_set_id` ⇒ GEPA prompt set; `candidate_name` ⇒ job applicant.
- **`is_active=True`** on `TalentLens` flags the currently-serving prompt set for a job.
- **`iteration=-1`** denotes a final/best record (in `TalentLens` and `IterationMetrics`).
- **`candidate_set_id` prefixes**: `seed_*`, `run_*`, `best_*` carry semantic meaning. Don't invent new prefixes without grepping first.
- **`Resume.status='pending_decision'` rows are invisible to optimization** — `build_dataset` and `assign_splits` both filter on `status='decided' AND hiring_label IS NOT NULL`. Pending rows only become training data after a decision is recorded.
- **`dataset_split` on `Resume` is sticky** once assigned. New decided resumes (with `dataset_split=None`) trigger **incremental** assignment, not a global resplit. Use `force_resplit=True` only when you truly want to invalidate prior train/val/test accounting.
- **History is preserved across runs.** `IterationMetrics` and `PromptEvolutionLog` deletes inside `run_optimization` are scoped by `candidate_set_id == run_set_id`, so warm-started retrains accumulate `v1 → v2 → v3` history on the Evolution page.
- **All LLM calls go through `completion_with_retry`** in `backend/core/litellm_client.py`. The global rate-limit and exponential backoff live there. Don't call `litellm.completion` directly.
- **Active-prompt loading goes through `prompt_loader.load_active_candidate`.** Score, retrain, and the decision auto-trigger all share this helper — keep the (active best → most-recent seed → None) fallback identical across callers.
- **`MetricsPersistenceCallback`** is what makes the dashboard live. If you add new mid-run state the frontend needs to see, plumb it through that callback rather than polling the DB from a side channel.

---

## 11. What NOT to do without explicit signoff

- **Don't widen scope to multi-tenancy or production inference inside a normal feature task.** Those are platform-shape decisions — surface them to the user first.
- **Don't replace SQLite without an Alembic migration plan.** Cutting over silently will lose data and break local dev.
- **Don't bypass `completion_with_retry`.** Every direct `litellm.completion` call is a future 429 incident.
- **Don't change the GEPA score contract** (1.0 correct / 0.0 wrong, mean of 5 prompt scores ≥ threshold). Other parts of the system — the dashboard, the iteration metrics, the reflection feedback strings — assume it.
- **Don't add protected-class fields to `Resume` without an explicit privacy discussion.** Fairness work is in-scope; collecting demographic data is a separate decision.
