# USAGE — testing the continuous-learning loop

A step-by-step guide for verifying that Resume GEPA works end-to-end: seed prompts, train on historical resumes, score new candidates, record decisions, and watch the system auto-evolve. Pairs with `CLAUDE.md` (architecture) and `README.md` (one-paragraph overview).

---

## 1. Prerequisites

- Python 3.10+ (the codebase uses `X | Y` type hints; macOS system 3.9 won't work).
- Node 18+ and npm.
- An NVIDIA NIM API key with budget for ~150–500 model calls per optimization (a small wizard run is ~50–150).
- `curl` and (optional) `sqlite3` for spot-checks.

## 2. First-time setup

From the repo root:

```bash
# Backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure your API key (and optionally DEMO_MODE for cheaper iteration)
cp .env.example .env
$EDITOR .env       # set NVIDIA_API_KEY=nvapi-...
                    # DEMO_MODE=true skips the LLM seed-expansion call

# Seed the demo job + 62 mock resumes
python seed_data.py

# Frontend
cd frontend && npm install && cd ..
```

Useful `.env` knobs:

| Var | Default | What it does |
|---|---|---|
| `NVIDIA_API_KEY` | — | required |
| `LLM_MAX_RPM` | `35` | upstream rate-limit ceiling; lower if you keep hitting 429s |
| `LLM_MAX_PARALLEL` | `1` | per-resume prompt concurrency; raise to 5 if your tier supports it |
| `DEMO_MODE` | `false` | when `true`, skips the LLM seed-expansion call (saves quota) |
| `GEPA_MAX_METRIC_CALLS` | `150` | hard budget per optimization run |

## 3. Start the services

Two terminals (or two background processes):

```bash
# Terminal A — backend on http://localhost:8000
.venv/bin/uvicorn backend.main:app --reload

# Terminal B — frontend on http://localhost:5173
cd frontend && npm run dev
```

Sanity check:

```bash
curl -s http://localhost:8000/api/health
# {"status":"ok","service":"resume-gepa"}
```

If port 8000 is busy: `lsof -ti tcp:8000` to identify the holder; either stop it or run uvicorn on `--port 8001` and also update `API_BASE` in `frontend/src/api/client.js`.

---

## 4. End-to-end happy path

### Step A — Walk the wizard
Open <http://localhost:5173>. You should land on **Setup**. The seed script pre-fills a Senior Full Stack Engineer job, 5 (deliberately weak) core values, 62 historical resumes with hire/reject labels, and 5 (deliberately weak) seed prompts. Click through each step; on the last screen click **Launch Optimization**.

What to watch for: it should redirect to **Dashboard** with a "Running…" badge in the header.

### Step B — Watch the initial optimization
On the **Dashboard**, expect (live, polled every 3 s):
- "Live Validation Accuracy" line chart climbing as iterations complete.
- "Live Eval Outcomes" table populating with prediction vs actual.
- "Current Best Prompts" updating as GEPA finds better candidates.

Completion takes ~5–20 minutes depending on your NIM tier. The run stops when either:
- 150 metric calls used (`GEPA_MAX_METRIC_CALLS`).
- 10 consecutive iterations without improvement (`EARLY_STOP_PATIENCE`).
- You drop a `gepa.stop` file (see §6).

When done, the dashboard shows train / val / test accuracy and a "Re-train now" button becomes enabled.

### Step C — Score a brand-new candidate
Click **Score** in the nav. The page should show "Active prompts: **evolved**" in the subtitle (meaning the optimization above promoted a best set).

1. Type a candidate name (e.g. "Smoke Test Candidate").
2. Drop in a resume file — anything from `data/uploads/` will do as a smoke test, or your own PDF / DOCX / TXT.
3. Click **Score candidate**.

Expected: in ~5–15 seconds you see an aggregate score (0–5), a "Likely Hire" / "Likely Reject" badge, and a per-prompt table with rationales for each of the 5 lenses. The card also shows which `candidate_set_id` it scored against (e.g. `best_abc12345`).

### Step D — Record a decision
On the same result card, click **Hire** or **Reject**. The system:
- Sets `Resume.hiring_label`, `status='decided'`, `decision_made_at=now`.
- Backfills `CandidatePrediction.actual_label` + `is_correct`.
- Increments the "decisions since last train" counter.

You should see the form reset. Go to **Pending** to confirm the row is gone (or to score a few more and decide them later).

### Step E — Manual retrain
On **Dashboard**, click **Re-train now**. The button is disabled until you have an active evolved set and no run is in progress. This kicks off a warm-started GEPA run — the seed for this run is the previous best, not the original wizard prompts.

Verify warm-start: open **Evolution**. The new run's "Iteration 0" prompts should match the previous run's best prompts (compare text), not the wizard prompts.

### Step F — Auto-retrain after N decisions
1. Go to **Score**, then submit 5 candidates and click Hire/Reject on each (the default `auto_retrain_threshold` is 5).
2. On the 5th decision, the response will include `auto_retrain_triggered: true` and you'll be redirected to **Dashboard**.
3. The dashboard should immediately show a "Running…" badge and the metrics history will start populating again.

After it completes, `Job.last_optimized_at` updates and the decisions-since-last-train counter resets to 0.

### Step G — Verify it actually learned from the new feedback
After the auto-retrain finishes, re-score the same kind of candidate from step C. You should see different per-prompt rationales and possibly a different aggregate — the prompts have shifted in response to your decisions.

---

## 5. API spot-checks (curl)

Useful when the UI doesn't make a behavior obvious or when debugging:

```bash
JOB=1

# Training status (used by the dashboard banner)
curl -s http://localhost:8000/api/jobs/$JOB/training-status | jq .
# { decisions_since_last_train, auto_retrain_threshold, last_optimized_at,
#   has_active_best_prompts, run_status }

# Pending candidates
curl -s http://localhost:8000/api/jobs/$JOB/candidates/pending | jq .

# Score a new candidate (replace with a real file path)
curl -s -X POST http://localhost:8000/api/jobs/$JOB/candidates/score \
  -F 'candidate_name=Alice Sample' \
  -F 'file=@data/uploads/alice_chen.txt' | jq .

# Record a decision (use the resume_id from the score response)
curl -s -X POST http://localhost:8000/api/jobs/$JOB/resumes/63/decision \
  -H 'Content-Type: application/json' \
  -d '{"hiring_label":"Hired"}' | jq .

# Manual warm-started retrain
curl -s -X POST http://localhost:8000/api/jobs/$JOB/retrain | jq .

# Optimization status (poll while running)
curl -s http://localhost:8000/api/jobs/$JOB/optimize/status | jq '.status, .phase, .current_iteration, .best_accuracy'
```

Expected error responses (these are correct, not bugs):
- `409` on `/candidates/score` if no prompt set exists yet → run the wizard.
- `409` on `/retrain` if a run is already in progress → wait, then retry.
- `409` on `/resumes/{id}/decision` if the resume isn't `pending_decision` (e.g. you tried to "decide" a historical row) → only decide rows that came from `/candidates/score`.

## 6. DB spot-checks (sqlite)

```bash
sqlite3 data/resume_gepa.db

-- Which prompt set is currently serving?
SELECT candidate_set_id, prompt_index, substr(prompt_text, 1, 80)
FROM talent_lenses
WHERE job_id = 1 AND is_active = 1 AND generation = 'evolved'
ORDER BY prompt_index;

-- All prompt versions over time (warm-start chain)
SELECT DISTINCT candidate_set_id, generation, iteration, is_active, created_at
FROM talent_lenses
WHERE job_id = 1
ORDER BY created_at;

-- Live decisions waiting to be picked up by the next train
SELECT id, candidate_name, hiring_label, decision_made_at, dataset_split
FROM resumes
WHERE job_id = 1 AND entry_source = 'live' AND status = 'decided'
ORDER BY decision_made_at DESC;

-- Per-iteration accuracy across runs
SELECT candidate_set_id, iteration, accuracy, val_accuracy, test_accuracy
FROM iteration_metrics
WHERE job_id = 1
ORDER BY id;
```

## 7. Reset and troubleshooting

| Symptom | Fix |
|---|---|
| `502 RateLimitError 429` from NIM | Lower `LLM_MAX_RPM`; set `LLM_MAX_PARALLEL=1`; wait a minute and retry. |
| `address already in use` on port 8000 | `lsof -ti tcp:8000` to find the holder. Either stop it or run uvicorn on `--port 8001` and update `frontend/src/api/client.js`. |
| Schema error after `git pull` | No Alembic yet — `rm data/resume_gepa.db && python seed_data.py`. You'll lose all local data, including any decisions you've recorded. |
| A run is stuck or you want to abort it | `touch data/gepa_runs/job_<JOB>/gepa.stop`. GEPA exits at the next stopper check (within ~one prompt eval). Delete the file before the next run. |
| Auto-retrain didn't fire on the 5th decision | Check `GET /training-status`: the threshold is `auto_retrain_threshold` on the `Job`. Make sure each decision was on a `live`/`pending_decision` resume (historical rows don't count). Also a run already in progress blocks the trigger. |
| Frontend can't reach backend | Check `API_BASE` in `frontend/src/api/client.js` matches your backend port. CORS is open for `:5173`, `:3000`, `:127.0.0.1:5173`. |
| Want a fresh demo without paying for seed expansion | Set `DEMO_MODE=true` in `.env`. Evaluation + reflection still use the LLM; only seed expansion is skipped. |

## 8. Cleanup

```bash
# Stop dev servers (Ctrl-C in each terminal)
# Optionally reset everything:
rm -rf data/resume_gepa.db data/uploads/* data/gepa_runs/*
python seed_data.py
```
