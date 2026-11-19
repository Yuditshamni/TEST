"""Open a new Nogamy project in one command: the repo from the core template, main protected, the core check
required. Run by a person (project lead) with their own `gh` sign-in and admin on the target owner. The AI never
runs it: it creates a repo and sets protection.

    python tools/new_project.py <owner>/<repo>  [--public] [--clone <folder>] [--dry-run]

Steps (each printed with its result):
1. `gh repo create <owner>/<repo> --template <core repo> --private` (the core repo is in nogamy/core.json).
2. Waits until GitHub has copied the template (branch main exists).
3. Protects main: changes only by pull request with one approval, and the check `nogamy-core-guard` required.
   GitHub refuses protection on a private repo of a free plan: the script says so and what to do instead.
4. With --clone: clones the repo, so the next step is opening it in the editor.
Then: open the folder in VS Code (or any AI tool) and say "set up the project" (skill nogamy-project-setup).
Standard library only, plus the gh CLI.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def core_repo():
    return json.loads((ROOT / "nogamy/core.json").read_text(encoding="utf-8"))["core_repo"]


def gh(*args, stdin=None, check=True):
    r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit(f"gh {' '.join(args[:3])}... failed: {r.stderr.strip()[:400]}")
    return r


PROTECTION = {
    "required_status_checks": {"strict": False, "contexts": ["nogamy-core-guard"]},
    "enforce_admins": False,
    "required_pull_request_reviews": {"required_approving_review_count": 1},
    "restrictions": None,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("repo", help="<owner>/<repo>, e.g. nogamy-tech/acme-dwh")
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--clone", help="folder to clone into")
    ap.add_argument("--dry-run", action="store_true", help="print the steps, change nothing")
    a = ap.parse_args()
    if a.repo.count("/") != 1 or re.search(r"(^|[-_./])(dev|test|prod)([-_.]|$)", a.repo.lower()):
        sys.exit("repo must be <owner>/<repo>, with no environment in the name (AGENTS.md: same names everywhere)")
    template = core_repo()
    steps = [f"create {a.repo} from template {template} ({'public' if a.public else 'private'})",
             "wait for branch main", "protect main: PR + 1 approval + required check nogamy-core-guard"]
    if a.clone:
        steps.append(f"clone into {a.clone}")
    if a.dry_run:
        print("\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)))
        return 0

    gh("auth", "status")
    print(f"1. {steps[0]}")
    gh("repo", "create", a.repo, "--template", template, "--public" if a.public else "--private")
    print("   ok")

    print("2. waiting for GitHub to copy the template")
    for _ in range(40):
        if gh("api", f"repos/{a.repo}/branches/main", check=False).returncode == 0:
            print("   ok")
            break
        time.sleep(3)
    else:
        sys.exit("   main did not appear within 2 minutes; run this script again with the same name later")

    print(f"3. {steps[2]}")
    r = gh("api", "-X", "PUT", f"repos/{a.repo}/branches/main/protection", "--input", "-",
           stdin=json.dumps(PROTECTION), check=False)
    if r.returncode == 0:
        print("   ok")
    elif "upgrade" in r.stderr.lower() or "403" in r.stderr:
        print("   GitHub refused: branch protection on a private repo needs a paid plan for this owner.\n"
              "   Until then: every change still goes by PR (AGENTS.md), and nogamy-core-guard still runs on each PR;\n"
              "   it is only not enforced. Record this in _context/platform.md section 4.")
    else:
        print(f"   failed: {r.stderr.strip()[:300]}")

    if a.clone:
        print(f"4. {steps[3]}")
        subprocess.run(["gh", "repo", "clone", a.repo, a.clone], check=True)
        print("   ok")
    print(f"\nDone. Open {'the folder ' + a.clone if a.clone else a.repo} in your editor and tell the agent: "
          "\"set up the project\" (nogamy-project-setup).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
