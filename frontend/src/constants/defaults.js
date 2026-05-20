/** Default job and core values matching seed_data.py */

export const DEFAULT_JOB_TITLE = 'Senior Full Stack Engineer';

export const DEFAULT_JOB_DESCRIPTION = `We are looking for a Senior Full Stack Engineer to lead the development of our web applications.
You will design scalable backend services using Python/FastAPI and rich, interactive user interfaces in React.
Key responsibilities:
- Lead features from conceptual design to production deployment, taking full ownership.
- Maintain a high standard of technical excellence by writing clean, testable code and participating in reviews.
- Work closely with customer success to address issues and enhance customer obsession.
- Innovate and propose new tools/architectures to improve platform performance.
- Collaborate closely with cross-functional teams to build impactful products.`;

export const DEFAULT_CORE_VALUES = [
  {
    name: 'Technical Excellence',
    description:
      'We strive for robust system architecture, clean and maintainable code, comprehensive automated test coverage, and continuous learning.',
  },
  {
    name: 'Ownership',
    description:
      'We take complete responsibility for outcomes, proactively solve problems without being asked, and follow projects through to delivery.',
  },
  {
    name: 'Collaboration',
    description:
      'We mentor others, share knowledge openly, value diverse perspectives, and work cross-functionally to achieve shared goals.',
  },
  {
    name: 'Innovation',
    description:
      'We continuously experiment, propose novel solutions, automate repetitive work, and seek to improve products and processes.',
  },
  {
    name: 'Customer Obsession',
    description:
      'We align our decisions with user needs, respond quickly to user issues, and focus on delivering direct customer value.',
  },
];

export const DEFAULT_EVALUATION_PROMPTS = [
  `You are evaluating a software engineer applicant for a Senior SWE role.

      Assess their TECHNICAL DEPTH based on the profile below.
      Consider: years of relevant experience, depth in Python and core CS concepts,
      evidence of system-level thinking, and complexity of past projects.

      Score rubric:
      1 = Beginner (<2 years, basic skills only)
      2 = Junior (2-3 years, solid fundamentals)
      3 = Mid-level (3-5 years, works independently)
      4 = Senior (5-8 years, designs systems)
      5 = Principal (8+ years, deep expertise, architects at scale)

      Return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}`,
  `You are evaluating a software engineer applicant for a Senior SWE role.

      Assess their PROBLEM-SOLVING ABILITY based on the profile below.
      Consider: evidence of tackling complex challenges, creative solutions,
      impact delivered, and ability to break down hard problems.

      Score rubric:
      1 = Struggles with complexity, needs extensive guidance
      2 = Can solve defined problems, needs some direction
      3 = Independently solves most problems
      4 = Handles complex, novel problems; finds elegant solutions
      5 = Exceptional: solves cutting-edge problems, mentors others

      Return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}`,
  `You are evaluating a software engineer applicant for a Senior SWE role.

      Assess their alignment with our CULTURE based on the profile below.
      Consider: evidence of collaboration, mentoring others, care for code quality,
      learning from feedback, and alignment with our values of inclusivity and growth.

      Score rubric:
      1 = Appears to work in isolation, dismisses feedback
      2 = Works with others, but limited collaborative impact
      3 = Good team player, contributes positively
      4 = Strong collaborator, mentors junior engineers, advocates for good practices
      5 = Exceptional: role model for culture, builds strong teams, leads by example

      Return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}`,
  `You are evaluating a software engineer applicant for a Senior SWE role.

      Assess their COMMUNICATION SKILLS based on the profile below.
      Consider: clarity of writing in resume/summaries, ability to explain complex topics,
      documentation quality, and evidence of effective knowledge sharing.

      Score rubric:
      1 = Unclear writing, hard to understand intent
      2 = Adequate writing, mostly understandable
      3 = Clear and professional communication
      4 = Excellent communicator, explains complexity clearly, strong writer
      5 = Exceptional: influences through communication, thought leader

      Return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}`,
  `You are evaluating a software engineer applicant for a Senior SWE role.

      Assess their CAREER TRAJECTORY AND GROWTH MINDSET based on the profile below.
      Consider: progression of responsibilities, skill development over time,
      willingness to take on new challenges, and evidence of continuous learning.

      Score rubric:
      1 = Stagnant career, minimal growth
      2 = Modest growth, some new challenges taken on
      3 = Steady growth, clear progression
      4 = Strong trajectory, consistently seeks growth opportunities
      5 = Exceptional: rapid growth, clear vision, takes on stretch goals

      Return ONLY valid JSON: {"score": <integer 1-5>, "rationale": "<2-3 sentences>"}`,
];
