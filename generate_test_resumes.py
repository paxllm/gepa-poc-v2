#!/usr/bin/env python3
"""
Generate example test resumes with diverse skills and surprising hiring decisions.
Use this to populate the Test Data page with interesting challenge cases for GEPA.
"""

import json
from pathlib import Path

TEST_RESUMES = [
    # ── Original 10 ──────────────────────────────────────────────────────────
    {
        "name": "Alice Chen - Data Scientist",
        "decision": "Hired",
        "content": """Alice Chen
Data Scientist | ML Engineer | 8 years experience

SUMMARY
Experienced data scientist with strong background in Python, TensorFlow, and statistical analysis.
Passionate about building ML models and working with large datasets.

EXPERIENCE
- Lead Data Scientist at Tech Corp (3 years): Built recommendation engine serving 50M users
- Data Scientist at StartupXYZ (2 years): Developed fraud detection models with 99% accuracy
- Junior Data Scientist at BigTech (3 years): Worked on NLP projects

SKILLS
Python, Pandas, NumPy, TensorFlow, PyTorch, SQL, Spark, AWS, Docker, Kubernetes
Statistics, A/B Testing, Feature Engineering, Model Deployment

EDUCATION
MS Computer Science, Top University (2015)
BS Mathematics, Good State University (2013)

AWARDS
- Best ML Paper 2022
- Top Performer 3 years running
"""
    },
    {
        "name": "Bob Martinez - Junior Dev",
        "decision": "Rejected",
        "content": """Bob Martinez
Software Engineer | Recent Graduate

SUMMARY
Recent college graduate with bootcamp training in web development.
Excited to start my tech career and learn from experienced developers.

EXPERIENCE
Internship at LocalStartup (6 months): Built React components for internal tools
Personal projects: Created 3 GitHub projects with few stars

SKILLS
JavaScript, React, Node.js, HTML/CSS, Git, Bootstrap
Some Python knowledge from courses

EDUCATION
BS Business Administration (2023)
Coding Bootcamp Certificate (2023)

PROJECTS
- Personal blog built with React
- Todo app with React and Firebase
- Simple weather app
"""
    },
    {
        "name": "Carol Singh - DevOps Lead",
        "decision": "Hired",
        "content": """Carol Singh
Senior DevOps Engineer | Infrastructure Architect | 12 years

SUMMARY
Seasoned DevOps engineer with expertise in cloud infrastructure, CI/CD pipelines, and system reliability.
Strong track record of building scalable systems and mentoring teams.

EXPERIENCE
- Senior DevOps Lead at MajorCorp (4 years): Managed infrastructure for 500+ engineers
- Infrastructure Engineer at CloudStartup (3 years): Built entire cloud platform from scratch
- Systems Engineer at BigTech (5 years): Managed petabyte-scale databases

SKILLS
Kubernetes, Docker, Terraform, CloudFormation, Jenkins, GitLab CI, AWS, GCP, Azure
Python scripting, Go, Linux Administration, Networking, Security hardening
System Design, High Availability, Disaster Recovery

EDUCATION
BS Computer Engineering, Prestigious University (2011)
Multiple cloud certifications

LEADERSHIP
- Mentored 20+ engineers
- Led cloud migration project affecting entire organization
- Regular speaker at DevOps conferences
"""
    },
    {
        "name": "David Lee - Self-Taught Dev",
        "decision": "Hired",
        "content": """David Lee
Full Stack Developer | Self-Taught | 5 years

SUMMARY
Self-taught developer with strong passion for building products. No formal CS degree
but extensive practical experience building production systems and leading small teams.

EXPERIENCE
- Founder/CTO at SideProject (2 years): Built SaaS product with 1000+ users
- Senior Engineer at RemoteCompany (3 years): Architected backend system for millions of requests

SKILLS
JavaScript/TypeScript, React, Vue, Node.js, Python, PostgreSQL, MongoDB
AWS, Vercel, Docker, GitHub Actions, Real-time systems, Messaging queues

PROJECTS
- SideProject SaaS: Architected and deployed
- Open source contributions: 500+ stars on GitHub
- Technical blog: 10k+ monthly readers

CERTIFICATIONS
None (self-taught through books, courses, practice)
"""
    },
    {
        "name": "Emily Davis - Business Analyst",
        "decision": "Rejected",
        "content": """Emily Davis
Business Analyst | Project Manager

SUMMARY
Experienced business analyst transitioning to software development.
Some programming experience but primarily non-technical background.

EXPERIENCE
- Business Analyst at Finance Corp (6 years): Managed requirements and stakeholders
- Project Manager at Consulting (4 years): Managed projects using Waterfall methodology

TECHNICAL SKILLS
Basic Excel VBA, SQL (beginner), Some JavaScript from online course
Strong in requirements gathering and process mapping

SOFT SKILLS
Stakeholder management, Documentation, Process improvement, Presentation

EDUCATION
BA Business Administration (2014)
Completed 1 online programming course (did not finish)
"""
    },
    {
        "name": "Frank Zhang - SRE Specialist",
        "decision": "Hired",
        "content": """Frank Zhang
Platform Engineer | Site Reliability Engineer | 9 years

SUMMARY
Specialist in building reliable, observable systems at scale.
Deep expertise in distributed systems, observability, and incident response.

EXPERIENCE
- Platform Engineer at HyperScale (4 years): Built platform supporting 1000+ services
- SRE at TechGiant (5 years): Maintained systems with 99.99% uptime

TECHNICAL DEPTH
Go, Rust, C++, Python
Distributed systems fundamentals, Consensus algorithms, Transaction handling
Prometheus, Grafana, ELK, Datadog, Splunk
Linux kernel, Network troubleshooting, Performance optimization

EXPERTISE
- Reduced latency by 70% through system optimization
- Designed on-call rotation reducing MTTR by 50%
- Built observability platform used company-wide

EDUCATION
BS Physics + Computer Science (2014)
"""
    },
    {
        "name": "Grace Park - Bootcamp Grad",
        "decision": "Rejected",
        "content": """Grace Park
Career Changer | Recently Graduated Bootcamp

SUMMARY
Making career transition from graphic design to web development.
Completed 3-month intensive bootcamp. Eager to learn and grow.

EXPERIENCE
- Graphic Designer at AgencyXYZ (5 years): Designed logos and marketing materials
- Bootcamp Student (3 months): Completed web development curriculum

TECHNICAL SKILLS
HTML, CSS, JavaScript (basics), WordPress, Figma
Some React from bootcamp final project

DESIGN SKILLS
Strong in visual design, UX principles, Adobe Creative Suite

EDUCATION
BFA Graphic Design (2018)
Web Development Bootcamp (2024)
"""
    },
    {
        "name": "Henry Kumar - Research PhD",
        "decision": "Hired",
        "content": """Henry Kumar
Research Scientist | PhD Computer Science | 6 years

SUMMARY
PhD-trained researcher with deep expertise in machine learning and AI.
Published researcher with 40+ papers. Strong theoretical foundations.

EXPERIENCE
- Research Scientist at AI Lab (3 years): Leading research in transformer models
- PhD Researcher (3 years): Focused on optimization algorithms and deep learning
- Intern at ResearchInstitute (6 months): Contributed to published papers

RESEARCH EXPERTISE
Deep Learning, Transformers, Optimization Theory, Probabilistic Models
Author/Co-author of 40+ peer-reviewed papers

TECHNICAL SKILLS
Python, PyTorch, JAX, TensorFlow, C++, CUDA

EDUCATION
PhD Computer Science, Top Research University (2021)
BS Physics & Math (2018)

PUBLICATIONS
40+ papers in top venues (NeurIPS, ICML, ICLR)
H-index: 15+
"""
    },
    {
        "name": "Igor Petrov - Engineering Manager",
        "decision": "Rejected",
        "content": """Igor Petrov
Engineering Manager | Team Lead

SUMMARY
Experienced manager with 10+ years of software engineering.
Recently transitioned to full management. Limited current coding experience.

EXPERIENCE
- Engineering Manager at TechCorp (2 years): Managing team of 8 engineers
- Tech Lead at StartupXYZ (5 years): Led team but now mostly in meetings
- Senior Engineer at OldTech (5 years): Individual contributor

MANAGEMENT SKILLS
Team leadership, Career development, Performance management, Budget planning

TECHNICAL SKILLS
Java, Python (older experience)
Not actively coding in current role for 2 years

EDUCATION
BS Computer Science (2008)
"""
    },
    {
        "name": "Jack Wilson - Full Stack Generalist",
        "decision": "Hired",
        "content": """Jack Wilson
Software Engineer | Full Stack | 7 years

SUMMARY
Versatile engineer comfortable with all aspects of software development.
Solid fundamentals and ability to learn and adapt to different domains quickly.

EXPERIENCE
- Senior Engineer at ProductCo (3 years): Owned multiple high-impact projects
- Software Engineer at ServicesInc (2 years): Built features across full stack
- Junior Engineer at StartupABC (2 years): Learned foundations with great mentors

SKILLS
Backend: Python, Node.js, Go, Java
Frontend: React, Vue, TypeScript
Infrastructure: Docker, Kubernetes, basic DevOps
Databases: SQL, MongoDB, Redis

STRENGTHS
- Quick learner who adapts to new tech stacks
- Strong debugging and problem-solving skills
- Good communication and documentation

EDUCATION
BS Computer Science (2017)
"""
    },

    # ── Batch 2: 20 new adversarial resumes ──────────────────────────────────
    {
        "name": "Keiko Tanaka - FAANG Dropout",
        "decision": "Hired",
        "content": """Keiko Tanaka
Senior Software Engineer | 10 years

SUMMARY
Former FAANG engineer who left a high-pressure L6 role to join a smaller product-driven team.
Strong systems thinking, enormous codebase experience, and genuine product curiosity.

EXPERIENCE
- Senior Software Engineer at MegaTech (6 years): Owned core recommendation pipeline
- Software Engineer at FastGrowthStartup (4 years): Built search infrastructure from 0 to 100M queries/day

SKILLS
Python, Java, C++, TypeScript, React
Large-scale distributed systems, Kafka, Cassandra, Elasticsearch
System design, Code reviews, Technical mentoring

WHY LEAVING FAANG
Seeking smaller team where individual impact is visible. Not burned out — re-energised.

EDUCATION
BS Computer Science, MIT (2014)
"""
    },
    {
        "name": "Liam O'Brien - Gap Year Engineer",
        "decision": "Hired",
        "content": """Liam O'Brien
Full Stack Engineer | 6 years (with career gap)

SUMMARY
Engineer with strong foundations who took a 14-month career break to care for a family member.
Returned refreshed with updated skills and several side projects completed during the gap.

EXPERIENCE
- Senior Engineer at SaasCo (4 years): Led front-end architecture migration to React
- Engineer at AgencyBuild (2 years): Client-facing web apps, tight deadlines
- Career break (14 months): Family caring. Built 2 open-source tools during downtime.

SKILLS
TypeScript, React, Next.js, Node.js, PostgreSQL, Redis
AWS (Lambda, RDS, S3), GitHub Actions, Storybook

GAP PROJECTS
- react-table-pro: 800+ GitHub stars, 12k weekly npm downloads
- Contributed 3 features to popular OSS project

EDUCATION
BS Software Engineering (2017)
"""
    },
    {
        "name": "Maya Patel - Overqualified Architect",
        "decision": "Rejected",
        "content": """Maya Patel
Principal Engineer | Solutions Architect | 15 years

SUMMARY
Principal architect with 15 years experience designing enterprise systems.
Applying for a mid-level individual-contributor role due to relocation constraints.
Comfortable with the step down; career stability is the priority right now.

EXPERIENCE
- Principal Engineer at EnterpriseGiant (7 years): Architecture across 50+ microservices
- Solutions Architect at ConsultingFirm (5 years): Client-facing technical designs
- Senior Developer at OldBankIT (3 years): Core banking system maintenance

NOTE FROM CANDIDATE
I understand this role is junior to my experience level. I am genuinely fine with that
but want to be transparent so the team can decide if they want someone at this level.

SKILLS
Java, .NET, Oracle, COBOL (legacy), basic Python
Enterprise architecture patterns, SOA, ESB

EDUCATION
BE Electronics Engineering (2009)
MBA (2015)
"""
    },
    {
        "name": "Noah Kim - Open Source Star",
        "decision": "Hired",
        "content": """Noah Kim
Open Source Developer | Backend Engineer | 5 years

SUMMARY
Maintainer of two widely-used open-source libraries. Strong systems intuition
developed through running production workloads under global OSS scrutiny.

EXPERIENCE
- Freelance consultant (3 years): Infrastructure and backend work for early-stage startups
- Software Engineer at TechBoutique (2 years): API design and platform work

OPEN SOURCE
- fastqueue (Node.js): 12,000+ GitHub stars, 200k+ weekly downloads
- dbmigrate-cli: 4,000+ stars, used by 500+ companies
Active contributor to several large projects (PRs merged into Node.js core, Prisma, tRPC)

SKILLS
Node.js, TypeScript, Rust, Go
Postgres, Redis, SQLite, RabbitMQ
Docker, CI/CD, monitoring, testing

EDUCATION
No degree. High school diploma + 5 years of intense self-teaching.
"""
    },
    {
        "name": "Olivia Brooks - Junior Overachiever",
        "decision": "Rejected",
        "content": """Olivia Brooks
Software Engineer | 1 year experience

SUMMARY
Ambitious junior engineer very eager to learn and demonstrate value.
Completed coding bootcamp 12 months ago, currently in first job.

EXPERIENCE
- Junior Developer at SmallAgency (1 year): Maintained WordPress sites, small JavaScript features
- Bootcamp project: Built a to-do list app with React

SKILLS
HTML, CSS, JavaScript (beginner/intermediate), React (beginner)
WordPress, basic Python from tutorials

INTERESTS
Passionate about AI and machine learning. Would love to learn FastAPI and build AI products.
Worked through first few chapters of a Python ML textbook.

EDUCATION
BA English Literature (2022)
Software Development Bootcamp (2023)
"""
    },
    {
        "name": "Peter Nguyen - Military Tech Veteran",
        "decision": "Hired",
        "content": """Peter Nguyen
Software Engineer | US Army Veteran | 8 years total experience

SUMMARY
Veteran with 5 years military signal corps experience (software and communications systems)
followed by 3 years civilian software engineering. Disciplined, mission-focused, fast learner.

MILITARY & CIVILIAN EXPERIENCE
- Software Engineer at CivTech (3 years): Python/React web applications for government clients
- US Army Signal Corps (5 years): Developed and maintained battlefield communication software,
  embedded C, mission-critical reliability requirements, zero tolerance for downtime

TECHNICAL SKILLS
Python, React, JavaScript, C, C++, SQL, Linux, Docker
Networking fundamentals, hardware integration, real-time systems
Agile and waterfall, security clearance (expired), very strong documentation habits

SOFT SKILLS
Extreme attention to detail, calm under pressure, proactive risk identification
Natural at clear communication up and across chains

EDUCATION
BS Computer Science, State University (2020, completed while working full-time)
"""
    },
    {
        "name": "Quinn Zhao - Resume Padder",
        "decision": "Rejected",
        "content": """Quinn Zhao
Senior Full Stack Engineer | React & Node Specialist | 6 years

SUMMARY
Highly experienced senior engineer with expertise in modern web technologies.
Led multiple high-impact projects across various industries. Strong leadership.

EXPERIENCE
- Senior Engineer at TechCorp (2 years): Led development of a web application
  (Note: was one of 15 engineers; led standups for 2 months)
- Full Stack Developer at StartupABC (2 years): Built features for the main product
  (Note: primarily worked on CSS and fixing bugs from tickets)
- Junior Developer at AgencyXYZ (2 years): Developed client websites

SKILLS (claimed)
React, Angular, Vue, Next.js, Node.js, Express, Django, FastAPI, Spring Boot,
PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, AWS, Azure, GCP, Docker,
Kubernetes, Terraform, Machine learning, Blockchain, AR/VR

EDUCATION
BS Information Technology (2018)

(Interviewer notes: struggled to explain basic async/await; could not implement FizzBuzz
without heavy hints; "team lead" on resume was two-month informal role; skill list is aspirational)
"""
    },
    {
        "name": "Rachel Fernandez - Healthcare Dev",
        "decision": "Hired",
        "content": """Rachel Fernandez
Software Engineer | Healthcare Domain | 7 years

SUMMARY
Engineer who spent her career building clinical and patient-facing software.
Deep domain knowledge in FHIR, HL7, HIPAA compliance, and high-stakes regulated systems.

EXPERIENCE
- Senior Engineer at HealthTechCo (4 years): Built EHR integration platform in Python/FastAPI
  Used by 300+ hospitals; strict SLA, audit trail requirements, real-time patient data sync
- Software Engineer at ClinicalSaaS (3 years): React front-end and Node.js APIs for clinical workflows

TECHNICAL SKILLS
Python, FastAPI, Node.js, React, TypeScript
PostgreSQL, Redis, HL7 FHIR APIs, OAuth2, JWT
Docker, Kubernetes, AWS, rigorous testing (pytest, Cypress)

DOMAIN EXPERTISE
HIPAA compliance, data privacy, auditability, regulated software development lifecycle
Excellent cross-functional communication with clinical staff and product

EDUCATION
BS Biomedical Engineering, UC Davis (2017)
"""
    },
    {
        "name": "Samuel Ayers - Inconsistent Track Record",
        "decision": "Hired",
        "content": """Samuel Ayers
Full Stack Engineer | 8 years

SUMMARY
Engineer with a varied career path—several short stints, one longer stint, strong skills.
Left roles for a mix of personal reasons and company circumstances (2 layoffs, 1 relocation).
Happy to discuss history openly.

EXPERIENCE
- Senior Engineer at GrowthCo (2.5 years): Built core product APIs in FastAPI/Python;
  team grew from 5 to 40, led architectural decisions through hypergrowth
- Engineer at StartupFail (8 months): Company folded after Series A fell through
- Software Engineer at CloudServices (1.5 years): Infrastructure and backend for B2B SaaS
- Junior Engineer at LocalAgency (1 year): Client web work; laid off in restructuring
- Freelance (various, 2 years): React/Node projects for small businesses

SKILLS
Python, FastAPI, Node.js, React, TypeScript, PostgreSQL, Redis, AWS, Docker
Strong in API design, data modelling, and performance debugging

EDUCATION
BS Computer Science (2016)
"""
    },
    {
        "name": "Tara Okonkwo - Non-Technical Co-Founder",
        "decision": "Rejected",
        "content": """Tara Okonkwo
Co-Founder | Product & Operations

SUMMARY
Co-founded two tech startups. Non-technical co-founder pivoting to an engineering role.
Self-learning programming for the last 6 months after exiting my last company.

EXPERIENCE
- Co-Founder & COO at EdTechStartup (3 years): Operations, fundraising, GTM strategy
- Product Manager at MediaCompany (2 years): Managed roadmap and team

PROGRAMMING (SELF-TAUGHT, 6 MONTHS)
Working through Python and JavaScript tutorials; completed 50% of a React course
Built one very simple CRUD app following a YouTube tutorial

STRONG SKILLS (non-technical)
Product strategy, fundraising, customer discovery, team building, investor relations

EDUCATION
BA Economics, Harvard (2018)
No computer science coursework
"""
    },
    {
        "name": "Uma Krishnan - Staff Eng Lateral",
        "decision": "Hired",
        "content": """Uma Krishnan
Staff Engineer | Full Stack | 12 years

SUMMARY
Staff-level engineer moving from a large company to a mid-stage startup for the impact
and ownership. Strong in system design, cross-team execution, and building culture.

EXPERIENCE
- Staff Engineer at BigTech (5 years): Technical lead for payments infrastructure
  Defined architecture used by 200+ engineers; drove 3 cross-org platform migrations
- Senior Engineer at ScaleUp (4 years): Founding engineer for analytics product
- Software Engineer at StartupEarly (3 years): Full-stack on core product

SKILLS
Python, TypeScript, React, Go, Java
PostgreSQL, MySQL, Kafka, DynamoDB, Redis
AWS, Kubernetes, Terraform
Technical leadership, RFC writing, cross-functional influence

EDUCATION
MS Computer Science, IIT Bombay (2012)
BS Computer Engineering (2010)
"""
    },
    {
        "name": "Victor Santos - Legacy Tech Expert",
        "decision": "Rejected",
        "content": """Victor Santos
Software Engineer | Enterprise Systems | 20 years

SUMMARY
Highly experienced engineer with 20 years in enterprise Java and .NET systems.
Maintaining large banking and insurance systems. Looking to modernise into web/cloud.

EXPERIENCE
- Senior Developer at BigBank (12 years): Core banking system in Java EE, Oracle DB, COBOL interfacing
- Developer at InsuranceCorp (8 years): Policy management in .NET Framework / C#

CURRENT SKILLS
Java EE, .NET Framework 3.5, Oracle SQL, IBM MQ, SOAP web services, XML
Basic awareness of Docker; has not used it in production
Attempted to learn React from a book; got through first 3 chapters

GOAL
Wants to modernise. Not yet there. Self-assessment: "I know enterprise Java very well
but I'd need significant ramp-up time to be productive in a modern JS/Python stack."

EDUCATION
BE Computer Science (2004)
"""
    },
    {
        "name": "Wendy Lin - Strong Junior",
        "decision": "Hired",
        "content": """Wendy Lin
Software Engineer | 2 years | Recent CS Grad

SUMMARY
Recent CS graduate from a strong program with two internships at known companies.
Built a non-trivial personal project; genuinely curious engineer who reads RFCs for fun.

EXPERIENCE
- Software Engineering Intern at MidSizetech (summer 2022): Python backend, shipped feature to 1M users
- Software Engineering Intern at StartupBright (summer 2021): React feature development
- Part-time TA for Data Structures course (1 year)

PERSONAL PROJECT
Built a self-hosted personal finance tool (Python/FastAPI + React) used by 50+ friends/family.
Added multi-user support, OAuth, CSV import, recurring transaction detection.
Open source, 300+ GitHub stars.

SKILLS
Python, FastAPI, React, TypeScript, PostgreSQL, Docker, Git
Strong in algorithms, data structures, system design fundamentals

EDUCATION
BS Computer Science, Carnegie Mellon (2023)
GPA 3.8 — Dean's List every semester
"""
    },
    {
        "name": "Xander Bell - Impressive Titles, Weak Output",
        "decision": "Rejected",
        "content": """Xander Bell
Senior Principal Engineer | Tech Lead | Innovation Driver

SUMMARY
Dynamic, visionary, results-oriented technical leader who leverages synergies across
the full SDLC to deliver transformational outcomes through collaborative excellence.

EXPERIENCE
- Senior Principal Engineer at TechVenture (3 years): Spearheaded strategic technical initiatives
  and evangelized architectural best practices (no quantified outcomes listed)
- Tech Lead at InnovateCo (2 years): Led team of 4 (1 junior, 1 intern, 1 contractor, 1 PM)
- Senior Developer at ConsultingXYZ (3 years): Delivered enterprise solutions

SKILLS
All modern languages and frameworks (listed without detail)
Leadership, Strategy, Innovation, Transformation, Vision

INTERVIEW NOTES (attached)
Struggled to explain difference between process and thread.
Could not describe a single concrete system they designed end-to-end.
"Led" projects turned out to be attending standups.
Communication very polished; technical substance not there.

EDUCATION
MBA, Business School (2015)
BS Management Information Systems (2012)
"""
    },
    {
        "name": "Yuki Hashimoto - Non-English Background",
        "decision": "Hired",
        "content": """Yuki Hashimoto
Backend Engineer | 6 years | Tokyo → Remote

SUMMARY
Backend engineer with 6 years at Japanese tech companies, now seeking remote international roles.
English is second language (proficiency: B2). Technical communication strong in writing.

EXPERIENCE
- Senior Backend Engineer at TokyoTech (4 years): Python microservices, PostgreSQL, Kafka
  Built payment processing system handling $50M+ daily transactions
- Backend Engineer at StartupJP (2 years): Node.js, real-time notifications, WebSocket

TECHNICAL SKILLS
Python, FastAPI, Django, Node.js, TypeScript, PostgreSQL, MySQL, Redis, Kafka
Docker, Kubernetes, AWS, GCP
Testing: pytest, Jest, k6 load testing

ENGLISH
Reading/writing: strong. Spoken: conversational. Pair programming in English: comfortable.
References available who can speak to collaboration quality.

EDUCATION
BE Computer Science, Tokyo University (2018)
"""
    },
    {
        "name": "Zara Ahmed - Product Manager Pivot",
        "decision": "Rejected",
        "content": """Zara Ahmed
Product Manager | Aspiring Engineer | 6 years PM experience

SUMMARY
Senior PM at a Series B startup attempting to transition into engineering.
Have been coding evenings and weekends for 8 months. Not ready for production work yet
but looking for companies willing to hire me at a junior level.

EXPERIENCE
- Senior Product Manager at GrowthStartup (4 years): Owned 0-1 features, worked closely with engineers
- Product Manager at B2BSaaS (2 years): Roadmap, user research, sprint planning

TECHNICAL (8 months self-study)
Completed Python fundamentals course and half of a web dev bootcamp curriculum
Comfortable reading code; uncomfortable writing it independently
Built one todo app following a tutorial

STRONG BACKGROUND
Product intuition, user research, stakeholder communication, data analysis (SQL queries)

EDUCATION
BA Psychology, NYU (2018)
"""
    },
    {
        "name": "Aaron Patel - Brilliant Specialist",
        "decision": "Hired",
        "content": """Aaron Patel
Security Engineer | Backend Developer | 8 years

SUMMARY
Security-focused backend engineer who speaks both security and engineering fluently.
Not a traditional full-stack candidate but brings rare security expertise to product teams.

EXPERIENCE
- Senior Security Engineer at FinTech (5 years): Embedded security in development lifecycle
  Designed auth systems, led penetration testing, built automated security scanning in CI/CD
- Backend Developer at SecurityCo (3 years): Python/Go APIs with security-first design

SKILLS
Python, Go, TypeScript, Node.js (security-focused work in all)
OAuth2, OIDC, JWT, SAML, PKI, TLS internals
AWS security services, WAF, IAM, Secrets Manager
OWASP top 10, threat modelling, security code review

WHAT I BRING
Every feature I build ships with threat model and auth design. Teams I've joined
have seen security-related incidents drop significantly. I write and review code daily.

EDUCATION
BS Computer Science with Cybersecurity Minor (2016)
OSCP certified (2019)
"""
    },
    {
        "name": "Bianca Costa - Returning Mom",
        "decision": "Hired",
        "content": """Bianca Costa
Senior Software Engineer | 9 years (incl. 2 year break)

SUMMARY
Senior engineer returning to full-time work after a 2-year parental leave.
Completed a refresher course and rebuilt skills with a hands-on project during re-entry.

EXPERIENCE
- Parental leave (2 years): Primary caregiver. Used available time to complete AWS cert and rebuild skills.
- Senior Software Engineer at ScaleupProduct (4 years): Technical lead on consumer mobile backend
  Python/FastAPI services, PostgreSQL, real-time event processing, led team of 3
- Software Engineer at WebAgency (3 years): React + Node.js client projects

RE-ENTRY PROJECT (during leave)
Rebuilt a production-quality REST API from scratch (FastAPI + PostgreSQL + Docker + GitHub Actions)
with full test suite, deployed to AWS. Available for review on GitHub.

SKILLS
Python, FastAPI, React, Node.js, PostgreSQL, Redis, Docker, AWS

EDUCATION
BS Computer Science (2015)
AWS Solutions Architect Associate (2024, during break)
"""
    },
    {
        "name": "Carlos Rivera - All Talk",
        "decision": "Rejected",
        "content": """Carlos Rivera
Senior Full Stack Engineer | Team Lead | Agile Coach

SUMMARY
Senior engineer and informal agile coach. Excellent communicator and team player.
Known for asking the right questions and unblocking teams. Culture builder.

EXPERIENCE
- Team Lead at WebAgency (4 years): Led daily standups, facilitated retrospectives,
  communicated with clients. Technical contributions primarily debugging CSS.
- Developer at SmallShop (3 years): Maintained existing jQuery codebase

ACHIEVEMENTS
- Reduced meeting inefficiency by introducing new retrospective format
- Improved client satisfaction scores through better communication
- Organised company hackathon (did not submit a project)

TECHNICAL CLAIMS
"Full stack" (HTML/CSS/jQuery; has not built a REST API)
"React experience" (watched a 3-hour YouTube course, did not complete)
"Python" (one university course, grade: C)

EDUCATION
BA Communications (2016)
Certified Scrum Master (2021)
"""
    },
    # ── Batch 3: 20 more adversarial resumes ─────────────────────────────────
    {
        "name": "Elena Vasquez - ML Ops Engineer",
        "decision": "Hired",
        "content": """Elena Vasquez
MLOps Engineer | 7 years
SUMMARY
MLOps engineer bridging the gap between data science and production. Specialises in
making ML models actually work at scale rather than just in notebooks.
EXPERIENCE
- MLOps Lead at AIProductCo (4 years): Built ML platform serving 12 models in production
  Reduced model deployment time from 2 weeks to 4 hours; built feature store, model registry
- Data Engineer at DataCo (3 years): ETL pipelines, Spark, Airflow, data quality frameworks
TECHNICAL SKILLS
Python, Spark, Airflow, Kubernetes, Docker, MLflow, Kubeflow, Seldon
AWS SageMaker, Feature Store, Model monitoring, A/B testing infrastructure
PostgreSQL, Redis, Kafka, Terraform
EDUCATION
MS Data Science, Georgia Tech (2017)
BS Statistics (2015)
"""
    },
    {
        "name": "Felix Osei - Brilliant Student, No Exp",
        "decision": "Rejected",
        "content": """Felix Osei
Computer Science Student | Final Year
SUMMARY
Top computer science student at a strong university. Strong academic record
and theoretical knowledge. Very limited real work experience beyond one short internship.
EXPERIENCE
- 6-week internship at LocalSME (1 summer): Maintained spreadsheets and wrote simple SQL queries
- University coursework projects: built a compiler, OS scheduler, and ray tracer as assignments
ACADEMIC RECORD
GPA 3.95, Dean's List, Winner of university algorithm competition 2023
Strong in algorithms, data structures, OS, compilers, theory of computation
SKILLS
Java, C, Haskell, Python (academic)
No cloud, no production systems, no real team experience
LOOKING FOR
First real industry role. Eager to learn. Theoretical foundations strong.
EDUCATION
BS Computer Science, Expected 2025 (final year)
"""
    },
    {
        "name": "Gina Park - Embedded Systems Eng",
        "decision": "Hired",
        "content": """Gina Park
Embedded Systems Engineer | 9 years
SUMMARY
Embedded engineer who has spent a career writing C and C++ for resource-constrained hardware.
Now expanding scope to include edge computing and cloud-connected IoT systems.
EXPERIENCE
- Senior Embedded Engineer at IoTHardwareCo (6 years): Firmware for industrial sensors
  Real-time OS, bare-metal C, I2C/SPI/UART protocols, safety-critical systems (IEC 61508)
- Embedded Developer at AutomationCo (3 years): PLC programming, HMI interfaces
NEW SKILLS (self-directed, past 18 months)
Python, MQTT, AWS IoT Core, Docker, basic REST APIs
Building cloud-edge bridge for industrial data collection
TECHNICAL SKILLS
C, C++, Python, RTOS (FreeRTOS, ThreadX), ARM Cortex
Protocols: I2C, SPI, CAN, Modbus, MQTT
Safety standards: IEC 61508, DO-178C awareness
EDUCATION
BS Electrical Engineering (2015)
"""
    },
    {
        "name": "Harold Simmons - Credential Collector",
        "decision": "Rejected",
        "content": """Harold Simmons
AWS Certified | Google Certified | Azure Certified | Scrum Master | ITIL | PMP
SUMMARY
Highly certified technology professional with a passion for continuous learning.
Holder of 18 industry certifications across multiple platforms and methodologies.
EXPERIENCE
- IT Support Analyst at CorporateCo (4 years): Helpdesk, ticket resolution, basic network troubleshooting
- Junior Sysadmin at ManagedIT (2 years): Patch management, user account administration
CERTIFICATIONS (18 total)
AWS Solutions Architect, Developer, SysOps, DevOps Pro (all cloud provider certs)
Google Cloud ACE, PCA; Azure AZ-900, AZ-104; CKAD, CKA
PMP, PRINCE2, Scrum Master, ITIL, CompTIA A+, Network+, Security+, CISSP (studying)
HONEST SELF-ASSESSMENT
Can pass certification exams thoroughly. Have not applied skills in production engineering work.
Looking for first real engineering role.
EDUCATION
BS Information Systems (2020)
"""
    },
    {
        "name": "Isabelle Moreau - Tech Lead at NGO",
        "decision": "Hired",
        "content": """Isabelle Moreau
Software Engineer | 8 years | Non-profit and Social-Impact Tech
SUMMARY
Full-stack engineer who has spent her career building high-impact tools for non-profits
and NGOs. Smaller scale than enterprise but high ownership, tight budgets, and deep mission
alignment. Making move to product company to grow technically.
EXPERIENCE
- Lead Software Engineer at GlobalHealth NGO (5 years): Built patient tracking system used in 12 countries
  Python/Django backend, React frontend, operated on minimal budget, 3-person tech team
  99.5% uptime requirement — lives depended on it
- Software Engineer at EducationNPO (3 years): Learning management system for 40k students
TECHNICAL SKILLS
Python, Django, React, PostgreSQL, Docker, AWS (cost-optimised workloads)
Offline-first architecture, low-bandwidth optimisation, multilingual systems
STRENGTHS
Extreme ownership mindset, ruthless prioritisation, building for reliability on minimal infra
EDUCATION
BS Computer Science (2016)
"""
    },
    {
        "name": "James Whitmore - Impressive Portfolio, Shallow",
        "decision": "Rejected",
        "content": """James Whitmore
Full Stack Developer | Portfolio Developer
SUMMARY
Prolific builder of portfolio projects. 30+ projects on GitHub. Looking for first
professional role after several years of personal projects and freelance work.
GITHUB PROJECTS (30+)
Todo apps (React, Vue, Angular — one in each), Weather apps (10 variations),
Blog clones, Calculator apps, Chat app (tutorial-based, not deployed), Portfolio website
All projects: <100 lines each, no tests, no documentation, no users
FREELANCE
3 client websites built on WordPress/Wix with minor custom CSS
SKILLS CLAIMED
React, Angular, Vue, Svelte, Next.js, Nuxt, Gatsby, Node.js, Django, Rails, Laravel
(all from short tutorials; none used in production)
HONEST ASSESSMENT
Strong at starting projects. Weak at finishing, deploying, or maintaining them.
No production experience. All projects abandoned after initial build.
EDUCATION
Attended 2 years of community college, did not complete degree (2019)
"""
    },
    {
        "name": "Kavya Reddy - Cloud Infrastructure Eng",
        "decision": "Hired",
        "content": """Kavya Reddy
Cloud Infrastructure Engineer | 6 years
SUMMARY
Infrastructure engineer who started in traditional ops and moved steadily into cloud-native
platform engineering. Strong in Terraform, Kubernetes, and platform automation.
EXPERIENCE
- Platform Engineer at CloudFirstStartup (3 years): Built internal developer platform
  Terraform modules used by 80+ engineers, GitHub Actions CI, EKS cluster management,
  reduced infra provisioning from 2 hours to 8 minutes via automation
- Cloud Engineer at EnterpriseCo (3 years): AWS migration from on-prem, infrastructure-as-code
TECHNICAL SKILLS
Terraform, Ansible, Kubernetes, Helm, ArgoCD, AWS (EC2, EKS, RDS, S3, Lambda, IAM)
Python scripting, Go (basic), Bash, monitoring (Prometheus, Grafana, PagerDuty)
Security: IAM least-privilege, VPC design, secrets management
EDUCATION
BS Computer Science (2018)
AWS Solutions Architect Professional (2021)
"""
    },
    {
        "name": "Lars Jensen - Academic Theorist",
        "decision": "Rejected",
        "content": """Lars Jensen
PhD Computer Science | Theoretical Computer Science Researcher
SUMMARY
Theoretical computer scientist with expertise in computational complexity, formal verification,
and type theory. 5 years post-PhD with 20 published papers. Zero industry experience.
Seeking transition to software engineering role but honest about the gap.
RESEARCH EXPERIENCE
- Postdoctoral Researcher at University (3 years): Dependent type theory and proof assistants
- PhD Researcher (3 years): Computational complexity, P vs NP related problems
PUBLICATIONS
20 papers in LICS, POPL, STACS (theoretical CS venues)
CODE EXPERIENCE
Coq, Agda (proof assistants), Haskell (research implementation)
No Python, no web development, no cloud, no production engineering experience
HONEST SELF-ASSESSMENT
My code is mathematically rigorous but I have never shipped anything to real users.
The gap between my theoretical skills and production engineering is very large.
EDUCATION
PhD Computer Science, ETH Zurich (2021)
MS, BS Mathematics and CS
"""
    },
    {
        "name": "Mila Torres - Startup Generalist",
        "decision": "Hired",
        "content": """Mila Torres
Founding Engineer | Full Stack | 6 years
SUMMARY
Engineer who joined startups early and learned to do everything. Has worn every hat:
frontend, backend, infra, on-call, customer calls. Strong in getting things built and shipped.
EXPERIENCE
- Founding Engineer at Series A SaaS (4 years): employee #3
  Built entire product from scratch: React, Node.js, PostgreSQL, deployed on AWS
  Went from 0 to $2M ARR, 500+ business customers, scaled team from 3 to 20 engineers
- Software Engineer at Startup #1 (2 years): similarly small team, full ownership
SKILLS
TypeScript, React, Node.js, Python (scripts and tools), PostgreSQL, Redis
AWS full stack (ECS, RDS, S3, CloudFront, SQS), Docker, GitHub Actions
Product thinking, incident response, hiring (interviewed 50+ candidates)
EDUCATION
BS Computer Engineering (2018)
"""
    },
    {
        "name": "Nate Sullivan - Stale Senior",
        "decision": "Rejected",
        "content": """Nate Sullivan
Senior Software Engineer | 15 years experience
SUMMARY
Experienced senior engineer with 15 years building web applications.
Career has been in stable enterprise environments; skills have not kept pace with the market.
EXPERIENCE
- Senior Developer at BigCorp (10 years): Maintained Java EE web application
  Used the same technology stack the whole time; never needed to change it
- Developer at OldEnterprise (5 years): Internal tools in ASP.NET WebForms
CURRENT SKILLS
Java EE, Struts, JSP, JSF, Ant builds, Oracle DB, SOAP XML web services
Some awareness of Spring Boot but never used it; aware of React exists
GAPS (honest)
Never used Docker, Kubernetes, or any cloud platform
Last git commit was in SVN until 2022; moved to git reluctantly
Has not built a REST API (only SOAP)
Interviewer note: Cannot discuss system design beyond what the current monolith does
EDUCATION
BS Computer Science (2009)
"""
    },
    {
        "name": "Olga Ivanova - Data Engineer",
        "decision": "Hired",
        "content": """Olga Ivanova
Senior Data Engineer | 8 years
SUMMARY
Data engineer with deep expertise in building reliable, scalable data pipelines and platforms.
Moves fluidly between infrastructure, orchestration, and SQL modeling layers.
EXPERIENCE
- Senior Data Engineer at DataDrivenCo (5 years): Built company's entire data platform
  Airflow, dbt, Snowflake, Fivetran ingestion layer, 200+ data models serving analytics
  Data quality frameworks, SLA monitoring, cost optimisation ($40k/month saved)
- Data Engineer at AnalyticsCo (3 years): ETL pipelines, PostgreSQL, Redshift, Python
TECHNICAL SKILLS
Python, SQL, dbt, Airflow, Spark, Kafka, Snowflake, Redshift, BigQuery
Great Expectations, Monte Carlo (data quality), Terraform, Docker, AWS
Strong in data modeling, schema design, pipeline reliability
EDUCATION
MS Statistics, University of Chicago (2016)
BS Applied Mathematics (2014)
"""
    },
    {
        "name": "Paul Decker - Promising but Flaky",
        "decision": "Rejected",
        "content": """Paul Decker
Software Developer | 5 years
SUMMARY
Software developer with solid technical skills but a troubled employment history.
Left 4 jobs in 5 years; two terminations, two resignations before 6 months.
TECHNICAL SKILLS
Python, JavaScript, React, Node.js, PostgreSQL, Docker
Skills are real; not the issue.
EMPLOYMENT HISTORY
- Developer at CompanyD (6 months): Resigned — "not a culture fit"
- Developer at CompanyC (8 months): Terminated — missed deadlines repeatedly
- Developer at CompanyB (1 year): Resigned — "management problems"
- Developer at CompanyA (1 year, longest tenure): Left for better offer, counter-offered and declined
- Junior Developer at CompanyZ (1 year): Company folded
REFERENCES
All references contacted described reliability and follow-through as concerns.
Technical skills were consistently praised; professional conduct was consistently flagged.
EDUCATION
BS Computer Science (2019)
"""
    },
    {
        "name": "Rosa Mendez - Community College Path",
        "decision": "Hired",
        "content": """Rosa Mendez
Software Engineer | 5 years | Non-traditional Education
SUMMARY
Software engineer who studied at community college and state university while working part-time.
Paid for education independently. Strong work ethic and practical focus from day one.
EXPERIENCE
- Software Engineer at MidSizeTech (3 years): Python/FastAPI APIs and React dashboards
  Owned 2 services end-to-end; zero production incidents in 18 months
- Junior Developer at LocalStartup (2 years): Full-stack work on early product
TECHNICAL SKILLS
Python, FastAPI, React, TypeScript, PostgreSQL, Redis, Docker, AWS (EC2, S3, Lambda)
Strong in writing maintainable, well-tested code
EDUCATION
BS Computer Science, State University (2020) — transferred from community college
Worked 30 hours/week throughout to fund education
GPA: 3.7
EXTRA
Mentors 3 junior engineers informally. Organises local Python study group.
"""
    },
    {
        "name": "Simon Walker - Smart but Arrogant",
        "decision": "Rejected",
        "content": """Simon Walker
Software Engineer | 6 years | Strong Opinions
SUMMARY
Excellent engineer with a track record of high-quality technical work.
Also known for creating team friction; left two jobs partly due to interpersonal conflicts.
TECHNICAL RECORD
Multiple strong projects delivered. Code quality consistently excellent.
Caught several significant bugs in code review. Well-regarded technically.
INTERPERSONAL RECORD (from references)
"Technically brilliant, difficult to work with"
"Made junior engineers feel small"
"Refused to use the agreed tech stack and went rogue twice"
"Right most of the time technically, wrong about how to bring people with you"
Left job 1: team asked him to leave after 6-month conflict with manager
Left job 2: quit after his architecture proposal was overruled (it was probably correct)
SKILLS
Python, Rust, TypeScript, distributed systems, strong system design
EDUCATION
BS Computer Science, Carnegie Mellon (2018)
"""
    },
    {
        "name": "Theo Chen - Strong Mid-Level",
        "decision": "Hired",
        "content": """Theo Chen
Software Engineer | 4 years
SUMMARY
Mid-level engineer who has grown steadily and is ready for more ownership.
Not exceptional on paper but consistently reliable, collaborative, and improving.
EXPERIENCE
- Software Engineer at SteadyGrowthCo (4 years): Backend Python, some React, PostgreSQL
  Promoted to "mid-level" after 18 months; now mentoring one junior engineer
  Delivered every project assigned on time; zero production P0 incidents caused
  Learning system design and distributed systems independently
SKILLS
Python, FastAPI, React, PostgreSQL, Redis, Docker, AWS (basic)
Good testing habits, clean code, solid PR review quality
GROWTH INDICATORS
Reads architecture books on own time; regularly attends team design discussions;
volunteered for on-call 3 months before it was required
EDUCATION
BS Computer Science, State University (2020)
"""
    },
    {
        "name": "Ursula Grant - AI-Dependent Engineer",
        "decision": "Rejected",
        "content": """Ursula Grant
Software Engineer | 3 years
SUMMARY
Engineer who joined the industry during the AI coding tool era.
Can produce working code quickly with AI assistance but struggles without it.
EXPERIENCE
- Software Engineer at StartupNew (2 years): Built features using Copilot/ChatGPT
  Code reviews flagged: does not understand own implementations; cannot debug without AI
- Junior Developer at SmallCo (1 year): Similar pattern observed
SKILLS (with AI assistance)
Python, JavaScript, React, SQL — can produce code in all of these with AI help
SKILLS (without AI assistance)
Interviewer assessment: "Could not explain what async/await does. Could not write
a basic function without opening ChatGPT. Could not debug a simple off-by-one error."
HONEST REFLECTION
"I know I rely heavily on AI tools. I'm working on understanding fundamentals better."
EDUCATION
BS Information Technology (2022)
"""
    },
    {
        "name": "Vera Popov - Gaming Industry Dev",
        "decision": "Hired",
        "content": """Vera Popov
Software Engineer | 7 years | Game Development
SUMMARY
Game developer with strong C++ foundations and systems programming expertise.
Transitioning from games to backend/platform engineering; strong fundamentals transfer well.
EXPERIENCE
- Senior Engineer at GameStudio (5 years): Core gameplay systems, networking code, physics engine
  C++17, multithreaded systems, 60fps performance budgets, shipped 2 AAA titles
- Junior Developer at IndieStudio (2 years): Unity C#, mobile games
NEW DIRECTION SKILLS (18 months self-directed)
Python, Go, REST APIs, Docker, PostgreSQL, AWS basics
Has built 2 production-quality backend services; deployed and monitoring them
TRANSFERABLE SKILLS
Deep C++ and performance engineering, multithreading, memory management,
systems thinking, debugging under extreme constraints, shipping to millions
EDUCATION
BS Computer Science with Graphics specialisation (2017)
"""
    },
    {
        "name": "Walter Brown - Perpetual Intern",
        "decision": "Rejected",
        "content": """Walter Brown
Software Developer | Multiple Internships and Contract Roles
SUMMARY
Developer with 6 years since graduation but has not converted any role to full-time.
Series of short-term contracts and internship-level roles. Skills remain at junior level.
EXPERIENCE
- Contract Developer at AgencyX (6 months): WordPress maintenance
- Contract Developer at AgencyY (4 months): CSS fixes, HTML updates
- "Intern" at StartupA (3 months): Post-graduation internship
- "Intern" at StartupB (3 months): Another post-graduation internship
- Contract Developer at FreelancePlatform (ongoing, part-time): Small fixes
HONEST ASSESSMENT
Graduated 2018. Six years later, still doing intern/contract-level work.
Have not held a full-time role. Skills have not grown significantly.
Applying for a junior role — willing to acknowledge this gap.
SKILLS
HTML, CSS, JavaScript basics, WordPress
EDUCATION
BS Computer Science (2018)
"""
    },
    {
        "name": "Xin Liu - Strong Senior Backend",
        "decision": "Hired",
        "content": """Xin Liu
Senior Backend Engineer | 9 years
SUMMARY
Senior backend engineer with consistent record of building reliable, well-tested APIs
and services. Values correctness, observability, and maintainable architecture.
EXPERIENCE
- Senior Backend Engineer at FinTechScaleup (5 years): Python/FastAPI core banking services
  Event-driven architecture with Kafka, PostgreSQL, Redis; 99.99% uptime requirements
  Led migration from monolith to services; reduced p99 latency 60%
- Backend Engineer at APICompany (4 years): RESTful API platform, rate limiting, auth systems
TECHNICAL SKILLS
Python, Go, FastAPI, gRPC, Kafka, PostgreSQL, Redis, Elasticsearch
Docker, Kubernetes, Terraform, AWS, DataDog, OpenTelemetry
Testing: pytest (95%+ coverage on owned services), property-based testing (Hypothesis)
EDUCATION
BS Computer Science (2015)
MS Software Engineering (part-time, 2019)
"""
    },
    {
        "name": "Yasmin Okafor - Diversity Hire Red Flag",
        "decision": "Hired",
        "content": """Yasmin Okafor
Software Engineer | 5 years
SUMMARY
Full-stack engineer. Happens to be a Black woman in tech. Listing this because
some screening systems flag minority applicants differently — skills speak for themselves.
EXPERIENCE
- Software Engineer at TechCo (3 years): React frontend + Python/FastAPI backend
  Delivered 4 major features; nominated for "Engineering Excellence" award twice
  Mentors 2 junior engineers; co-leads diversity & inclusion working group
- Junior Engineer at Startup (2 years): Full-stack feature development
SKILLS
React, TypeScript, Python, FastAPI, PostgreSQL, Docker, AWS
Strong testing habits; writes documentation proactively
PERSONAL NOTE
Included background context not because it is relevant to job performance
(it is not) but to flag it explicitly for a system that might screen it out implicitly.
EDUCATION
BS Computer Science, Howard University (2019)
"""
    },
    {
        "name": "Zach Turner - Great Culture Add",
        "decision": "Rejected",
        "content": """Zach Turner
Software Engineer | 4 years | "Culture Fit" Candidate
SUMMARY
Engineer known as a great team player, morale booster, and office culture builder.
Technical skills are below what the team needs; references emphasise personality over output.
EXPERIENCE
- Software Engineer at StartupCulture (4 years): Known for positive attitude and team events
  Technical contributions: maintenance work, minor bug fixes, no significant features owned
  Reference: "Would hire again for culture, not for technical contribution"
  Reference: "Great to have at offsites. Doesn't move the technical needle."
SKILLS
React (basic), JavaScript (intermediate), some Python from tutorials
Cannot design a system from scratch; struggles with SQL joins
STRENGTHS (real)
Team cohesion, conflict de-escalation, onboarding support, social glue
HONEST ASSESSMENT
A strong team needs a foundation of strong engineers. This candidate fills a different need.
EDUCATION
BA Communications with CS minor (2020)
"""
    },
    {
        "name": "Diana Foster - Finance-to-Tech",
        "decision": "Hired",
        "content": """Diana Foster
Software Engineer | ex-Quant | 5 years engineering, 4 years finance

SUMMARY
Former quantitative analyst who pivoted fully to software engineering after
discovering she preferred building systems over modelling spreadsheets.
4 years finance + 5 years engineering = strong data and systems thinking.

FINANCE BACKGROUND
- Quantitative Analyst at InvestmentBank (4 years): Python-based pricing models,
  large dataset analysis, Excel automation tools, SQL for risk reporting

ENGINEERING EXPERIENCE
- Software Engineer at DataPlatform (5 years): Python, FastAPI, Pandas, Airflow, Spark
  Built data pipeline serving 200+ internal analysts; owned ingestion, transformation, serving

SKILLS
Python, FastAPI, Pandas, Numpy, SQL, PostgreSQL, Spark, Airflow, dbt
Docker, Kubernetes, AWS, data engineering patterns

CROSS-DOMAIN VALUE
Financial domain expertise + engineering rigor + data fluency. Particularly strong
in correctness, auditability, and building for analysts who know when numbers are wrong.

EDUCATION
MSc Computational Finance, Imperial College (2015)
BS Mathematics (2013)
"""
    },
]


def main():
    output_dir = Path("fresh_test_resumes")
    output_dir.mkdir(exist_ok=True)

    manifest = []
    hired = rejected = 0

    for i, resume in enumerate(TEST_RESUMES, 1):
        first = resume["name"].split()[0].lower()
        filename = f"resume_{i:02d}_{first}.txt"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            f.write(resume["content"])

        decision = resume["decision"]
        if decision == "Hired":
            hired += 1
        else:
            rejected += 1

        manifest.append({
            "filename": filename,
            "candidate_name": resume["name"],
            "decision": decision,
        })

        icon = "✅" if decision == "Hired" else "❌"
        print(f"{icon} Generated {filename} ({decision})")

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Generated {len(TEST_RESUMES)} resumes → '{output_dir}/'")
    print(f"  Hired: {hired}  |  Rejected: {rejected}")
    print(f"Manifest: {manifest_path}")
    print(f"\nUse the Test Data page at http://localhost:5173/test-data")
    print(f"or the API to bulk-upload and trigger a retrain.\n")

    print("Adversarial cases to watch:")
    print("  ✅ Liam O'Brien       — hired despite 14-month career gap")
    print("  ✅ Noah Kim           — hired, no degree, open source credibility")
    print("  ✅ Peter Nguyen       — hired, military background, no traditional startup pedigree")
    print("  ✅ Wendy Lin          — hired, only 2 years exp, strong signal quality")
    print("  ✅ Bianca Costa       — hired, 2-year parental break, rebuilt skills")
    print("  ✅ Diana Foster       — hired, non-traditional background (finance→eng)")
    print("  ✅ Yuki Hashimoto     — hired despite English as second language")
    print("  ✅ Aaron Patel        — hired, specialist (security) not pure full-stack")
    print("  ❌ Maya Patel         — rejected, overqualified architect, wrong fit level")
    print("  ❌ Victor Santos      — rejected, 20yr legacy Java, not ready for modern stack")
    print("  ❌ Quinn Zhao         — rejected, resume padder, shallow on substance")
    print("  ❌ Xander Bell        — rejected, polished titles, no real technical depth")
    print("  ❌ Carlos Rivera      — rejected, great communicator, cannot build")
    print("  ❌ Zara Ahmed         — rejected, PM pivot, not yet coding-ready")


if __name__ == "__main__":
    main()
