/** Default job, core values, and evaluation angles — matches backend/constants/default_prompts.py */

export const DEFAULT_JOB_TITLE = 'Senior Full Stack Engineer';

export const DEFAULT_JOB_DESCRIPTION = `We are looking for a Senior Full Stack Engineer to lead the development of our web applications.
You will design scalable backend services using Python/FastAPI and rich, interactive user interfaces in React.
Key responsibilities:
- Lead features from conceptual design to production deployment, taking full ownership.
- Maintain a high standard of technical excellence by writing clean, testable code and participating in reviews.
- Work closely with customer success to address issues and enhance customer obsession.
- Innovate and propose new tools/architectures to improve platform performance.
- Collaborate closely with cross-functional teams to build impactful products.`;

/** Intentionally vague — gives GEPA room to evolve better lenses */
export const DEFAULT_CORE_VALUES = [
  {
    name: 'Be Cool',
    description: 'People should be cool and not uncool.',
  },
  {
    name: 'Work Hard',
    description: 'Try to work hard when you feel like it.',
  },
  {
    name: 'Team Stuff',
    description: 'Teams are good. Be on a team sometimes.',
  },
  {
    name: 'Innovation Maybe',
    description: 'Do new things if they come up. Innovation is trendy.',
  },
  {
    name: 'Customers?',
    description: 'Customers exist. Think about them occasionally.',
  },
];

/** Intentionally weak user angles — demo mode uses these verbatim as GEPA seed */
export const DEFAULT_EVALUATION_PROMPTS = [
  `Look at the resume.

Give some kind of score.`,

  `Problem solving?

Not sure what to look for. Score them.`,

  `Culture.

Team stuff maybe. Pick a number.`,

  `Communication.

Writing seems fine or not. Rate it.`,

  `Career.

Did things happen on the resume? Score 1-5 I guess.`,
];
