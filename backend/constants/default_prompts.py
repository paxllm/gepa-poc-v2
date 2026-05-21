"""Default human-authored evaluation lenses and core values for seed data and the setup wizard.

Intentionally weak/vague so GEPA seed generation and evolution have headroom to improve prompts.
"""

DEFAULT_CORE_VALUES: list[dict[str, str]] = [
    {
        "name": "Be Cool",
        "description": "People should be cool and not uncool.",
    },
    {
        "name": "Work Hard",
        "description": "Try to work hard when you feel like it.",
    },
    {
        "name": "Team Stuff",
        "description": "Teams are good. Be on a team sometimes.",
    },
    {
        "name": "Innovation Maybe",
        "description": "Do new things if they come up. Innovation is trendy.",
    },
    {
        "name": "Customers?",
        "description": "Customers exist. Think about them occasionally.",
    },
]

DEFAULT_EVALUATION_PROMPTS: list[str] = [
    """Look at the resume.

Give some kind of score.""",

    """Problem solving?

Not sure what to look for. Score them.""",

    """Culture.

Team stuff maybe. Pick a number.""",

    """Communication.

Writing seems fine or not. Rate it.""",

    """Career.

Did things happen on the resume? Score 1-5 I guess.""",
]

SEED_AUTHORED_SET_ID = "seed_authored"
