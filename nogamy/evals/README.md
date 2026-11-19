# Evals — fixed tasks that every core change must still pass

`cases/*.json`: one request a developer could make, the skills it touches, and the checks:
`must` (the agent clearly does this) and `must_not` (the agent clearly does not).
`run_evals.py` gives the agent model AGENTS.md, the PROJECT.md skeleton and every core skill, then a
judge model grades the answer against the checks. Runs in core CI (cases of the changed skills)
and before every release (all cases). Needs `ANTHROPIC_API_KEY`.

Add a case when: a feedback issue is fixed (the case proves it stays fixed), or a new skill is added
(3–5 cases per core skill is the target). Invented data only; personal-looking data is allowed only in
`feedback-scrub.json`, on purpose.

    pip install anthropic
    python nogamy/evals/run_evals.py
