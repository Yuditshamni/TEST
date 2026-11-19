"""Core report (core repo only), run by .github/workflows/nogamy-core-curator.yml: daily it refreshes the
pinned "Nogamy control panel" issue; on Sundays it also opens the weekly report issue with the AI triage.

    python nogamy/ops/curator.py --usage <folder with usage/**/*.jsonl> --out report.md [--latest v0.3.0] [--triage]

The report opens with "Needs your attention": projects behind the latest release or silent for 14 days,
core files people keep trying to edit, skills the agent keeps skipping, feedback waiting more than 14 days.

Signals, last 30 days unless noted:
- usage per skill (uses, people, projects) and core skills nobody used: candidates to fix or remove
- core_edit_blocked per file: people keep trying to change it → the file is wrong or unclear
- skill_gate_blocked per skill: the agent writes before reading → the description does not trigger
- per project: core version seen, updates applied / declined (declined = the update is not trusted)
- agents in use (Claude Code / Copilot / Codex)
- open feedback issues per skill (gh)
--triage adds an AI section (anthropic SDK, ANTHROPIC_API_KEY): the top changes to make, and why.
People decide; nothing here changes the core.
"""
import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_events(folder, days=30):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    events = []
    for f in Path(folder).rglob("*.jsonl"):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                e = json.loads(line)
                if datetime.fromisoformat(e["ts"]) >= since:
                    events.append(e)
            except (ValueError, KeyError):
                continue
    return events


def latest_release():
    r = subprocess.run(["gh", "release", "view", "--json", "tagName", "-q", ".tagName"], capture_output=True,
                       text=True, cwd=ROOT)
    return r.stdout.strip() or None


def open_feedback():
    r = subprocess.run(["gh", "issue", "list", "--label", "feedback", "--state", "open", "--limit", "200",
                        "--json", "number,title,labels,body,createdAt"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return []
    items = json.loads(r.stdout)
    for i in items:
        labels = [l["name"] for l in i["labels"]]
        skill = next((l[6:] for l in labels if l.startswith("skill:")), None)
        if not skill:
            m = re.search(r"skill:\s*`([\w.-]+)`", i.get("body") or "")
            skill = m.group(1) if m else "unknown"
        i["skill"] = skill
    return items


STALE_DAYS = 14
REPEAT = 3


def attention(proj, blocked, gate, feedback, latest):
    """Short list of what the core owner should act on, most urgent first."""
    today = datetime.now(timezone.utc).date()
    out = []
    behind = sorted(n for n, p in proj.items() if latest and p["version"] not in (latest, "?"))
    if behind:
        out.append(f"{len(behind)} project(s) not on `{latest}`: " + ", ".join(f"`{n}`" for n in behind)
                   + " (their daily core-update PR is open or declined)")
    silent = sorted(n for n, p in proj.items() if p["last"] and
                    (today - datetime.fromisoformat(p["last"]).date()).days >= STALE_DAYS)
    if silent:
        out.append(f"no AI session for {STALE_DAYS}+ days: " + ", ".join(f"`{n}`" for n in silent))
    declined = sorted(n for n, p in proj.items() if p["declined"])
    if declined:
        out.append("core update declined in: " + ", ".join(f"`{n}`" for n in declined) + " (ask why: the update is not trusted)")
    for f, n in blocked.most_common():
        if n >= REPEAT:
            out.append(f"`{f}`: {n} blocked edit attempts (the file is wrong or unclear for the people using it)")
    for s, n in gate.most_common():
        if n >= REPEAT:
            out.append(f"`{s}`: the agent wrote {n} times before opening it (its description does not trigger)")
    old = [i for i in feedback if (today - datetime.fromisoformat(i["createdAt"].replace("Z", "+00:00")).date()).days
           > STALE_DAYS]
    if old:
        out.append(f"{len(old)} feedback issue(s) open for more than {STALE_DAYS} days: "
                   + ", ".join(f"#{i['number']}" for i in old[:10]) + " (label one `fix-approved` to get a fix PR)")
    return out


def build(events, feedback, latest=None):
    core_skills = sorted(p.name for p in (ROOT / ".claude/skills").glob("nogamy-*") if p.is_dir())
    use, people, projects = Counter(), defaultdict(set), defaultdict(set)
    for e in events:
        if e.get("event") == "skill_used":
            s = e.get("skill", "?")
            use[s] += 1
            people[s].add(e.get("user"))
            projects[s].add(e.get("project"))
    blocked = Counter(e.get("core_path") for e in events if e.get("event") == "core_edit_blocked")
    gate = Counter(e.get("skill") for e in events if e.get("event") == "skill_gate_blocked")
    agents = Counter(e.get("agent") for e in events if e.get("event") == "session_start")
    proj = defaultdict(lambda: {"version": "?", "last": "", "applied": 0, "declined": 0, "sessions": 0})
    for e in sorted(events, key=lambda x: x["ts"]):
        p = proj[e.get("project", "unknown")]
        p["version"], p["last"] = e.get("core_version", p["version"]), e["ts"][:10]
        p["applied"] += e.get("event") == "core_update_applied"
        p["declined"] += e.get("event") == "core_update_declined"
        p["sessions"] += e.get("event") == "session_start"
    fb = Counter(i["skill"] for i in feedback)

    L = [f"# Nogamy core report — {datetime.now(timezone.utc):%Y-%m-%d}", "",
         f"Latest release `{latest or '?'}` · {len(events)} usage events in 30 days · {len(proj)} projects · "
         f"{len(feedback)} open feedback issues", ""]
    todo = attention(proj, blocked, gate, feedback, latest)
    L += ["## Needs your attention", ""] + ([f"- {x}" for x in todo] or ["- nothing: every project is current, no repeated blocks"]) + [""]
    L += ["## Core skills", "", "| Skill | Uses | People | Projects | Open feedback | Gate blocks |", "|---|---|---|---|---|---|"]
    for s in sorted(core_skills, key=lambda x: -use[x]):
        L.append(f"| `{s}` | {use[s]} | {len(people[s])} | {len(projects[s])} | {fb[s]} | {gate[s]} |")
    dead = [s for s in core_skills if not use[s]]
    L += ["", f"**Not used in 30 days:** {', '.join(f'`{s}`' for s in dead) or 'none'}", ""]
    L += ["## Core files people tried to edit", ""]
    L += [f"- `{p}`: {n}" for p, n in blocked.most_common(15)] or ["- none"]
    L += ["", "## Projects", "", "| Project | Core version | Current? | Last seen | Sessions | Updates applied | Declined |",
          "|---|---|---|---|---|---|---|"]
    for name, p in sorted(proj.items()):
        cur = "?" if not latest else ("yes" if p["version"] == latest else "**no**")
        L.append(f"| `{name}` | {p['version']} | {cur} | {p['last']} | {p['sessions']} | {p['applied']} | {p['declined']} |")
    L += ["", "## AI tools", ""] + ([f"- {a}: {n} sessions" for a, n in agents.most_common()] or ["- no sessions"])
    core_agents = sorted(p.stem for p in (ROOT / ".claude/agents").glob("nogamy-*.md"))
    a_use, a_people = Counter(), defaultdict(set)
    for e in events:
        if e.get("event") == "agent_used":
            a_use[e.get("agent_name", "?")] += 1
            a_people[e.get("agent_name", "?")].add(e.get("user"))
    L += ["", "## Agents (`.claude/agents/`)", "", "| Agent | Uses | People |", "|---|---|---|"]
    L += [f"| `{a}` | {a_use[a]} | {len(a_people[a])} |" for a in sorted(set(core_agents) | set(a_use), key=lambda x: -a_use[x])]
    unused = [a for a in core_agents if not a_use[a]]
    L += ["", f"**Agents not used in 30 days:** {', '.join(f'`{a}`' for a in unused) or 'none'}"]
    L += ["", "## Open feedback", ""]
    L += [f"- #{i['number']} `{i['skill']}` {i['title']}" for i in feedback[:50]] or ["- none"]
    return "\n".join(L) + "\n"


def triage(report, feedback):
    import anthropic
    client = anthropic.Anthropic()
    details = "\n\n".join(f"#{i['number']} [{i['skill']}] {i['title']}\n{(i.get('body') or '')[:1500]}" for i in feedback[:40])
    r = client.beta.messages.create(
        model="claude-opus-5-5", max_tokens=16000,
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        system="You maintain a data-engineering method used by consultants: skills, rules, templates.",
        messages=[{"role": "user", "content":
                   "Weekly report and open feedback below. Propose the 5 most valuable core changes for this week. "
                   "For each: the file, the change in 1-3 lines, which signals support it (issue numbers, counts), "
                   "and the risk. Group duplicate feedback. Flag any feedback that looks like it still contains "
                   "client or personal data. Markdown, short.\n\n" + report + "\n\n# Feedback details\n\n" + details}],
    )
    if r.stop_reason == "refusal":
        return "\n## Triage\n\n(the model declined; triage skipped)\n"
    return "\n## Triage (AI proposal — people decide)\n\n" + next(b.text for b in r.content if b.type == "text") + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usage", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--triage", action="store_true")
    ap.add_argument("--latest", help="the latest release tag (default: gh release view)")
    a = ap.parse_args()
    feedback = open_feedback()
    latest = a.latest or latest_release()
    report = build(load_events(a.usage), feedback, latest)
    if a.triage:
        try:
            report += triage(report, feedback)
        except Exception as ex:
            report += f"\n## Triage\n\n(skipped: {str(ex)[:200]})\n"
    Path(a.out).write_text(report, encoding="utf-8")
    print(report[:3000])


if __name__ == "__main__":
    main()
