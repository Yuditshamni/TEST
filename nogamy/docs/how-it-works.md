# How the Nogamy core works

One core, many projects. The core learns from the projects; the projects get the core's improvements.
AI proposes every change; a person approves every change.

```
            ┌──────────────── nogamy-core (Nogamy org, template) ────────────────┐
            │ skills · AGENTS.md · standards · tools · framework · hooks · evals │
            │ CI → release vX.Y.Z → weekly curator report                        │
            └───────▲───────────────────────▲──────────────────────────┬─────────┘
       feedback     │          usage events │                          │ daily check:
       (issues)     │          (usage-data) │                          │ "core update vX" PR
            ┌───────┴───────────────────────┴──────────────────────────▼─────────┐
            │ project repo: PROJECT.md · _context · fabric · sources · stt · ... │
            │ core files read-only: hook + VS Code + nogamy-core-guard            │
            └─────────────────────────────────────────────────────────────────────┘
```

## The loop

1. **Use.** Developers work with Copilot, Claude Code or Codex. The skills and rules come from the core.
2. **Lock.** A core file cannot be changed in a project: the hook blocks the agent, VS Code shows it
   read-only, and `nogamy-core-guard` fails a PR in which a core file differs from the release.
3. **Learn.** Four signals reach the core team:
   - feedback (`nogamy-feedback`): a person says what is missing or wrong, cleaned of client data;
   - usage: which skills are used, by whom, in which project;
   - quiet signals: core files people tried to edit, skills nobody opens, updates declined;
   - the weekly curator report, with an AI triage of the top changes.
4. **Improve.** The core team changes the core by PR. CI checks structure, client data and the evals.
5. **Release.** `nogamy-core-release` publishes vX.Y.Z with notes and the feedback it closed.
6. **Spread.** Each project's first session of the day checks the core and offers the update PR.
   The developer merges it. Back to 1.

## Who does what

| Who | Does |
|---|---|
| Developer | works, sends feedback, merges the daily core update PR of their project |
| Project approver (`PROJECT.md`) | owns `PROJECT.md`, project skills and rules |
| Core team | reads feedback and the weekly report, changes the core by PR, releases |
| AI | proposes: drafts feedback, opens update PRs, triages the report. Never merges, never edits core in a project |

Setup: `setup.md`. Telemetry: `telemetry.md`. What is core: `../core-manifest.txt`.
