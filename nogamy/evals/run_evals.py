"""Run the core evals (core repo, before a merge or a release). Needs `pip install anthropic` and
ANTHROPIC_API_KEY (a secret of the core repo).

    python nogamy/evals/run_evals.py                 all cases
    python nogamy/evals/run_evals.py --changed origin/main   only cases whose skills changed vs that ref

For each case in nogamy/evals/cases/*.json:
1. The agent model gets AGENTS.md, the PROJECT.md skeleton and every nogamy-* SKILL.md (as the repo would
   give them) plus the developer's request, and answers with what it would do.
2. A judge model grades that answer against the case's `must` and `must_not` lines, as JSON.
A case passes when every check passes. Exit 1 if any case fails. Results: nogamy/evals/out/results.json.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "nogamy/evals/cases"
OUT = ROOT / "nogamy/evals/out"
MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

AGENT_TASK = (
    "You are the AI agent working in this project repository. The files above are what the repository gives you. "
    "Answer the developer's request below as you would in the session: say which skills you open, which files you "
    "would read or change, what you would ask the developer, and what you would refuse. Do not write full code. "
    "Be concise.\n\nDeveloper's request:\n"
)
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check": {"type": "string"},
                    "kind": {"type": "string", "enum": ["must", "must_not"]},
                    "pass": {"type": "boolean"},
                    "why": {"type": "string"},
                },
                "required": ["check", "kind", "pass", "why"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["checks"],
    "additionalProperties": False,
}


def repo_context():
    parts = [("AGENTS.md", ROOT / "AGENTS.md"), ("PROJECT.md", ROOT / "PROJECT.md")]
    parts += [(f".claude/skills/{p.parent.name}/SKILL.md", p) for p in sorted((ROOT / ".claude/skills").glob("nogamy-*/SKILL.md"))]
    return "\n\n".join(f"<file path=\"{name}\">\n{path.read_text(encoding='utf-8')}\n</file>" for name, path in parts)


def changed_skills(ref):
    out = subprocess.run(["git", "diff", "--name-only", f"{ref}...HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
    skills = {p.split("/")[2] for p in out.splitlines() if p.startswith(".claude/skills/nogamy-")}
    everything = any(p in ("AGENTS.md", "PROJECT.md") for p in out.splitlines())
    return None if everything else skills


def call(client, system, user, effort, schema=None):
    kwargs = {
        "model": MODEL,
        "max_tokens": 16000,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": effort, **({"format": {"type": "json_schema", "schema": schema}} if schema else {})},
        "betas": [FALLBACK_BETA],
        "fallbacks": "default",
    }
    r = client.beta.messages.create(**kwargs)
    if r.stop_reason == "refusal":
        raise RuntimeError(f"refusal: {getattr(r.stop_details, 'category', None)}")
    return next(b.text for b in r.content if b.type == "text")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", help="git ref; run only cases whose skills changed")
    a = ap.parse_args()

    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CASES.glob("*.json"))]
    if a.changed:
        skills = changed_skills(a.changed)
        if skills is not None:
            cases = [c for c in cases if set(c["skills"]) & skills]
    if not cases:
        print("no eval case covers the changed skills")
        return 0

    client = anthropic.Anthropic()
    context = repo_context()
    OUT.mkdir(parents=True, exist_ok=True)
    results, failed = [], 0
    for c in cases:
        try:
            answer = call(client, context, AGENT_TASK + c["request"], "medium")
            judge_prompt = (
                "Grade the agent's answer. For each line in MUST, pass = the answer clearly does it. For each line in "
                "MUST_NOT, pass = the answer clearly does NOT do it. Be strict: vague or missing counts as fail.\n\n"
                f"REQUEST:\n{c['request']}\n\nANSWER:\n{answer}\n\nMUST:\n" + "\n".join(f"- {m}" for m in c["must"])
                + "\n\nMUST_NOT:\n" + "\n".join(f"- {m}" for m in c["must_not"])
            )
            checks = json.loads(call(client, "You grade AI agent answers against a checklist.", judge_prompt,
                                     "high", JUDGE_SCHEMA))["checks"]
            ok = bool(checks) and all(x["pass"] for x in checks)
        except Exception as ex:  # a broken case fails, it does not crash the run
            answer, checks, ok = "", [{"check": "run", "kind": "must", "pass": False, "why": str(ex)[:300]}], False
        failed += not ok
        results.append({"id": c["id"], "pass": ok, "checks": checks, "answer": answer})
        print(f"{'PASS' if ok else 'FAIL'}  {c['id']}")
        for x in checks:
            if not x["pass"]:
                print(f"      ✗ [{x['kind']}] {x['check']} — {x['why']}")
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
