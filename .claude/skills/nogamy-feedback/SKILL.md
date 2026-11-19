---
name: nogamy-feedback
description: Send feedback on the Nogamy core (a nogamy-* skill, AGENTS.md, standards, tools, templates, framework objects) to the core team as an issue, with all personal and client data removed first. Use when the developer says "feedback", "פידבק", "the skill missed", "the core should", "this rule is wrong", or when a core file needs a change (core files are read-only in a project).
---

# Feedback to the Nogamy core

Core files are read-only in a project. A needed change reaches the core only through this skill.
The core team reads every item, and the fix reaches every project in the next core update.

## When

- The developer says "feedback: …" / "פידבק: …".
- A `nogamy-*` skill did not cover a case, gave a wrong instruction, or was not picked when it should have been.
- The agent was blocked from editing a core file, and the change still seems right.
- The same project-only workaround was needed twice: maybe it belongs in the core.

Not feedback: a project fact (→ `PROJECT.md`, `_context/`), a project-only rule (→ `PROJECT.md` → Project rules), a project skill (→ `nogamy-create-skill`).

## Steps

1. **Understand.** Ask at most one question if the target or the problem is unclear.
2. **Draft** in the format below, in English (Hebrew is fine for quoted wording).
3. **Scrub** — iron rule, no exceptions. Remove or replace with a placeholder:
   - people: names, e-mails, phones, IDs, any row about a person;
   - client: client name, org and repo names, system/product names, the words in `PROJECT.md` → `Never in feedback`;
   - data: real values, counts that identify the client, table or column names that reveal the client's business (`BRONZE_<SOURCE>_<TABLE>` is fine, the real one is not);
   - environment: workspace, warehouse, tenant or item IDs (GUIDs), server names, URLs, connection strings, secrets.
   Describe the **pattern**, never the instance. Example: "a delta load by a date column with late-arriving rows", not the real table.
4. **Gate.** Save the draft to `_private/feedback-draft.md` and run `python nogamy/ops/pii_gate.py --file _private/feedback-draft.md`. Blocked → rewrite and run again. Never send a blocked draft.
5. **Show** the final text to the developer, word for word. Send only after an explicit "yes" / "שלח".
6. **Send:** `python nogamy/ops/feedback.py send --file _private/feedback-draft.md`.
   It runs the gate again and opens the issue in the Nogamy core repo with the developer's own `gh` access,
   labeled `feedback`, `skill:<name>`, `project:<id>`. Only the project id leaves the project, not the repo or org name.
   No `gh` or no access → give the developer the final text to paste in the core repo's "Nogamy feedback" form.
7. **Report** in one line: the issue link. Delete `_private/feedback-draft.md`.

## Format

```
Title: [<core file or skill>] <the gap in a few words>

Skill: <nogamy-... or "AGENTS.md" / "standards/..." / "tools/..." / "framework">
Kind: gap | wrong | unclear | not picked | new skill | bug
What happened: <generic pattern, 1–3 lines>
Expected: <what the core should say or do>
Suggested change: <optional: wording, a new step, a rule>
Workaround used in the project: <optional, generic>
```

## Rules

- Never send without the developer's explicit approval of the final text.
- Never send a draft the gate blocked, never "fix" the gate by rewording a real value into a disguised one.
- Never open the issue any other way than `feedback.py` (it is the gate), and never put a link to the project repo in the text.
- One issue, one topic. Two topics → two issues.
- Do not change the core file while waiting. Use a project-side workaround if needed (`PROJECT.md` → Project rules, or a project skill) and mention it in the issue.
