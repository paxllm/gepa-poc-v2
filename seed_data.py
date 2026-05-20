"""
Seed script to populate the database with a sample job, core values, and resumes.
Creates mock text files under data/uploads/ and inserts them into SQLite.

Re-running this script clears existing data and assigns fresh train/val/test splits.
"""

import asyncio
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.constants.default_prompts import DEFAULT_EVALUATION_PROMPTS, SEED_AUTHORED_SET_ID
from backend.core.config import get_settings
from backend.core.database import get_session_factory, init_db
from backend.gepa_integration.dataset_split import assign_splits
from backend.models.db_models import (
    CandidatePrediction,
    CoreValue,
    Evaluation,
    IterationMetrics,
    Job,
    PromptEvolutionLog,
    Resume,
    TalentLens,
)


# Sample Resumes Text Content (25 Hired, 25 Rejected)
RESUMES_DATA = [
    # ─── HIRED (Strong candidates matching JD & values) ─────────
    {
        "candidate_name": "Alice Chen",
        "hiring_label": "Hired",
        "content": """
ALICE CHEN
Senior Software Engineer
Email: alice.chen@email.com | Phone: 555-0192 | GitHub: github.com/alicechen

SUMMARY
Experienced Full Stack Engineer with 7+ years of building scalable web applications. Strong background in React, Python, and cloud architecture (AWS). Proven track record of taking technical ownership and leading small teams to deliver high-impact products.

EXPERIENCE
Lead Engineer | TechCorp (2022 - Present)
- Architected and built a microservices-based SaaS platform using Python (FastAPI) and React, improving page load speeds by 45%.
- Took complete ownership of the migration from legacy infrastructure to AWS ECS, reducing monthly server costs by 30% and setup automated CI/CD pipelines.
- Mentored 4 junior engineers, established code review guidelines, and promoted collaboration across design and product teams.
- Collaborated with product managers to design a real-time analytics dashboard, leading to a 20% increase in customer retention.

Senior Developer | DevSolutions (2019 - 2022)
- Built and maintained customer-facing web applications using React, Node.js, and PostgreSQL.
- Innovated a new caching layer using Redis that reduced database query latency by 60%.
- Consistently achieved 95%+ test coverage by implementing rigorous automated testing (Jest, Cypress).

EDUCATION
B.S. in Computer Science | Stanford University (2015 - 2019)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL, HTML/CSS
Frameworks: FastAPI, React, Next.js, Node.js, Express
DevOps/Cloud: AWS (S3, EC2, ECS, RDS), Docker, Git, CI/CD, Redis, PostgreSQL
"""
    },
    {
        "candidate_name": "Marcus Johnson",
        "hiring_label": "Hired",
        "content": """
MARCUS JOHNSON
Full Stack developer
Email: marcus.j@email.com | Phone: 555-0234 | GitHub: github.com/mjohnson

SUMMARY
Passionate Software Engineer with 6 years of professional experience specializing in modern JavaScript/TypeScript frameworks and backend API design. Driven by technical excellence and customer-centric problem solving.

EXPERIENCE
Senior Software Engineer | CustomerFirst Inc (2021 - Present)
- Designed and implemented a responsive, high-performance checkout flow in React/Next.js, directly improving conversion rate by 15%.
- Spearheaded the adoption of GraphQL, reducing frontend-backend payload sizes by 40%.
- Initiated and led "Innovation Fridays", resulting in 3 new internal tools that automated customer support ticket routing.
- Worked closely with customer success team to identify and resolve critical application bugs, reducing customer escalations by 50%.

Software Engineer | BuildSmart (2020 - 2021)
- Developed robust backend API endpoints using Python, Django, and PostgreSQL.
- Participated in system design discussions and took ownership of the billing module integration with Stripe.
- Collaborated with UX designers to build an accessible component library.

EDUCATION
B.S. in Software Engineering | University of Michigan (2016 - 2020)

SKILLS
Frontend: React, TypeScript, Tailwind CSS, Next.js, Redux, GraphQL
Backend: Python, Django, Node.js, PostgreSQL, MongoDB, REST APIs
Tools & Cloud: Git, Docker, AWS, Stripe API, CI/CD pipelines
"""
    },
    {
        "candidate_name": "Elena Rostova",
        "hiring_label": "Hired",
        "content": """
ELENA ROSTOVA
Senior Full Stack Engineer
Email: elena.rostova@email.com | GitHub: github.com/erostova

SUMMARY
Dynamic and innovative engineer with over 8 years of experience creating highly scalable cloud applications. Expert in Python, React, and serverless architectures. Strong advocate for engineering excellence and collaborative problem-solving.

EXPERIENCE
Staff Engineer | CloudScale Systems (2022 - Present)
- Led the redesign of a high-throughput data processing pipeline using Python, AWS Lambda, and DynamoDB, handling 10M+ daily events.
- Collaborated with product team to deliver a highly requested custom reporting feature, driving $1.2M in expansion ARR.
- Promoted collaboration by organizing cross-functional architecture reviews and mentoring senior and mid-level developers.
- Took ownership of application security, implementing OAuth2/OIDC standards and resolving vulnerability backlogs.

Senior Full Stack Developer | InnovateTech (2018 - 2022)
- Created full-stack features using React, FastAPI, and PostgreSQL.
- Implemented a server-side rendering architecture that improved SEO rating and doubled organic search traffic.
- Authored developer tooling that reduced local setup time from 2 hours to 5 minutes.

EDUCATION
M.S. in Computer Science | Georgia Tech (2016 - 2018)
B.S. in Computer Science | Saint Petersburg State University (2012 - 2016)

SKILLS
Python (FastAPI, Django), JavaScript/TypeScript (React, Node.js), HTML5, CSS3, SQL, NoSQL, AWS (Lambda, DynamoDB, RDS, API Gateway), Docker, CI/CD, Git.
"""
    },
    {
        "candidate_name": "Liam Henderson",
        "hiring_label": "Hired",
        "content": """
LIAM HENDERSON
Senior Full Stack Developer
Email: liam.henderson@email.com | GitHub: github.com/lhenderson

SUMMARY
Creative and results-driven Full Stack Developer with 6+ years of experience specializing in FastAPI, React, and PostgreSQL. Passionate about optimization, clean architecture, and delivering customer value.

EXPERIENCE
Senior Full Stack Developer | ApexTech (2022 - Present)
- Took complete ownership of a greenfield project to build a client-facing web application with FastAPI and React, delivering it ahead of schedule.
- Worked closely with Customer Success to resolve critical user bottlenecks, increasing client retention by 25%.
- Mentored 3 junior developers and set up rigorous code linting/formatting standards to ensure technical excellence.
- Collaborated with Product Managers to design a telemetry system that tracks frontend errors in real time.

Software Engineer | DevFoundry (2020 - 2022)
- Developed scalable backend REST APIs using Python, Django, and PostgreSQL.
- Refactored frontend styling, improving page load speed by 35%.
- Collaborated in a team of 5 developers using Agile methodologies.

EDUCATION
B.S. in Computer Science | University of Washington (2016 - 2020)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL, HTML/CSS
Frameworks: FastAPI, Django, React, Redux, Tailwind CSS
Cloud/Tools: AWS, Docker, Git, CI/CD pipelines, PostgreSQL, Redis
"""
    },
    {
        "candidate_name": "Priya Patel",
        "hiring_label": "Hired",
        "content": """
PRIYA PATEL
Lead Full Stack Engineer
Email: priya.patel@email.com | GitHub: github.com/ppatel

SUMMARY
Dynamic software engineer with 8 years of experience building modern web apps. Proven track record of taking technical ownership and leading small teams to deliver high-quality products.

EXPERIENCE
Lead Developer | InnovateWeb (2021 - Present)
- Designed and implemented a high-performance analytics dashboard using React, Next.js, and FastAPI.
- Automated testing pipelines, raising unit test coverage from 40% to 90% and securing system reliability.
- Collaborated with design and product teams to streamline the user onboarding experience, boosting sign-ups by 20%.
- Conducted training sessions on advanced Python design patterns.

Software Engineer | TechSolutions (2018 - 2021)
- Built Python/Django backend APIs for complex e-commerce platforms.
- Designed a new caching architecture with Redis, reducing query load by 40%.
- Actively mentored onboarding interns and collaborated across teams.

EDUCATION
M.S. in Computer Science | University of Texas (2016 - 2018)
B.S. in Computer Science | Mumbai University (2012 - 2016)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Frameworks: React, Next.js, FastAPI, Django, Express, Node.js
Database/Cloud: PostgreSQL, MongoDB, Redis, AWS, Docker, Git
"""
    },
    {
        "candidate_name": "Carlos Mendez",
        "hiring_label": "Hired",
        "content": """
CARLOS MENDEZ
Senior Software Engineer
Email: carlos.mendez@email.com | GitHub: github.com/cmendez

SUMMARY
Full Stack Engineer with 7 years of professional experience building scalable SaaS products. Expert in Python web frameworks, React, and cloud architectures. Passionate about collaboration and technical excellence.

EXPERIENCE
Senior Software Engineer | SaaSify (2022 - Present)
- Led the redesign of a high-throughput REST API using Python (FastAPI) and PostgreSQL, handling 5M+ daily requests.
- Promoted strong collaboration through pair programming sessions and engineering workshops.
- Championed a customer-first focus by reviewing customer support tickets to directly improve the UI flow.
- Automated deployment to AWS ECS with multi-stage Docker builds.

Full Stack Developer | WebCraft (2019 - 2022)
- Developed frontend dashboards using React, Redux, and Tailwind CSS.
- Handled database schema designs and query optimization in PostgreSQL.
- Collaborated with QA team to establish end-to-end integration tests.

EDUCATION
B.S. in Software Engineering | Arizona State University (2015 - 2019)

SKILLS
Backend: Python, FastAPI, Django, PostgreSQL, MySQL
Frontend: React, Redux, TypeScript, JavaScript, CSS3
DevOps: AWS (ECS, RDS, S3), Docker, CI/CD, Git
"""
    },
    {
        "candidate_name": "Yuki Tanaka",
        "hiring_label": "Hired",
        "content": """
YUKI TANAKA
Senior Full Stack Engineer
Email: yuki.tanaka@email.com | GitHub: github.com/ytanaka

SUMMARY
Performance-driven engineer with 6 years of experience developing responsive and scalable web solutions. Focused on clean code, automated workflows, and collaborating across teams.

EXPERIENCE
Senior Developer | CloudFlow (2022 - Present)
- Architected and built serverless applications using FastAPI, AWS Lambda, and React.
- Automated deployment pipelines (CI/CD) with GitHub Actions, reducing deployment time by 50%.
- Mentored and onboarded 3 new junior engineers, advocating for standard design patterns.
- Resolved high-priority customer scaling issues under tight deadlines.

Software Engineer | NetSystems (2020 - 2022)
- Built and maintained customer portal APIs using Python and Django.
- Optimized database queries, cutting response times by 30%.
- Collaborated with UI designers to build accessible web components.

EDUCATION
B.S. in Computer Science | Kyoto University (2016 - 2020)

SKILLS
Web: React, Next.js, Tailwind CSS, HTML5, JavaScript
Backend: Python, FastAPI, Django, PostgreSQL, Redis
Cloud/Tools: AWS (Lambda, API Gateway, RDS), Docker, Git, GitHub Actions
"""
    },
    {
        "candidate_name": "Chloe Lefebvre",
        "hiring_label": "Hired",
        "content": """
CHLOE LEFEBVRE
Lead Full Stack Engineer
Email: chloe.l@email.com | GitHub: github.com/clefebvre

SUMMARY
Customer-obsessed Lead Developer with 8 years of experience building high-scale web apps. Skilled at guiding teams and taking complete ownership of software projects.

EXPERIENCE
Lead Full Stack Engineer | BizCore (2021 - Present)
- Managed and built features for a critical B2B application using React, FastAPI, and AWS.
- Refactored legacy codebase to modern TypeScript and React hooks, reducing code complexity by 30%.
- Participated in weekly customer feedback sessions to align engineering roadmaps with user needs.
- Formulated testing guidelines to promote robust delivery.

Full Stack Engineer | TechPioneers (2018 - 2021)
- Designed scalable backend microservices using FastAPI, Redis, and PostgreSQL.
- Led cross-functional design sprints to align UI components with brand standards.
- Mentored junior hires during project onboarding phase.

EDUCATION
B.S. in Computer Science | McGill University (2014 - 2018)

SKILLS
Languages: Python, TypeScript, JavaScript, SQL
Frameworks: React, Next.js, FastAPI, Node.js
Tools/Cloud: AWS, Docker, Redis, PostgreSQL, Git, Jenkins
"""
    },
    {
        "candidate_name": "Daniel Kim",
        "hiring_label": "Hired",
        "content": """
DANIEL KIM
Senior Software Developer
Email: daniel.kim@email.com | GitHub: github.com/dkim

SUMMARY
Results-oriented software engineer with 7 years of full stack experience. Passionate about system performance, developer tools, and continuous innovation.

EXPERIENCE
Senior Developer | NexaTech (2022 - Present)
- Developed and scaled high-performance REST APIs in Python (FastAPI) and responsive UIs in React.
- Created an internal testing suite that reduced integration errors by 60%.
- Championed "Ownership Culture" by leading post-mortem analyses and technical designs.
- Automated system diagnostic scripts, saving the team hours in daily operations.

Full Stack Developer | AppForge (2019 - 2022)
- Built and integrated Stripe payment flows, processing $500k+ monthly.
- Developed interactive data visualizations using React and D3.js.
- Partnered with product teams to scope API requirements.

EDUCATION
B.S. in Computer Science | UC Berkeley (2015 - 2019)

SKILLS
Frontend: React, Redux, D3.js, HTML5, CSS3, JavaScript
Backend: Python, FastAPI, Django, PostgreSQL, MySQL
Other: Stripe API, Docker, AWS (S3, EC2, RDS), Git
"""
    },
    {
        "candidate_name": "Amina Diallo",
        "hiring_label": "Hired",
        "content": """
AMINA DIALLO
Senior Full Stack Developer
Email: amina.diallo@email.com | GitHub: github.com/adiallo

SUMMARY
Dedicated Full Stack Engineer with 6 years of experience building web applications. Expert in designing APIs with FastAPI and crafting interfaces with React.

EXPERIENCE
Senior Developer | SyncSpace (2022 - Present)
- Designed a collaborative real-time editor using FastAPI, WebSockets, and React.
- Conducted comprehensive code reviews to maintain high quality and mentor mid-level developers.
- Coordinated with the customer success team to build user-friendly troubleshooting features.
- Refactored authentication layers using OAuth2/JWT.

Full Stack Developer | CoreWeb (2020 - 2022)
- Built web portals using React, Node.js, and MongoDB.
- Handled backend optimization, improving data loading times by 40%.
- Worked closely with frontend developers to consume REST APIs.

EDUCATION
B.S. in Computer Science | University of Maryland (2016 - 2020)

SKILLS
Languages: Python, JavaScript, TypeScript, HTML/CSS
Web Frameworks: FastAPI, React, Node.js, WebSockets
Database/Cloud: PostgreSQL, MongoDB, AWS (EC2, S3), Docker, Git
"""
    },
    {
        "candidate_name": "Thomas Wright",
        "hiring_label": "Hired",
        "content": """
THOMAS WRIGHT
Senior Staff Engineer
Email: thomas.wright@email.com | GitHub: github.com/twright

SUMMARY
Senior Full Stack Engineer with 9 years of experience. Expert in designing robust backend systems with Python and engaging user interfaces in React.

EXPERIENCE
Senior Staff Engineer | ScaleUp Labs (2021 - Present)
- Led the migration of a massive monolith API to FastAPI microservices, improving uptime to 99.9%.
- Mentored and guided a team of 6 engineers on backend design patterns and React component design.
- Collaborated with product leaders to translate customer feedback into technical specifications.
- Proposed and implemented a pipeline optimization saving 30% computing costs.

Senior Developer | CloudBase (2017 - 2021)
- Developed core full stack features using Django, React, and PostgreSQL.
- Initiated and led the optimization of frontend assets, reducing build size by 35%.
- Maintained legacy backend systems and handled database tuning.

EDUCATION
B.S. in Computer Science | University of Illinois (2013 - 2017)

SKILLS
Languages: Python, JavaScript, SQL, Bash
Frameworks: FastAPI, Django, React, Express
Cloud/Ops: AWS, Docker, Kubernetes, CI/CD, PostgreSQL, Git
"""
    },
    {
        "candidate_name": "Sofia Bianchi",
        "hiring_label": "Hired",
        "content": """
SOFIA BIANCHI
Senior Full Stack Engineer
Email: sofia.bianchi@email.com | GitHub: github.com/sbianchi

SUMMARY
Customer-centric Full Stack Developer with 5+ years of experience. Proficient in React, Next.js, FastAPI, and cloud services (AWS).

EXPERIENCE
Senior Software Engineer | UserFocus (2023 - Present)
- Developed new core features using FastAPI and React, boosting user interaction metrics by 18%.
- Actively investigated user issues, introducing new telemetry that cut bug identification times in half.
- Promoted strong developer collaboration by creating a shared component library.
- Managed serverless code deployments using AWS Lambda and Serverless Framework.

Software Engineer | DevElite (2021 - 2023)
- Built backend endpoints in FastAPI and PostgreSQL, and integrated third-party APIs.
- Wrote automated integration tests using pytest and Playwright.
- Supported system designers in architecting the database models.

EDUCATION
B.S. in Computer Science | Politecnico di Milano (2018 - 2021)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Web Frameworks: React, Next.js, FastAPI, Tailwind CSS
Testing/Cloud: pytest, Playwright, AWS (Lambda, S3, RDS), Docker, Git
"""
    },
    {
        "candidate_name": "Alexandre Dupont",
        "hiring_label": "Hired",
        "content": """
ALEXANDRE DUPONT
Senior Full Stack Developer
Email: alexandre.d@email.com | GitHub: github.com/adupont

SUMMARY
Professional developer with 7 years of experience. Passionate about building robust web tools using React and Python (FastAPI/Django) and maintaining backend reliability.

EXPERIENCE
Senior Developer | WebWorks (2022 - Present)
- Authored high-performance REST APIs in Python (FastAPI) and responsive client portals in React.
- Managed containerized application deployments on AWS using Docker and ECS.
- Oversaw technical onboarding of new team members and established clear API documentation.
- Designed system workflows to minimize data retrieval latency by 20%.

Software Developer | CodersInc (2019 - 2022)
- Built features using Python, Django, and React.
- Managed relational database schema upgrades and data migration strategies.
- Collaborated in an agile scrum environment.

EDUCATION
M.S. in Software Engineering | Sorbonne University (2017 - 2019)
B.S. in Computer Science | Sorbonne University (2014 - 2017)

SKILLS
Stack: Python (FastAPI, Django), JavaScript, TypeScript, React
Databases: PostgreSQL, MySQL, SQLite
Cloud: AWS (ECS, RDS, S3), Docker, CI/CD, Git
"""
    },
    {
        "candidate_name": "Zara Al-Farsi",
        "hiring_label": "Hired",
        "content": """
ZARA AL-FARSI
Lead Full Stack Developer
Email: zara.al@email.com | GitHub: github.com/zalfarsi

SUMMARY
Highly collaborative engineer with 8 years of experience. Strong background in React, Python, and scalable backend design. Passionate about mentoring and engineering excellence.

EXPERIENCE
Lead Developer | TechSynergy (2021 - Present)
- Directed development of an internal dashboard built with React and FastAPI, saving 20 hours/week for staff.
- Set up automated testing strategies, achieving 90% code coverage.
- Mentored and trained junior engineers in writing clean, reusable React components.
- Conducted collaborative architecture design meetings with engineering managers.

Senior Developer | CloudGrid (2018 - 2021)
- Developed backend systems with Django and PostgreSQL.
- Led database optimization projects that cut API query response times by 30%.
- Handled API integrations with third-party billing services.

EDUCATION
B.S. in Computer Science | American University of Beirut (2014 - 2018)

SKILLS
Frontend: React, TypeScript, Redux, CSS3, HTML5
Backend: Python, FastAPI, Django, PostgreSQL
Tools/Cloud: AWS, Docker, Git, GitHub Actions, Jest
"""
    },
    {
        "candidate_name": "Viktor Novak",
        "hiring_label": "Hired",
        "content": """
VIKTOR NOVAK
Senior Full Stack Engineer
Email: viktor.novak@email.com | GitHub: github.com/vnovak

SUMMARY
Solution-oriented Full Stack Developer with 6+ years of experience. Skilled in React, Next.js, Python (FastAPI), and DevOps tools. Focus on high-quality code and ownership.

EXPERIENCE
Senior Full Stack Developer | ByteForge (2022 - Present)
- Engineered serverless backend APIs using FastAPI and AWS Lambda.
- Re-architected frontend components in React, reducing load times by 40%.
- Took complete ownership of deployment scripts and CI/CD pipelines.
- Supported customer success teams during high-impact product launches.

Software Engineer | AppGrid (2020 - 2022)
- Developed frontend dashboards using React and Tailwind CSS.
- Wrote robust backend endpoints using Python and Django.
- Optimized database tables and indexes for MySQL.

EDUCATION
B.S. in Computer Science | Charles University (2016 - 2020)

SKILLS
Frameworks: React, Next.js, FastAPI, Django, Tailwind CSS
Languages: Python, JavaScript, TypeScript, SQL
DevOps/Cloud: AWS Lambda, API Gateway, Docker, CI/CD, Git, MySQL
"""
    },
    {
        "candidate_name": "Natalie Brooks",
        "hiring_label": "Hired",
        "content": """
NATALIE BROOKS
Senior Full Stack Engineer
Email: natalie.brooks@email.com | GitHub: github.com/nbrooks

SUMMARY
Platform engineer with 7 years building customer-facing SaaS products. Deep expertise in Python backend services and growing strength in React frontends. Known for reliability engineering and cross-team incident response.

EXPERIENCE
Senior Engineer | HealthTrack SaaS (2022 - Present)
- Built HIPAA-compliant REST APIs with FastAPI and PostgreSQL, serving 200k+ monthly active users.
- Led frontend migration from jQuery to React/TypeScript, improving accessibility scores from 62 to 94.
- Owned on-call rotation and reduced P1 incident MTTR from 4 hours to 45 minutes through runbooks and telemetry.
- Partnered with customer success to ship self-service billing fixes that cut support tickets by 35%.

Software Engineer | MedFlow (2019 - 2022)
- Developed Django microservices and React admin dashboards for clinic scheduling.
- Implemented feature flags and A/B testing infrastructure used by product and growth teams.

EDUCATION
B.S. in Computer Science | Purdue University (2015 - 2019)

SKILLS
Backend: Python, FastAPI, Django, PostgreSQL, Redis, Celery
Frontend: React, TypeScript, Tailwind CSS, Next.js
Cloud/Ops: AWS (ECS, RDS, CloudWatch), Docker, CI/CD, Git
"""
    },
    {
        "candidate_name": "Oscar Ng",
        "hiring_label": "Hired",
        "content": """
OSCAR NG
Senior Full Stack Developer
Email: oscar.ng@email.com | GitHub: github.com/ongdev

SUMMARY
Engineer with 8 years of experience who transitioned from DevOps into full stack product development. Combines infrastructure instincts with strong React and Python application design.

EXPERIENCE
Senior Full Stack Developer | ShipFast (2021 - Present)
- Designed and shipped a multi-tenant analytics product using FastAPI, React, and AWS ECS.
- Built deployment pipelines with GitHub Actions and Terraform, cutting release cycles from weekly to daily.
- Mentored two mid-level engineers on API design, observability, and frontend state management.
- Collaborated with support to reproduce and fix customer-reported edge cases within 24 hours.

DevOps Engineer | CloudNest (2018 - 2021)
- Managed Kubernetes clusters and observability stacks before moving into application development.
- Wrote internal tooling in Python that automated certificate rotation and database failover drills.

EDUCATION
B.S. in Computer Engineering | UC San Diego (2014 - 2018)

SKILLS
Languages: Python, JavaScript, TypeScript, Go, SQL
Frameworks: FastAPI, React, Next.js, Flask
Infrastructure: AWS, Docker, Kubernetes, Terraform, Prometheus, Git
"""
    },
    {
        "candidate_name": "Isabel Santos",
        "hiring_label": "Hired",
        "content": """
ISABEL SANTOS
Staff Full Stack Engineer
Email: isabel.santos@email.com | GitHub: github.com/isantos

SUMMARY
Former startup CTO with 10 years of hands-on engineering experience. Expert at owning ambiguous product areas from zero to production using Python, React, and pragmatic architecture.

EXPERIENCE
Staff Engineer | LedgerPro (2022 - Present)
- Rebuilt a legacy monolith into FastAPI services and a React SPA, enabling 3x faster feature delivery.
- Established engineering standards for testing, code review, and incident retrospectives across 12 engineers.
- Drove customer-obsessed roadmap decisions by synthesizing NPS feedback into quarterly technical bets.
- Introduced event-driven workflows with Redis streams, reducing duplicate billing errors by 90%.

Co-Founder & CTO | PayLoop (2018 - 2022)
- Built MVP and scaled platform to 50k users using Django, React, PostgreSQL, and Stripe integrations.
- Hired and coached a team of 5 engineers while remaining primary contributor to core product code.

EDUCATION
M.S. in Computer Science | Carnegie Mellon University (2016 - 2018)
B.S. in Computer Science | Universidade de Lisboa (2012 - 2016)

SKILLS
Stack: Python (FastAPI, Django), React, TypeScript, PostgreSQL, Redis
Leadership: Technical design, mentoring, roadmap ownership, post-mortems
Cloud: AWS, Docker, CI/CD, Git, Stripe API
"""
    },
    {
        "candidate_name": "Ryan O'Connell",
        "hiring_label": "Hired",
        "content": """
RYAN O'CONNELL
Senior Full Stack Engineer
Email: ryan.oconnell@email.com | GitHub: github.com/roconnell

SUMMARY
Full stack engineer with 6 years of experience, including 3 years building React Native mobile apps before specializing in web platforms with FastAPI and React.

EXPERIENCE
Senior Software Engineer | MobilityHub (2022 - Present)
- Delivered a unified web dashboard in React/Next.js backed by FastAPI services for fleet operators.
- Ported mobile authentication flows to web, improving login success rates by 22%.
- Owned performance tuning across API and frontend, reducing p95 page load from 3.2s to 1.1s.
- Collaborated with design and customer teams to launch accessibility improvements for screen reader users.

Mobile Developer | RideStack (2019 - 2022)
- Built React Native features consumed by 1M+ riders before transitioning to full stack web work.
- Integrated REST APIs and real-time location updates with robust offline handling.

EDUCATION
B.S. in Software Engineering | Trinity College Dublin (2015 - 2019)

SKILLS
Web: React, Next.js, TypeScript, HTML5, CSS3
Backend: Python, FastAPI, Django, PostgreSQL, WebSockets
Mobile (prior): React Native
Tools: AWS, Docker, Git, Jest, Playwright
"""
    },
    {
        "candidate_name": "Maya Chen",
        "hiring_label": "Hired",
        "content": """
MAYA CHEN
Senior Full Stack Developer
Email: maya.chen@email.com | GitHub: github.com/mchen-dev

SUMMARY
Accessibility-focused engineer with 5 years of experience building inclusive web products. Strong in React, Python/FastAPI, and customer-centric delivery.

EXPERIENCE
Senior Developer | AccessFirst (2023 - Present)
- Led WCAG 2.1 AA compliance initiative across React component library and FastAPI admin tools.
- Built customer feedback loops into release process, triaging user-reported UI bugs within one sprint.
- Designed reusable form components adopted by 4 product squads, reducing duplicate frontend code by 40%.
- Automated visual regression tests with Playwright, catching 30+ accessibility regressions pre-release.

Full Stack Developer | EduPortal (2021 - 2023)
- Shipped learning management features using React, FastAPI, and PostgreSQL.
- Mentored interns on API contracts, component testing, and documentation practices.

EDUCATION
B.S. in Computer Science | University of Toronto (2017 - 2021)

SKILLS
Frontend: React, TypeScript, Tailwind CSS, ARIA, axe-core
Backend: Python, FastAPI, PostgreSQL, Redis
Testing: Jest, Playwright, pytest
Cloud/Tools: AWS, Docker, Git, CI/CD
"""
    },
    {
        "candidate_name": "Jonah Klein",
        "hiring_label": "Hired",
        "content": """
JONAH KLEIN
Senior Full Stack Engineer
Email: jonah.klein@email.com | GitHub: github.com/jklein

SUMMARY
Open-source contributor and product engineer with 7 years of experience. Builds developer-friendly APIs in FastAPI and polished React interfaces with a focus on maintainability.

EXPERIENCE
Senior Engineer | DevTools Co (2022 - Present)
- Maintains an open-source FastAPI plugin with 2k+ GitHub stars used in production by 40 companies.
- Built internal developer portal in React that reduced API integration time for partners by 50%.
- Proposed and implemented schema versioning strategy that eliminated breaking changes for external clients.
- Runs weekly knowledge-sharing sessions on system design and testing patterns.

Software Engineer | APIForge (2019 - 2022)
- Developed REST and GraphQL gateways in Python with React-based admin consoles.
- Increased automated test coverage from 55% to 88% across backend and frontend repos.

EDUCATION
B.S. in Computer Science | University of Wisconsin (2015 - 2019)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Frameworks: FastAPI, React, Next.js, GraphQL
Practices: Open source, API design, pytest, Jest, GitHub Actions
Cloud: AWS (Lambda, API Gateway, RDS), Docker
"""
    },
    {
        "candidate_name": "Keisha Washington",
        "hiring_label": "Hired",
        "content": """
KEISHA WASHINGTON
Lead Full Stack Engineer
Email: keisha.washington@email.com | GitHub: github.com/kwashington

SUMMARY
Enterprise SaaS engineer with 9 years of experience designing resilient microservices and modern React applications. Strong track record of ownership in regulated environments.

EXPERIENCE
Lead Engineer | FinSecure (2021 - Present)
- Architected FastAPI microservices handling payment authorization with 99.99% uptime over 18 months.
- Led React frontend rewrite for compliance reporting, reducing manual audit prep time by 60%.
- Coordinated cross-functional launches with legal, support, and sales without missing regulatory deadlines.
- Mentored 5 engineers on secure coding, code review culture, and incident communication.

Senior Developer | BankTech Solutions (2017 - 2021)
- Built Django and React features for commercial banking portals used by 300+ institutions.
- Optimized PostgreSQL queries and caching layers, improving API latency by 45%.

EDUCATION
B.S. in Computer Science | Howard University (2013 - 2017)

SKILLS
Backend: Python, FastAPI, Django, PostgreSQL, Redis, Kafka
Frontend: React, Redux, TypeScript
Security/Compliance: OAuth2, audit logging, SOC2-aware development
Cloud: AWS, Docker, Kubernetes, CI/CD, Git
"""
    },
    {
        "candidate_name": "Hiroshi Yamamoto",
        "hiring_label": "Hired",
        "content": """
HIROSHI YAMAMOTO
Senior Full Stack Engineer
Email: hiroshi.yamamoto@email.com | GitHub: github.com/hyamamoto

SUMMARY
International engineer with 6 years of experience building multilingual SaaS platforms. Proficient in Python/FastAPI backends and React frontends with strong collaboration across distributed teams.

EXPERIENCE
Senior Software Engineer | GlobalReach (2022 - Present)
- Implemented i18n/l10n framework across React app and FastAPI services supporting 12 languages.
- Owned feature delivery for enterprise SSO integrations (SAML, OIDC) requested by top customers.
- Led async design reviews with teams in Tokyo, Berlin, and San Francisco to align API contracts.
- Reduced customer onboarding time by 30% through guided setup flows co-designed with success team.

Software Engineer | NipponCloud (2020 - 2022)
- Developed internal tools and customer dashboards using Django, React, and PostgreSQL.
- Automated deployment checks that prevented 15 production regressions in first year.

EDUCATION
M.S. in Information Science | University of Tokyo (2018 - 2020)
B.S. in Computer Science | Waseda University (2014 - 2018)

SKILLS
Languages: Python, JavaScript, TypeScript, SQL, Japanese, English
Frameworks: FastAPI, React, Next.js, Django
Cloud/Tools: AWS, Docker, Git, GitHub Actions, PostgreSQL
"""
    },
    {
        "candidate_name": "Beatrice Holt",
        "hiring_label": "Hired",
        "content": """
BEATRICE HOLT
Senior Full Stack Developer
Email: beatrice.holt@email.com | GitHub: github.com/bholt

SUMMARY
PhD-trained engineer with 5 years in industry building data-intensive web applications. Combines research rigor with pragmatic full stack delivery in Python and React.

EXPERIENCE
Senior Developer | InsightLab (2023 - Present)
- Built interactive research dashboards in React with FastAPI backends processing 5TB+ monthly datasets.
- Designed experiment tracking UI used by scientists and product managers to evaluate feature impact.
- Introduced statistical guardrails in API validation, reducing bad data uploads by 70%.
- Collaborated with customer research team to translate user interviews into shippable MVP features.

Research Software Engineer | DataScience Corp (2021 - 2023)
- Transitioned from academic research to production engineering, shipping Django/React internal tools.
- Authored documentation and training materials adopted by 3 engineering teams.

EDUCATION
Ph.D. in Computational Science | MIT (2016 - 2021)
B.S. in Mathematics & Computer Science | Yale University (2012 - 2016)

SKILLS
Languages: Python, JavaScript, TypeScript, R, SQL
Frameworks: FastAPI, React, Django, Pandas
Practices: Experiment design, technical writing, pytest, Jest
Cloud: AWS (S3, EC2, RDS), Docker, Git
"""
    },
    {
        "candidate_name": "Finn McCarthy",
        "hiring_label": "Hired",
        "content": """
FINN MCCARTHY
Senior Full Stack Engineer
Email: finn.mccarthy@email.com | GitHub: github.com/fmccarthy

SUMMARY
High-growth engineer who progressed from bootcamp graduate to senior full stack role in 6 years. Deep experience with React, FastAPI, and owning features end-to-end in fast-moving startups.

EXPERIENCE
Senior Engineer | GrowthStack (2023 - Present)
- Owns checkout and subscription flows built with React and FastAPI, processing $2M+ ARR annually.
- Reduced failed payments by 18% through retry logic, observability, and close partnership with support.
- Led migration from SQLite prototype to PostgreSQL with zero downtime using blue-green deployments.
- Mentors junior engineers through structured pairing and weekly architecture discussions.

Full Stack Developer | StartupLaunch (2020 - 2023)
- Second engineering hire; built core product from MVP to 20k users using Django and React.
- Established CI/CD, linting, and code review practices as team scaled from 2 to 10 engineers.

EDUCATION
Full Stack Web Development Bootcamp | General Assembly (2019 - 6 months)
B.A. in Economics | University of Oregon (2013 - 2017)

SKILLS
Stack: Python (FastAPI, Django), React, TypeScript, PostgreSQL, Redis
Practices: Startup ownership, rapid iteration, customer feedback loops
Tools: AWS, Docker, Stripe, Git, GitHub Actions, pytest
"""
    },

    # ─── REJECTED (Unrelated, weak, or misaligned candidates) ────
    {
        "candidate_name": "John Smith",
        "hiring_label": "Rejected",
        "content": """
JOHN SMITH
Junior IT Support Specialist
Email: john.smith@email.com | Phone: 555-0811

SUMMARY
Dedicated IT support specialist with 1 year of experience in helpdesk troubleshooting, hardware maintenance, and network configuration. Eager to transition into a junior software developer role.

EXPERIENCE
Helpdesk Technician | LocalNet Solutions (2024 - Present)
- Provided technical support to 100+ office staff, resolving hardware, software, and network issues.
- Configured local area networks, printers, and user access controls.
- Drafted standard operating procedures for hardware onboarding.
- Created simple HTML/CSS pages for the internal company portal.

IT Intern | TechRetail (2023 - 2024)
- Assisted with OS installations, backups, and virus removal.
- Managed inventory of IT assets.

EDUCATION
Associate Degree in Information Technology | Community College (2021 - 2023)

SKILLS
Windows Server, Active Directory, Basic Networking (TCP/IP), PC Hardware Troubleshooting, Basic HTML/CSS, Microsoft Office.
"""
    },
    {
        "candidate_name": "Sarah Connor",
        "hiring_label": "Rejected",
        "content": """
SARAH CONNOR
Data Entry Clerk / Administrative Assistant
Email: sarah.connor@email.com

SUMMARY
Highly organized administrative professional with 4 years of experience managing office logistics, data entry, and client communication. Looking for entry-level programming opportunities.

EXPERIENCE
Data Entry Specialist | DataSolutions Corp (2022 - Present)
- Inputted 500+ daily customer records into CRM with 99.9% accuracy.
- Managed filing systems and handled confidential documents.
- Answered client phone calls and routed support emails.
- Completed a 12-week online python programming bootcamp.

Administrative Assistant | Alpha Logistics (2020 - 2022)
- Organized weekly team schedules and meeting agendas.
- Handled invoice matching and basic bookkeeping.

EDUCATION
B.A. in Communications | Boston University (2016 - 2020)

SKILLS
Microsoft Excel, Data Entry, Google Workspace, Customer Service, Basic Python (functions, lists, simple scripts).
"""
    },
    {
        "candidate_name": "David Miller",
        "hiring_label": "Rejected",
        "content": """
DAVID MILLER
Technical Writer
Email: david.miller@email.com | Portfolio: davidwrites.com

SUMMARY
Professional Technical Writer with 5 years of experience translating complex software concepts into user-friendly documentation, API guides, and knowledge base articles.

EXPERIENCE
Technical Writer | SaaSify (2021 - Present)
- Authored comprehensive developer documentation and API reference guides for external partners.
- Created step-by-step tutorials, screencasts, and onboarding flows for non-technical users.
- Collaborated with software engineers to review code comments and update documentation.
- Reviewed and edited system design documents for grammatical clarity.

Content Developer | WebAgency (2019 - 2021)
- Wrote blog posts and technical articles about cloud computing trends.
- Maintained company website documentation using Markdown and Hugo.

EDUCATION
B.A. in English | University of Texas (2015 - 2019)

SKILLS
Technical Writing, Markdown, API Documentation (Swagger/OpenAPI), Git, HTML/CSS, basic understanding of JavaScript.
"""
    },
    {
        "candidate_name": "Emily Davis",
        "hiring_label": "Rejected",
        "content": """
EMILY DAVIS
Junior Frontend Developer
Email: emily.davis@email.com | Phone: 555-9012

SUMMARY
Eager and motivated Frontend Developer with 1 year of professional experience building responsive web designs. Passionate about HTML/CSS and basic JavaScript. Seeking a junior role to grow frontend skills.

EXPERIENCE
Junior Frontend Developer | PixelCraft (2025 - Present)
- Developed clean, responsive static websites using HTML5, CSS3, and Bootstrap.
- Assisted senior web designers by translating mockups into web pages.
- Fixed basic styling bugs and improved CSS layout responsiveness.
- Learned foundational React concepts and helped update basic UI components.

EDUCATION
Web Development Bootcamp | Tech Academy (2024 - 12 weeks)

SKILLS
Web Tech: HTML5, CSS3, Bootstrap, JavaScript (ES6), React (basic)
Tools: Git, GitHub, VS Code, Figma (viewing assets)
"""
    },
    {
        "candidate_name": "Rajesh Kumar",
        "hiring_label": "Rejected",
        "content": """
RAJESH KUMAR
Senior Database Administrator (DBA)
Email: rajesh.kumar@email.com | Phone: 555-1033

SUMMARY
Senior Database Administrator with 10 years of experience managing, securing, and optimizing complex database environments. Deep expertise in SQL, PostgreSQL, and Oracle systems.

EXPERIENCE
Lead DBA | DataFortress (2020 - Present)
- Supervised database installations, upgrades, and configuration changes across 50+ enterprise servers.
- Optimized query engine performance and resolved indexing latency, resulting in a 40% reduction in query times.
- Managed complete disaster recovery protocols, daily backups, and security patch application.
- Wrote robust Bash and Python automation scripts for routine system maintenance tasks.

Senior Database Engineer | InfoTech (2016 - 2020)
- Designed schema configurations and executed database migrations.
- Monitored cluster health and performed capacity planning.

EDUCATION
B.S. in Information Technology | Delhi University (2012 - 2016)

SKILLS
Database: PostgreSQL, Oracle DB, SQL Server, MySQL, SQLite
Languages: SQL, PL/pgSQL, Bash, Python (scripting)
Systems: Linux (RHEL, Ubuntu), Docker, Backup & Recovery, Performance Tuning
"""
    },
    {
        "candidate_name": "James Wilson",
        "hiring_label": "Rejected",
        "content": """
JAMES WILSON
IT Product Manager
Email: james.wilson@email.com | Phone: 555-2201

SUMMARY
Dedicated Product Manager with 5 years of experience leading cross-functional teams to deliver SaaS solutions. Expert in agile methodologies, backlog management, and gathering business requirements.

EXPERIENCE
Product Manager | ApexSaaS (2023 - Present)
- Defined product vision, wrote detailed user stories, and managed product feature backlogs.
- Coordinated with development teams during bi-weekly sprint planning and retrospectives.
- Interviewed customers and stakeholders to extract business requirements, leading to 3 new integrations.
- Analyzed web analytics to understand user behavior and increase product activation rates.

Product Owner | CloudScale (2021 - 2023)
- Maintained feature lists, prioritized development sprints, and conducted product demonstrations.
- Collaborated with UI designers on wireframe iterations.

EDUCATION
B.A. in Business Administration | Boston College (2017 - 2021)

SKILLS
Product: Product Strategy, Roadmap Planning, Scrum, Agile, Backlog Grooming
Tools: Jira, Confluence, Trello, Google Analytics, Figma
"""
    },
    {
        "candidate_name": "Jessica Taylor",
        "hiring_label": "Rejected",
        "content": """
JESSICA TAYLOR
QA Automation Engineer
Email: jessica.taylor@email.com | Phone: 555-3392

SUMMARY
Detail-oriented QA Automation Engineer with 4 years of experience testing complex web apps. Expert in automation scripting with Python, Selenium, and Cypress.

EXPERIENCE
QA Automation Engineer | TestLabs (2022 - Present)
- Developed and maintained automated testing suites using Python, Selenium, and PyTest.
- Wrote end-to-end frontend tests in Cypress, reducing manual testing effort by 70%.
- Documented detailed bug reports in Jira and tracked defects through resolution.
- Integrated automated tests into CI/CD pipelines to block buggy releases.

QA Tester | QualityTech (2020 - 2022)
- Performed regression testing, sanity testing, and exploratory testing on mobile apps.
- Created test cases and checklists from product requirements.

EDUCATION
B.S. in Computer Science | Ohio State University (2016 - 2020)

SKILLS
QA Testing: Selenium, Cypress, PyTest, Automated Scripting, Regression Testing
Languages: Python, JavaScript, SQL
Tools: Git, Jenkins, Jira, Postman
"""
    },
    {
        "candidate_name": "Lucas Meyer",
        "hiring_label": "Rejected",
        "content": """
LUCAS MEYER
Junior Python Developer
Email: lucas.meyer@email.com | Phone: 555-4491

SUMMARY
Enthusiastic Junior Developer with 1 year of professional experience. Proficient in basic Python coding and interested in learning full stack web development under engineering mentorship.

EXPERIENCE
Junior Software Developer | CodeStarter (2025 - Present)
- Wrote basic Python scripts to automate internal data cleaning and file sorting tasks.
- Assisted backend developers by writing simple API endpoints using FastAPI.
- Fixed basic spelling and logging issues in backend codebase.
- Participated in team code reviews to learn engineering standards.

EDUCATION
B.S. in Computer Science | Munich Technical University (2021 - 2025)

SKILLS
Languages: Python, SQL (basic), HTML/CSS
Frameworks: FastAPI (basic)
Tools: Git, GitHub, VS Code
"""
    },
    {
        "candidate_name": "Grace Adams",
        "hiring_label": "Rejected",
        "content": """
GRACE ADAMS
Graphic Designer
Email: grace.adams@email.com | Portfolio: graceadams.design

SUMMARY
Creative Graphic Designer with 3 years of experience specializing in digital illustration, landing page design, and branding assets. Proficient in Figma and Adobe Suite.

EXPERIENCE
Graphic Designer | CreativeStudio (2023 - Present)
- Designed branding assets, digital marketing ads, and logos for diverse corporate clients.
- Authored interactive website layouts and prototypes in Figma.
- Worked alongside front-end developers to ensure correct visual implementation.
- Managed typography and style guides for internal product lines.

Design Intern | BrandAgency (2022 - 2023)
- Created layout designs for email newsletters and social media assets.
- Assisted with photo editing and retouching tasks.

EDUCATION
B.F.A. in Graphic Design | Rhode Island School of Design (2019 - 2023)

SKILLS
Design: UI Layouts, Typography, Branding, Color Theory, Illustration
Tools: Figma, Adobe Photoshop, Illustrator, InDesign, basic HTML/CSS
"""
    },
    {
        "candidate_name": "Oliver Schmidt",
        "hiring_label": "Rejected",
        "content": """
OLIVER SCHMIDT
System Administrator
Email: oliver.schmidt@email.com | Phone: 555-5521

SUMMARY
Experienced System Administrator with 8 years of background in Linux infrastructure management, network configuration, and security maintenance. Expert in server scripting and virtualization.

EXPERIENCE
System Administrator | NetOps Corp (2021 - Present)
- Managed and maintained 100+ Linux (Ubuntu/RHEL) servers and local office network firewalls.
- Configured and optimized active directory, DHCP, DNS, and SSH server access rules.
- Wrote Bash and Python shell scripts to automate system health checks and backup processes.
- Monitored server CPU and memory usage, resolving resource issues proactively.

IT Specialist | ServerPro (2018 - 2021)
- Responded to hardware failures, swapped disks, and set up RAID controllers.
- Installed virtual machine servers using VMware.

EDUCATION
B.S. in Computer Engineering | Berlin Institute of Technology (2014 - 2018)

SKILLS
OS: Linux (Ubuntu, Debian, RedHat), Windows Server
Networking: TCP/IP, DNS, DHCP, Firewalls, VPN
Automation: Bash Scripting, Python Scripting, Ansibe, VMware
"""
    },
    {
        "candidate_name": "Fatima Zahra",
        "hiring_label": "Rejected",
        "content": """
FATIMA ZAHRA
Agile Project Manager
Email: fatima.zahra@email.com | Phone: 555-6671

SUMMARY
Certified Scrum Master and Project Manager with 6 years of experience. Skilled in project scoping, resource allocation, and tracking development velocity.

EXPERIENCE
IT Project Manager | TechDelivery (2023 - Present)
- Facilitated daily standup meetings, sprint planning sessions, and retrospectives for 3 development teams.
- Coordinated release timelines and tracked project delivery metrics (velocity, burn-down charts).
- Managed project budgets and reported progress reports to executive leadership.
- Resolved scheduling conflicts and resource bottlenecks to maintain timeline integrity.

Scrum Master | DevSpeed (2020 - 2023)
- Mentored teams on Agile principles and resolved operational roadblocks.
- Maintained project tasks in Jira.

EDUCATION
B.A. in Project Management | University of Cairo (2016 - 2020)

SKILLS
Methodologies: Agile, Scrum, Kanban, Project Scoping, Budgeting
Tools: Jira, Confluence, Microsoft Project, MS Excel
"""
    },
    {
        "candidate_name": "Igor Petrov",
        "hiring_label": "Rejected",
        "content": """
IGOR PETROV
Senior Frontend Developer
Email: igor.petrov@email.com | GitHub: github.com/ipetrov

SUMMARY
Frontend engineer with 6 years of experience building React interfaces. Dedicated strictly to frontend UI development; do not work with backend code, databases, or cloud infrastructure.

EXPERIENCE
Senior Frontend Developer | ReactOnly (2022 - Present)
- Developed complex React frontend dashboards and component styling.
- Handled styling sheets and state management. Refuse to take on database design, backend services, or cloud dev as they are outside my specialization.
- Implemented responsive design across modern browsers.
- Wrote unit tests for components using Jest and React Testing Library.

Frontend Developer | WebFront (2020 - 2022)
- Built interactive dashboard pages using React, HTML, and CSS.
- Optimized web applications for maximum load speed.

EDUCATION
B.S. in Computer Science | Novosibirsk State University (2016 - 2020)

SKILLS
Frontend: React, Redux, HTML5, CSS3, JavaScript, TypeScript, Tailwind CSS
Testing: Jest, Enzyme, React Testing Library
Excluded Areas: No backend, No SQL/databases, No Python/FastAPI, No AWS/DevOps
"""
    },
    {
        "candidate_name": "Emma Wilson",
        "hiring_label": "Rejected",
        "content": """
EMMA WILSON
HR Specialist
Email: emma.wilson@email.com | Phone: 555-7782

SUMMARY
HR Specialist with 4 years of experience managing recruiting pipelines, candidate sourcing, and employee relations for rapid-growth tech firms.

EXPERIENCE
HR Specialist | TalentPeople (2022 - Present)
- Directed recruitment pipelines, sourced software developer candidates, and conducted screen calls.
- Designed onboarding guidelines to improve developer ramp-up time.
- Conducted employee exit interviews and maintained employee records.
- Led company culture committees and team building events.

HR Assistant | StaffSearch (2020 - 2022)
- Maintained HR databases and candidate tracking systems.
- Managed interview scheduling and correspondence.

EDUCATION
B.A. in Psychology | Penn State University (2016 - 2020)

SKILLS
HR: Sourcing, Candidate Screening, Onboarding, Employee Relations, Event Planning
Tools: ATS systems (Lever, Greenhouse), HRIS, MS Office
"""
    },
    {
        "candidate_name": "Ravi Sharma",
        "hiring_label": "Rejected",
        "content": """
RAVI SHARMA
Technical Sales Engineer
Email: ravi.sharma@email.com | Phone: 555-8891

SUMMARY
Sales Engineer with 5 years of experience delivering product demos, answering technical RFPs, and explaining system architecture to enterprise clients.

EXPERIENCE
Sales Engineer | CloudSolutions (2023 - Present)
- Collaborated with account executives to present technical presentations to prospects.
- Built proof-of-concept demos using existing software components without writing custom code.
- Responded to technical RFP security questionnaires and compliance inquiries.
- Gathered client feedback to suggest features for the core engineering team.

Solutions Engineer | SaaSPro (2021 - 2023)
- Answered customer queries and explained API integration options.
- Demonstrated product features at industry tradeshows.

EDUCATION
B.S. in Electrical Engineering | Mumbai University (2016 - 2020)

SKILLS
Sales: Product Demonstrations, Technical Consulting, RFP Responses, Customer Relations
Tech: General understanding of APIs, Cloud Systems, Security Compliance
"""
    },
    {
        "candidate_name": "Sophie Dubois",
        "hiring_label": "Rejected",
        "content": """
SOPHIE DUBOIS
Freelance Web Developer
Email: sophie.dubois@email.com | Portfolio: sophiedubois.com

SUMMARY
Solo Web Developer with 7 years of experience building freelance websites. Prefer to work completely independently; do not participate in code reviews, team planning, or joint coding sessions.

EXPERIENCE
Independent Freelancer | Self-Employed (2021 - Present)
- Delivered websites for small business clients. Prefer working in isolation without external input. Dislike processes like pull requests, Scrum standups, or collaborative developer meetings.
- Created custom landing pages using WordPress, PHP, and basic React components.
- Configured hosting and managed client billing databases.

Web Developer | SoloDesigns (2019 - 2021)
- Developed HTML/CSS websites and templates for local shops.
- Handled client communication and project planning.

EDUCATION
B.S. in Computer Science | Brussels University (2015 - 2019)

SKILLS
Web: PHP, WordPress, HTML5, CSS3, JavaScript, basic Python
Databases: MySQL
Preferences: Strictly Solo Work (No Scrum, No Code Reviews, No Peer Programming)
"""
    },
    {
        "candidate_name": "Michael Chang",
        "hiring_label": "Rejected",
        "content": """
MICHAEL CHANG
Senior Backend Python Engineer
Email: michael.chang@email.com | GitHub: github.com/mchang

SUMMARY
Backend specialist with 8 years of experience building high-scale Python services. Strong in FastAPI, Django, and PostgreSQL but no professional frontend development experience.

EXPERIENCE
Senior Backend Engineer | DataPipe (2021 - Present)
- Designed FastAPI services processing 20M events/day with Kafka and PostgreSQL.
- Optimized database indexing and query plans, cutting p99 latency by 50%.
- Built internal CLI tools and REST APIs; all user interfaces handled by separate frontend team.
- Led backend guild meetings on service reliability and observability.

Backend Developer | ServerLogic (2018 - 2021)
- Maintained Django monolith and migrated critical modules to microservices.
- Wrote extensive pytest suites but never contributed to React or JavaScript codebases.

EDUCATION
B.S. in Computer Science | UCLA (2014 - 2018)

SKILLS
Backend: Python, FastAPI, Django, PostgreSQL, Redis, Kafka
Excluded: No React, No TypeScript, No HTML/CSS beyond basic templates
Cloud: AWS, Docker, CI/CD, Git
"""
    },
    {
        "candidate_name": "Linda Park",
        "hiring_label": "Rejected",
        "content": """
LINDA PARK
Senior Java Developer
Email: linda.park@email.com | Phone: 555-9018

SUMMARY
Enterprise Java engineer with 9 years of experience in Spring Boot, Hibernate, and Angular. Seeking to move into Python/React stack but has not shipped production code in either.

EXPERIENCE
Senior Java Developer | EnterpriseCore (2020 - Present)
- Built microservices with Spring Boot and deployed to on-prem Kubernetes clusters.
- Developed Angular admin panels for internal operations teams.
- Completed online courses in Python and React but no workplace projects using FastAPI or React.
- Participated in architecture reviews focused on JVM performance tuning.

Software Engineer | FinServe (2017 - 2020)
- Maintained legacy Java EE applications and Oracle databases.
- Wrote unit tests with JUnit and integration tests with TestContainers.

EDUCATION
B.S. in Computer Science | Seoul National University (2013 - 2017)

SKILLS
Primary: Java, Spring Boot, Angular, Oracle DB, Maven
Learning (non-production): Python basics, React tutorials
No production experience: FastAPI, PostgreSQL in Python stack
"""
    },
    {
        "candidate_name": "Kevin Zhang",
        "hiring_label": "Rejected",
        "content": """
KEVIN ZHANG
PHP / WordPress Developer
Email: kevin.zhang@email.com | Portfolio: kevinzhang.dev

SUMMARY
Web developer with 12 years of experience building WordPress sites, WooCommerce stores, and PHP backends. Limited exposure to modern Python APIs or React SPAs.

EXPERIENCE
Lead WordPress Developer | SiteCraft Agency (2019 - Present)
- Delivered 80+ client websites using WordPress, PHP, MySQL, and jQuery.
- Customized WooCommerce plugins and managed shared hosting deployments.
- Built landing pages with Elementor; occasional vanilla JavaScript for form validation.
- No experience with FastAPI, Docker-based deployments, or component-driven React apps.

Web Developer | LocalMedia (2014 - 2019)
- Maintained PHP CMS templates and MySQL databases for regional news sites.
- Integrated third-party ad scripts and analytics tags.

EDUCATION
B.S. in Information Systems | San Jose State University (2010 - 2014)

SKILLS
Web: PHP, WordPress, WooCommerce, HTML, CSS, jQuery, MySQL
Missing for role: Python, FastAPI, React, TypeScript, AWS, automated testing at scale
"""
    },
    {
        "candidate_name": "Monica Reyes",
        "hiring_label": "Rejected",
        "content": """
MONICA REYES
UX Researcher
Email: monica.reyes@email.com | Portfolio: monicareyes.com

SUMMARY
User experience researcher with 5 years conducting interviews, usability studies, and journey mapping for digital products. Some familiarity with Figma and HTML but not a software engineer.

EXPERIENCE
Senior UX Researcher | ProductInsight (2022 - Present)
- Planned and ran 60+ user research sessions for mobile and web products.
- Synthesized findings into personas, journey maps, and recommendations for design teams.
- Collaborated with engineers on feasibility but did not write production application code.
- Completed a part-time JavaScript course to better understand developer constraints.

UX Research Associate | DesignLab (2020 - 2022)
- Created research plans, moderated tests, and presented insights to stakeholders.
- Used Dovetail and Miro for analysis; basic HTML/CSS for prototype review only.

EDUCATION
M.A. in Human-Computer Interaction | Georgia Tech (2018 - 2020)
B.A. in Psychology | UC Davis (2014 - 2018)

SKILLS
Research: Interviews, usability testing, surveys, affinity mapping
Tools: Figma (review), Miro, Dovetail, Google Analytics
Not applicable: FastAPI, React production development, system design, DevOps
"""
    },
    {
        "candidate_name": "Brandon Lee",
        "hiring_label": "Rejected",
        "content": """
BRANDON LEE
Recent Computer Science Graduate
Email: brandon.lee@email.com | GitHub: github.com/blee-student

SUMMARY
New graduate with one 10-week software engineering internship. Academic projects in Java and basic web development; not yet qualified for a senior full stack ownership role.

EXPERIENCE
Software Engineering Intern | RetailTech (Summer 2025)
- Assisted team with bug fixes in internal Java Spring application.
- Wrote unit tests under supervision; no independent feature ownership.
- Attended standups and code reviews as observer.

Teaching Assistant | University CS Department (2024 - 2025)
- Graded introductory programming assignments in Python.
- Held office hours for data structures course.

EDUCATION
B.S. in Computer Science | UC Irvine (2021 - 2025)
Relevant coursework: Algorithms, Databases, Web Development (intro)

SKILLS
Academic: Python, Java, SQL, basic HTML/CSS, Git
Projects: Todo app (Flask), course registration CLI (Java)
Gap vs role: No React production experience, no FastAPI at scale, <1 year industry experience
"""
    },
    {
        "candidate_name": "Hannah Kowalski",
        "hiring_label": "Rejected",
        "content": """
HANNAH KOWALSKI
Machine Learning Engineer
Email: hannah.kowalski@email.com | GitHub: github.com/hkowalski

SUMMARY
ML engineer with 6 years of experience training and deploying models in Python. Strong in PyTorch and MLOps but minimal experience building customer-facing web applications.

EXPERIENCE
Senior ML Engineer | VisionAI (2022 - Present)
- Trained computer vision models and deployed them via batch inference pipelines on AWS SageMaker.
- Built internal Jupyter-based evaluation notebooks and Airflow DAGs for retraining.
- Exposed model predictions through a thin Flask wrapper maintained by a separate platform team.
- No ownership of React frontends, user authentication flows, or full product features.

ML Engineer | AdPredict (2019 - 2022)
- Developed ranking models and feature stores using Spark and Python.
- Collaborated with data scientists; limited web development beyond API consumption.

EDUCATION
M.S. in Machine Learning | University of Warsaw (2017 - 2019)
B.S. in Mathematics | University of Warsaw (2014 - 2017)

SKILLS
ML: PyTorch, scikit-learn, Spark, feature engineering, model deployment
Python: NumPy, Pandas, Flask (minimal), Airflow
Not demonstrated: React, FastAPI product APIs, PostgreSQL application design, full stack ownership
"""
    },
    {
        "candidate_name": "Tyler Brooks",
        "hiring_label": "Rejected",
        "content": """
TYLER BROOKS
Contract Software Developer
Email: tyler.brooks@email.com | Phone: 555-3344

SUMMARY
Contract developer with 4 years of experience across 9 short-term engagements (average 5 months each). Some exposure to React and Python but inconsistent depth and limited evidence of ownership or collaboration.

EXPERIENCE
Contract Developer | Various Clients (2022 - Present)
- 6-month React dashboard contract: implemented UI tickets from mockups without backend involvement.
- 4-month Python script contract: wrote ETL utilities; no web framework experience on project.
- 3-month WordPress migration contract: PHP and plugin configuration only.
- Frequently changed projects before participating in long-term architecture or mentoring efforts.

Junior Developer | WebAgency (2021 - 2022)
- Maintained client sites; left after 8 months for higher-paying contract work.

EDUCATION
Associate Degree in Web Development | Online College (2019 - 2021)

SKILLS
Exposure: React (ticket work), Python (scripts), PHP, WordPress, basic SQL
Concerns: Job hopping, no sustained FastAPI/React product ownership, limited testing or DevOps
"""
    },
    {
        "candidate_name": "Nadia Hassan",
        "hiring_label": "Rejected",
        "content": """
NADIA HASSAN
Senior Go Backend Engineer
Email: nadia.hassan@email.com | GitHub: github.com/nhassan

SUMMARY
Backend engineer with 7 years of experience in Go, gRPC, and Kubernetes. Deep infrastructure skills but no professional React or Python/FastAPI development.

EXPERIENCE
Senior Backend Engineer | StreamServe (2021 - Present)
- Built high-throughput microservices in Go with gRPC and PostgreSQL.
- Managed Kubernetes deployments and service mesh configuration for 40+ services.
- Frontend team consumes APIs; candidate has not written React components or Python web apps.
- Strong on performance profiling and distributed systems, weak on full stack product delivery.

Backend Developer | CloudNet (2018 - 2021)
- Maintained Go APIs and Redis caching layers for ad-tech platform.
- Wrote Bash automation; no Django, FastAPI, or JavaScript framework experience.

EDUCATION
B.S. in Computer Engineering | Cairo University (2014 - 2018)

SKILLS
Primary: Go, gRPC, Kubernetes, PostgreSQL, Redis, Prometheus
Missing: Python (FastAPI/Django), React, TypeScript, customer-facing UI development
"""
    },
    {
        "candidate_name": "Curtis Allen",
        "hiring_label": "Rejected",
        "content": """
CURTIS ALLEN
Senior .NET Full Stack Developer
Email: curtis.allen@email.com | Phone: 555-4455

SUMMARY
Full stack developer with 10 years of experience in C#, ASP.NET Core, and Blazor. Solid engineering background but stack does not match Python/FastAPI and React requirements.

EXPERIENCE
Senior .NET Developer | GovSystems (2020 - Present)
- Built internal portals with ASP.NET Core Web API and Blazor Server frontends.
- Managed SQL Server schemas and Entity Framework migrations.
- Deployed to Azure App Service with Azure DevOps pipelines.
- Evaluated Python microservices for a pilot but did not lead implementation; no React production work.

Software Developer | InsureTech (2016 - 2020)
- Maintained WCF services and MVC applications for insurance workflows.
- Mentored junior .NET developers on C# best practices.

EDUCATION
B.S. in Computer Science | Virginia Tech (2012 - 2016)

SKILLS
Stack: C#, ASP.NET Core, Blazor, SQL Server, Azure
Not aligned: Python, FastAPI, React, AWS-centric workflows described in job posting
"""
    },
    {
        "candidate_name": "Patricia O'Brien",
        "hiring_label": "Rejected",
        "content": """
PATRICIA O'BRIEN
Manual QA Tester
Email: patricia.obrien@email.com | Phone: 555-5566

SUMMARY
Quality assurance professional with 5 years of manual testing experience for web and mobile applications. Familiar with bug tracking tools but no software development or automation engineering background.

EXPERIENCE
QA Tester | AppWorks (2022 - Present)
- Executed manual test cases for e-commerce web and iOS applications.
- Logged defects in Jira with detailed reproduction steps and screenshots.
- Participated in sprint demos; did not write application code or automated test scripts.
- Attended introductory Selenium workshop but did not implement automation in role.

QA Associate | SoftTest (2020 - 2022)
- Performed regression, smoke, and exploratory testing on release candidates.
- Maintained test case spreadsheets and sign-off documentation.

EDUCATION
B.A. in Business Information Systems | Arizona State University (2016 - 2020)

SKILLS
QA: Manual testing, test case design, regression testing, Jira, TestRail
Limited: Selenium (workshop only), basic SQL queries for test data
Not applicable: Python/FastAPI development, React, system architecture, production coding
"""
    }
]


async def seed():
    settings = get_settings()
    upload_dir = settings.upload_path
    db_file = settings.data_dir / "resume_gepa.db"

    print("Cleaning up old database and uploads...")
    # Delete database file if exists to allow fresh seed (will be caught and handled if locked)
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"Deleted database file: {db_file}")
        except Exception as e:
            print(f"Warning: Could not delete database file: {e}. Clearing tables via SQL instead.")

    # Clean uploads directory
    if upload_dir.exists():
        for f in upload_dir.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete upload file {f}: {e}")
    else:
        upload_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing database...")
    await init_db()

    factory = get_session_factory()

    async with factory() as session:
        # Explicitly delete all records in tables to bypass SQLite process locks
        print("Wiping all existing table records...")
        await session.execute(delete(CandidatePrediction))
        await session.execute(delete(Evaluation))
        await session.execute(delete(PromptEvolutionLog))
        await session.execute(delete(IterationMetrics))
        await session.execute(delete(TalentLens))
        await session.execute(delete(CoreValue))
        await session.execute(delete(Resume))
        await session.execute(delete(Job))
        await session.commit()

        print("Seeding job: Senior Full Stack Engineer")
        job = Job(
            title="Senior Full Stack Engineer",
            description="""
We are looking for a Senior Full Stack Engineer to lead the development of our web applications. 
You will design scalable backend services using Python/FastAPI and rich, interactive user interfaces in React.
Key responsibilities:
- Lead features from conceptual design to production deployment, taking full ownership.
- Maintain a high standard of technical excellence by writing clean, testable code and participating in reviews.
- Work closely with customer success to address issues and enhance customer obsession.
- Innovate and propose new tools/architectures to improve platform performance.
- Collaborate closely with cross-functional teams to build impactful products.
"""
        )
        session.add(job)
        await session.flush()

        print("Seeding core values...")
        core_values = [
            CoreValue(
                job_id=job.id,
                name="Technical Excellence",
                description="We strive for robust system architecture, clean and maintainable code, comprehensive automated test coverage, and continuous learning."
            ),
            CoreValue(
                job_id=job.id,
                name="Ownership",
                description="We take complete responsibility for outcomes, proactively solve problems without being asked, and follow projects through to delivery."
            ),
            CoreValue(
                job_id=job.id,
                name="Collaboration",
                description="We mentor others, share knowledge openly, value diverse perspectives, and work cross-functionally to achieve shared goals."
            ),
            CoreValue(
                job_id=job.id,
                name="Innovation",
                description="We continuously experiment, propose novel solutions, automate repetitive work, and seek to improve products and processes."
            ),
            CoreValue(
                job_id=job.id,
                name="Customer Obsession",
                description="We align our decisions with user needs, respond quickly to user issues, and focus on delivering direct customer value."
            ),
        ]
        session.add_all(core_values)

        print("Seeding evaluation prompts...")
        for idx, lens_text in enumerate(DEFAULT_EVALUATION_PROMPTS, start=1):
            session.add(
                TalentLens(
                    job_id=job.id,
                    candidate_set_id=SEED_AUTHORED_SET_ID,
                    prompt_index=idx,
                    prompt_text=lens_text,
                    iteration=0,
                    generation="seed",
                    is_active=False,
                )
            )

        print("Seeding resumes...")
        for r_data in RESUMES_DATA:
            candidate_name = r_data["candidate_name"]
            hiring_label = r_data["hiring_label"]
            content = r_data["content"].strip()

            # Create file
            filename = f"{candidate_name.replace(' ', '_').lower()}.txt"
            file_path = upload_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            resume = Resume(
                job_id=job.id,
                candidate_name=candidate_name,
                file_path=str(file_path),
                file_type="txt",
                parsed_text=content,
                hiring_label=hiring_label,
            )
            session.add(resume)

        await session.commit()

        print("Assigning train/val/test splits...")
        split_summary = await assign_splits(session, job.id, force_resplit=True)
        print(
            f"Splits: {split_summary['train']} train / "
            f"{split_summary['val']} val / {split_summary['test']} test"
        )
        print(f"Successfully seeded all data! (Total: {len(RESUMES_DATA)} resumes)")


if __name__ == "__main__":
    asyncio.run(seed())
