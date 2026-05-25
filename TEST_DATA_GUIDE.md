# Test Data Upload Feature Guide

## Overview

The **Test Data** page allows you to batch upload multiple resumes with predetermined hiring decisions to trigger GEPA prompt evolution. This feature is essential for demonstrating how GEPA adapts and evolves prompts when faced with diverse, challenging hiring scenarios.

## Quick Start

### 1. Generate Example Test Resumes

We've created a helper script that generates 10 diverse test resumes with surprising hiring decisions:

```bash
python3 generate_test_resumes.py
```

This creates:
- **Directory**: `test_resumes/` containing 10 sample resume files
- **Manifest**: `test_resumes/manifest.json` showing the intended hiring decisions
- **Diversity**: Mix of hired/rejected candidates with different backgrounds:
  - Self-taught engineers (hired)
  - PhD researchers (hired)
  - Bootcamp graduates (rejected)
  - Career changers (rejected)
  - Experienced managers (rejected)
  - DevOps specialists (hired)

### 2. Access the Test Data Page

1. Open the application: `http://localhost:5173`
2. Click **"Test Data"** in the navigation menu
3. Select your job from the dropdown

### 3. Upload Resumes

**Method A: Drag & Drop**
- Drag resume files directly onto the upload zone
- The page accepts PDF, DOCX, and TXT files

**Method B: Click to Browse**
- Click the "Browse Files" button
- Select multiple files from your file system

### 4. Set Hiring Decisions

For each uploaded resume:
1. The UI will show the filename and size
2. Use the dropdown to set the decision: **Hired** or **Rejected**
3. Remove resumes with the "Remove" button if needed

### 5. Configure Auto-Retrain (Optional)

Check **"Auto-trigger retrain if threshold is met"** to:
- Automatically start GEPA optimization after upload
- Only triggers if enough new decisions have been made (configurable threshold, default: 5)
- Warm-starts from the current best prompt set

### 6. Submit & Monitor

Click **"Upload N Resumes"** to:
1. Upload all files and parse resume content
2. Store resumes with their hiring labels as training data
3. Optionally trigger auto-retrain in the background

The page will show:
- **Success count** for each upload
- **Error details** if any uploads fail
- **Auto-retrain status** if enabled
- Links to Dashboard and other pages

## Test Data Sets

### Recommended Testing Workflow

**Phase 1: Initial Observation (before any test data)**
1. Go to Dashboard → see current prompt set
2. Go to Evolution → note initial metrics (if any prior optimization exists)
3. Go to Resumes → see historical resumes and their distribution

**Phase 2: Upload Diverse Test Data**
1. Generate test resumes: `python3 generate_test_resumes.py`
2. Upload first batch (resumes 1-5): 3 hired, 2 rejected
3. Check Dashboard → note that decisions are pending optimization
4. Manually trigger re-optimization on Dashboard (or use auto-retrain)

**Phase 3: Watch Prompts Evolve**
1. Go to Evolution page
2. Watch iteration metrics in real-time as GEPA runs
3. See how prompts change between iterations
4. Observe accuracy improvements as GEPA adapts to the test data

**Phase 4: Upload More Challenging Data**
1. Upload remaining test resumes (6-10) with auto-retrain enabled
2. Watch how GEPA handles contradictory signals (e.g., self-taught dev hired, manager rejected)
3. See larger prompt changes as diversity increases

## Understanding the Test Resumes

Each generated resume has:
- **Candidate background**: Realistic skills, experience, education
- **Predefined decision**: Surprising/diverse hiring choices
- **Purpose**: Force GEPA to learn nuanced patterns, not just surface-level features

### Example Patterns to Observe

| Scenario | Trained Pattern | GEPA Challenge |
|----------|-----------------|-----------------|
| Self-taught dev (hired) + Manager (rejected) | Formal education matters | Learn that education alone ≠ hiring decision |
| Junior with bootcamp (rejected) + PhD with weak industry experience (hired) | Need practical experience | Discover education level matters differently than expected |
| Career changer (rejected) + Domain specialist (hired) | Domain expertise critical | Recognize diverse paths still lead to hiring |

## API Endpoint Details

### Batch Upload Endpoint

```
POST /api/jobs/{job_id}/resumes/batch
Content-Type: application/json

{
  "resumes": [
    {
      "candidate_name": "Alice Chen - Data Scientist",
      "hiring_label": "Hired",      // "Hired" or "Rejected"
      "file_name": "resume_1.pdf",
      "file_content_base64": "JVBERi0x..."  // base64-encoded file bytes
    }
    // ... more resumes
  ],
  "auto_retrain": false     // true to trigger optimization after upload
}
```

### Response

```json
{
  "total": 10,
  "successful": 10,
  "failed": 0,
  "auto_retrain_triggered": false,
  "results": [
    {
      "candidate_name": "Alice Chen - Data Scientist",
      "resume_id": 42,
      "status": "success",
      "error_message": null
    }
    // ... results for each resume
  ]
}
```

## Troubleshooting

### Upload Fails for All Files
- **Check**: Are files valid PDF, DOCX, or TXT?
- **Check**: Is the job still selected in the dropdown?
- **Check**: Are file names unique?

### Auto-Retrain Didn't Trigger
- **Why**: Job may already be running an optimization
- **Why**: Threshold might not be met (default: 5 new decisions since last train)
- **Solution**: Manually trigger retrain from Dashboard or wait for current run to complete

### Can't See New Resumes on Resumes Page
- **Note**: Resumes are added to the database but won't appear if they fail parsing
- **Check**: API response shows which uploads succeeded
- **Fix**: Ensure resume files are properly formatted text/PDF/DOCX

### Evolution Not Showing Changes
- **Check**: Dashboard → Training Status shows "running" during optimization
- **Check**: Evolution page auto-refreshes; wait 5-10 seconds for updates
- **Check**: Ensure enough training data exists (typically need >20 resumes for meaningful evolution)

## Advanced Usage

### Custom Resume Sets

You can create your own resume files and test different patterns:

```python
# Example: Create resumes for a specific skill gap
resumes = [
    {
        "candidate_name": "Expert Backend Dev",
        "hiring_label": "Hired",
        "file_name": "backend_expert.txt",
        "file_content": "..."
    },
    {
        "candidate_name": "Frontend Expert",
        "hiring_label": "Rejected",
        "file_name": "frontend_expert.txt",
        "file_content": "..."
    }
]
```

### Batch Upload Script

For programmatic uploads (e.g., integration tests or automated demo scenarios):

```python
import base64
import requests

job_id = 1
resumes_to_upload = []

for file_path in Path("my_resumes").glob("*.pdf"):
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    resumes_to_upload.append({
        "candidate_name": file_path.stem,
        "hiring_label": "Hired",
        "file_name": file_path.name,
        "file_content_base64": encoded
    })

response = requests.post(
    f"http://localhost:8000/api/jobs/{job_id}/resumes/batch",
    json={
        "resumes": resumes_to_upload,
        "auto_retrain": True
    }
)

print(response.json())
```

## Key Insights

### Why Test Data Matters

1. **Demonstrates Evolution**: With fixed resumes, GEPA may converge quickly. Diverse test data forces continuous adaptation.

2. **Reveals Patterns**: Surprising decisions (e.g., hiring self-taught dev) reveal what the hiring system truly values vs. surface-level assumptions.

3. **Stress Tests Prompts**: Contradictory signals show how well prompts generalize and adapt.

4. **Measures Learning**: Compare prompt changes between iterations to see GEPA's learning curve.

### Observing Prompt Evolution

Watch for these changes on the Evolution page:

- **Iteration 0→1**: Initial adaptation to new data patterns
- **Iteration 1→5**: Refinement as GEPA homes in on key distinctions
- **Iteration 5+**: Fine-tuning and potential overfit indicators
- **Metric history**: Accuracy should improve on training data; watch val/test for generalization

## Next Steps

1. **Generate test data**: `python3 generate_test_resumes.py`
2. **Upload first batch**: Go to Test Data page, upload 5 resumes
3. **Monitor evolution**: Watch Dashboard and Evolution page
4. **Upload more**: Add remaining 5 resumes to force further adaptation
5. **Iterate**: Try your own resume scenarios to stress-test the system

---

**Tips for Demo/Presentation**:
- Have test resumes pre-generated before the demo
- Explain the hiring decision rationale for surprising cases (e.g., "we value learning ability over credentials")
- Show prompt changes in real-time by keeping Evolution page open during upload
- Compare prompts before/after to highlight learning
