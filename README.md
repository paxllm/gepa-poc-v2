# Resume GEPA – Self-Learning Hiring Intelligence System

This proof-of-concept (POC) implements a self-learning hiring intelligence system that automatically improves resume evaluation prompts based on historical hiring outcomes using the `gepa` prompt optimization library and NVIDIA NIM models.

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy (Async), SQLite, Pydantic v2, PyMuPDF, python-docx
- **Optimization**: GEPA (Optimization Engine), NVIDIA NIM (meta/llama-3.3-70b-instruct or similar)
- **Frontend**: React, Vite, Recharts, Axios, Vanilla CSS

---

## Setup & Running Guide

### 1. Backend Setup

1. **Configure Environment Variables**:
   Open the `.env` file in the root directory and enter your NVIDIA NIM API key:
   ```env
   NVIDIA_API_KEY=nvapi-xxxxxx-your-key-here
   ```

   For NVIDIA NIM keys with low rate limits (~40 requests/minute), keep these defaults in `.env`:
   ```env
   LLM_MAX_RPM=35
   LLM_MAX_PARALLEL=1
   LLM_RETRY_MAX=6
   ```
   `LLM_MAX_PARALLEL=1` evaluates the five talent-lens prompts sequentially per resume, which avoids burst 429 errors during GEPA optimization. Increase `LLM_MAX_RPM` and `LLM_MAX_PARALLEL` only if your API tier allows higher throughput.

   Optional demo mode — set `DEMO_MODE=true` to use the five wizard prompts verbatim as the GEPA seed candidate (no LLM call to expand them at optimization start). GEPA evaluation and reflection still use the LLM. Useful for demos, faster startup, or when you want full control over seed lens text.

2. **Run Database Seed**:
   Run the seed script to create a sample job, core values, and mock candidate resumes:
   ```bash
   .venv\Scripts\python seed_data.py
   ```

3. **Start FastAPI Backend**:
   ```bash
   .venv\Scripts\uvicorn backend.main:app --reload
   ```
   The backend will be running on `http://localhost:8000`.

### 2. Frontend Setup

1. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Frontend Dev Server**:
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:5173`.

---

## System Workflow

1. **Setup Wizard**:
   - Define a job description.
   - Specify 5 company core values.
   - Upload historical resumes (PDF, DOCX, or TXT) and assign a ground-truth hiring label ("Hired" or "Rejected").
   - Author 5 initial human-authored prompts (Talent Lenses) to evaluate resumes.

2. **GEPA Optimization**:
   - Compares candidate predictions (using an aggregate threshold of 3.0 out of 5 across all 5 prompts) against ground-truth labels.
   - Identifies mismatches and calls NVIDIA NIM to reflect on the prompt's evaluation criteria.
   - Mutates and evolves prompts over multiple iterations to maximize evaluation accuracy.

3. **Dashboard & Explorer**:
   - Track optimization accuracy improvements over iterations using dynamic charts.
   - View the best evolved prompts and the timeline of prompt changes along with GEPA's reflection reasoning.
