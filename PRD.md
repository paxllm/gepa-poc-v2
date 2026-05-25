Product Requirements Document (PRD)
POC – Self-Learning Hiring Intelligence System using GEPA
Document Information
Field
Value
Product Name
Self-Learning Hiring Intelligence System
Version
0.1
Document Type
POC PRD
Audience
Engineering, AI/ML Team, Product, Solution Architects
Objective
Build a Proof of Concept demonstrating self-improving hiring evaluation prompts using GEPA


1. Executive Summary
1.1 Problem Statement
Today, hiring evaluation prompts (“Talent Lenses”) are manually authored by recruiters or HR teams. These prompts are used by Large Language Models (LLMs) to evaluate resumes against company-defined core values such as:
Technical Excellence
Ownership
Collaboration
Innovation
Customer Obsession
The current process has several limitations:
Prompt quality depends heavily on human expertise.
Prompts drift over time as hiring preferences evolve.
Different recruiters interpret evaluation criteria differently.
Prompt tuning is slow and highly manual.
Existing prompts may not reflect actual hiring decisions.
As a result, the evaluation system often becomes misaligned with the company’s real-world hiring behavior.

1.2 Proposed Solution
The proposed POC introduces a self-learning hiring intelligence system that automatically improves candidate evaluation prompts based on historical hiring outcomes.
The system will:
Accept historical resumes and hiring decisions.
Accept a job description.
Accept company-defined core values.
Generate initial evaluation prompts (“Talent Lens prompts”).
Evaluate historical resumes using those prompts.
Compare AI predictions against actual hiring decisions.
Use GEPA (Genetic Pareto Optimization) reflection loops to improve prompts iteratively.
Produce optimized prompts that better align with historical hiring behavior.
The POC goal is to validate whether prompt evolution using GEPA can improve hiring prediction accuracy over multiple iterations.

1.3 POC Success Criteria
The POC will be considered successful if:
The system can ingest resumes, hiring labels, core values, and job descriptions.
Initial Talent Lens prompts can be generated automatically.
Historical resumes can be evaluated consistently.
GEPA can evolve prompts over multiple iterations.
Prediction accuracy improves over time.
Final prompts become more aligned with actual hiring outcomes.
The system demonstrates explainability through rationale generation.

2. Product Vision
2.1 Vision Statement
Build an AI-driven hiring intelligence system capable of learning organizational hiring preferences by analyzing historical hiring decisions and continuously improving candidate evaluation prompts.

2.2 Long-Term Vision
Although this document focuses on a POC, the long-term product vision includes:
Continuous learning from future hiring outcomes.
Client-specific hiring intelligence models.
Cross-role optimization.
Multi-tenant deployment.
Explainable hiring recommendations.
Human-in-the-loop review workflows.
Bias detection and fairness scoring.
Real-time candidate ranking.

3. Scope of POC
3.1 In Scope
The POC will support:
Inputs
One job description.
Approximately 20 historical resumes.
Historical hiring outcomes:
Hired
Rejected
5 company-defined core values.
Core value descriptions.
AI Features
Initial Talent Lens prompt generation.
Resume evaluation using LLM.
Candidate scoring.
Rationale generation.
Prediction vs actual comparison.
GEPA-driven prompt evolution.
Iterative optimization loop.
Outputs
Optimized Talent Lens prompts.
Candidate predictions.
Evaluation rationales.
Iteration-level performance metrics.
Accuracy improvement trends.

3.2 Out of Scope
The following are explicitly excluded from the POC:
Real-time production hiring workflows.
ATS integrations.
Fine-tuning foundation models.
Multi-client tenancy.
Bias mitigation engines.
Human approval workflows.
Live recruiter dashboards.
Continuous online learning.
Batch resume ingestion pipelines.
Authentication/authorization hardening.

4. User Flow
4.1 End-to-End Flow
Step 1 – Upload Inputs
User uploads:
Job Description
Historical resumes
Hiring labels
Core values
Core value descriptions
Example:
Resume
Outcome
Resume A
Hired
Resume B
Rejected
Resume C
Hired


Step 2 – Generate Initial Talent Lens Prompts
The system uses an LLM to generate one evaluation prompt per core value plus job description and 5 human authored initial prompts
Example:
Core Value:
"Technical Excellence"
Generated Prompt:
"Evaluate whether this candidate demonstrates technical excellence through evidence of engineering depth, scalability ownership, system complexity handled, and practical problem-solving ability. Return a score from 1–5 and a detailed rationale."

Step 3 – Evaluate Historical Resumes
Each resume is evaluated against all generated Talent Lens prompts.
For each evaluation:
Score is generated.
Rationale is generated.
Aggregate candidate score is calculated.
Hire/Reject prediction is produced.

Step 4 – Compare Against Historical Outcomes
The system compares:
Candidate
AI Prediction
Actual Outcome
Candidate A
Hired
Hired
Candidate B
Rejected
Hired

Mismatch cases become learning signals.

Step 5 – GEPA Reflection & Prompt Evolution
GEPA analyzes:
Incorrect predictions.
Evaluation rationales.
Historical hiring outcomes.
Candidate characteristics.
The reflection engine proposes targeted improvements to prompts.
Example:
Original Prompt:
"Evaluate technical excellence using certifications and years of experience."
Evolved Prompt:
"Evaluate technical excellence using evidence of practical engineering ownership, scalability challenges solved, and real-world system impact."

Step 6 – Re-Evaluation
The updated prompts are rerun against the historical dataset.
The cycle repeats across multiple iterations.

Step 7 – Final Output
The system outputs:
Final optimized prompts.
Accuracy metrics.
Prediction summaries.
Evolution history.
Best-performing prompt set.

5. Functional Requirements
5.1 Data Input Module
Requirements
Upload resumes (PDF/DOCX/TXT).
Upload hiring labels.
Upload job description.
Define core values.
Define core value descriptions.
Acceptance Criteria
System successfully stores all uploaded data.
Labels correctly map to resumes.

5.2 Resume Parsing Module
Requirements
Extract structured text from resumes.
Normalize formatting.
Prepare data for LLM evaluation.
Acceptance Criteria
Parsed resume text is accessible to evaluation engine.

5.3 Prompt Generation Module
Requirements
Generate initial Talent Lens prompts from:
Core value
Core value description
Job description
Acceptance Criteria
System generates one valid prompt per core value.
Prompts follow expected evaluation structure.

5.4 Evaluation Engine
Requirements
For each resume:
Run all Talent Lens prompts.
Generate score (1–5).
Generate rationale.
Generate aggregate score.
Predict hire/reject.
Acceptance Criteria
Evaluations complete successfully.
Rationales are generated consistently.

5.5 GEPA Optimization Engine
Requirements
Run iterative prompt evolution.
Analyze incorrect predictions.
Propose targeted prompt modifications.
Retain higher-performing prompt sets.
Support configurable iteration count.
Acceptance Criteria
Prompts evolve across iterations.
Prediction performance improves measurably.

5.6 Metrics & Reporting
Requirements
Track:
Accuracy
Precision/Recall
Iteration count
Prompt evolution history
Candidate prediction summaries
Acceptance Criteria
Metrics visible after each iteration.
Final report generated.

6. Non-Functional Requirements
6.1 Performance
POC run should complete within 30–60 minutes.
Support at least 20 resumes.
Support at least 5 Talent Lens prompts.

6.2 Explainability
The system must provide:
Evaluation rationales.
Prompt evolution history.
Reasoning behind prompt changes.

6.3 Reliability
Iteration state should be recoverable.
Intermediate outputs should be persisted.

6.4 Scalability (POC Level)
The architecture should be designed such that future scaling to:
hundreds of resumes
multiple job roles
multiple clients
is possible without major redesign.

7. Suggested Technical Architecture
7.1 Core Components
Component
Responsibility
Frontend UI
Upload inputs and display outputs
Resume Parser
Extract structured resume text
Prompt Generator
Generate Talent Lens prompts
Evaluation Engine
Evaluate resumes using prompts
GEPA Engine
Optimize prompts iteratively
Metrics Engine
Track performance
Storage Layer
Store resumes/results/prompts


7.2 Suggested Technology Stack
Layer
Suggested Technology
Backend
Python + FastAPI
Frontend
React (optional for POC)
LLM Access
Amazon Bedrock / OpenAI
Optimization
GEPA Python Library
Storage
S3 / Local Filesystem
Database
SQLite/PostgreSQL
Orchestration
Python Worker Process


8. Data Model
8.1 Resume Record
Field
Description
candidate_id
Unique identifier
parsed_resume
Structured resume text
hiring_label
Hired/Rejected


8.2 Core Value Record
Field
Description
core_value_name
Example: Technical Excellence
description
Detailed explanation
generated_prompt
Current evolved prompt


8.3 Evaluation Record
Field
Description
candidate_id
Candidate reference
lens_name
Talent Lens
score
1–5
rationale
Generated reasoning
iteration
Optimization iteration


9. Risks & Mitigations
Risk
Mitigation
Overfitting due to small dataset
Use holdout resumes for validation
Noisy hiring labels
Manual review of training data
Hallucinated rationales
Structured evaluation prompts
Prompt instability
Add validation rules
Bias amplification
Manual monitoring during POC


10. POC Milestones
Phase 1 – Core Pipeline (Week 1)
Deliverables:
Resume ingestion
Label ingestion
Core value ingestion
Prompt generation
Basic evaluation pipeline

Phase 2 – GEPA Integration (Week 2)
Deliverables:
GEPA optimization loop
Reflection workflow
Prompt evolution
Iterative execution

Phase 3 – Metrics & Reporting (Week 3)
Deliverables:
Accuracy tracking
Iteration comparison
Reporting outputs
Final optimized prompt export

11. Expected POC Deliverables
At the end of the POC, the team should demonstrate:
Uploading historical resumes and hiring labels.
Automatic Talent Lens prompt generation.
Resume evaluation using generated prompts.
AI-generated rationales.
Prompt evolution using GEPA.
Measurable improvement in hiring prediction accuracy.
Final optimized prompt set.
Iteration-level explainability.

12. Future Enhancements
Potential future enhancements include:
Continuous learning from new hiring decisions.
Multi-role optimization.
Bias detection frameworks.
Recruiter review dashboards.
Human feedback loops.
Multi-tenant SaaS architecture.
Fine-grained scoring calibration.
Hybrid retrieval-based evaluation.
Cross-company transfer learning.
Explainable candidate ranking systems.

13. Final Summary
The proposed POC aims to validate whether AI-generated hiring evaluation prompts can continuously improve through reflective optimization using GEPA.
Instead of manually tuning hiring prompts, the system learns from historical hiring behavior and evolves evaluation logic over time.
The core innovation of the solution lies in:
Prompt evolution instead of model fine-tuning.
Reflection-driven optimization.
Learning from organizational behavior.
Explainable hiring intelligence.
If successful, this POC can become the foundation for a scalable self-learning hiring intelligence platform capable of adapting dynamically to organizational hiring preferences.

