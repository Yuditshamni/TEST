"""Send one feedback item to the Nogamy core repo, run by the agent in the skill nogamy-feedback.

    python nogamy/ops/feedback.py send --file _private/feedback-draft.md

Order: personal/client data gate (pii_gate.py) → issue in the core repo with the developer's own `gh`
access → labels feedback, skill:<name>, project:<id> (without labels if the developer may not set them;
the curator adds them from the footer). Only the project id leaves the project.
The agent calls this only after the developer approved the exact text.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "nogamy" / "hooks"))
import nogamy_telemetry as tel  # noqa: E402
import pii_gate  # noqa: E402
from core_update import core_repo, current_version  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["send"])
    ap.add_argument("--file", required=True)
    a = ap.parse_args()

    text = Path(a.file).read_text(encoding="utf-8")
    reasons = pii_gate.check(text, pii_gate.client_terms(ROOT / "PROJECT.md"))
    if reasons:
        tel.emit("feedback_blocked", None, reasons=len(reasons))
        print("Blocked, nothing was sent. Rewrite these parts and run again:")
        for r in reasons:
            print(f"- {r}")
        return 1

    m = re.search(r"^Title:\s*(.+)$", text, re.M)
    title = m.group(1).strip() if m else text.strip().splitlines()[0][:100]
    body = re.sub(r"^Title:.*\n+", "", text, count=1, flags=re.M)
    skill = re.search(r"^Skill:\s*`?([\w./-]+)", text, re.M)
    skill = re.sub(r"[^\w.-]", "-", skill.group(1)).strip("-") if skill else "unknown"
    project, _ = tel.project_settings(ROOT)
    body += f"\n\n---\nproject: `{project}` · skill: `{skill}` · core version: `{current_version()}`\n"

    base = ["gh", "issue", "create", "--repo", core_repo(), "--title", f"[{project}] {title}", "--body", body]
    r = subprocess.run(base + ["--label", "feedback", "--label", f"skill:{skill}", "--label", f"project:{project}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(base, capture_output=True, text=True)
    if r.returncode != 0:
        print("Could not open the issue:", r.stderr.strip()[:300])
        return 1
    url = r.stdout.strip()
    tel.emit("feedback_sent", None, skill=skill)
    print(json.dumps({"issue": url}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
