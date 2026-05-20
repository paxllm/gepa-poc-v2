"""Default human-authored evaluation lenses for seed data and the setup wizard."""

DEFAULT_EVALUATION_PROMPTS: list[str] = [
    """Rate this engineer.

    Give a score from 1-5 based on whatever feels right.
    Think about coding, projects, personality, communication, and experience.

    Return JSON.""",

    """Check if this person is good at solving problems.

    Use the resume/profile and decide if they seem smart.
    Score from 1-5.

    Return score and reason.""",

    """Does this engineer fit the company culture?

    Look at teamwork and attitude if possible.
    Give a score between 1 and 5.

    Output JSON only.""",

    """Evaluate communication.

    Check if the candidate explains things well.
    Score them from low to high.

    Return JSON.""",

    """Evaluate career growth.

    See if the person improved over time and learned things.
    Give a rating out of 5 and explain shortly.""",
]

SEED_AUTHORED_SET_ID = "seed_authored"
