---
name: nogamy-review
description: Review a branch, a PR or a set of changed files against Nogamy's method and the project rules — SQL, ETL items, the BI model, STT, scripts. Runs on every change before a person reviews. Use when asked to review, or before handing a branch over.
---

# Review

Read the diff (`git diff <main>...HEAD`, or the files the person names) and the files it touches. Do not edit; report.

**Fresh eye.** The one who wrote the change does not review it alone. Before a PR, run the agent `nogamy-code-reviewer` on the branch: it reads this checklist and reports in its own format. Then add its findings to this output.

## Checklist

**Structure**
- [ ] one object per file, right folder, named as the object (`nogamy-db-objects`)
- [ ] every database change has its object file and a numbered migration that agree; the migration is safe to run twice and was applied in DEV
- [ ] no secrets, no connection strings with credentials, no rows of people or customers anywhere (code, comments, examples)
- [ ] files touched belong to this task only; no core file changed (`nogamy-*` skills, `AGENTS.md`, `standards/`, `tools/`, `nogamy/`: a wish to change one → `nogamy-feedback`)
- [ ] a new project skill or agent is named `<project-id>-<what>` (never `nogamy-`) and registered in `PROJECT.md`

**Method (`nogamy-method`)**
- [ ] STT approved for every built table; columns and order match it
- [ ] names and case per `nogamy-naming`; `KEY_<ENTITY>`, `FACT_KEY`
- [ ] no environment in any name or in code (`TRY_` is not an environment: it marks a try-out); no database or server name inside code
- [ ] ETL columns present; `-99` row and `-99` mapping
- [ ] idempotent: can each load run twice with the same result? any insert without a prior delete-by-key, merge or truncate?
- [ ] delta loads: watermark advanced only on success, inside the transaction, and covers every bronze → gold pair; the bronze load timestamp (`LOAD_TO_BRONZE_TS`) is carried to staging
- [ ] silver reads bronze with the `IS_LAST` filter (`IS_LAST_INSERT_TO_BRONZE_IND = 1`)
- [ ] own lane: each entity reads only its bronze → silver → gold; every read of another entity's layers is needed and documented in the view header and the pipeline README
- [ ] `python tools/dev_map.py --check` passes; every dotted arrow in the dev map is a documented dependency
- [ ] one load procedure per entity, going view(s) → silver staging → gold; business logic in views, none hidden in the procedure; no view or watermark the load does not need
- [ ] PK / FK / index policy applied, as agreed for the project
- [ ] a past period can be re-run without losing current data; nothing non-deterministic that differs between runs
- [ ] no permanent work tables (temp tables, or `TRY_` for a try-out); no `TRY_` name in a PR to the main branch
- [ ] header comment, consistent style (`nogamy-write-sql`), no commented-out code, no TODO

**Platform (`_context/platform.md`, `nogamy-write-sql`)**
- [ ] only types and statements the platform supports
- [ ] ETL items: no hard-coded server, ID, path or environment; retry policy per `nogamy-build-pipeline`; README line
- [ ] checks file in `qa/data/` exists and was run twice (results in the PR)
- [ ] test document `qa/deploy/<branch topic>.md` in the PR, expected results as rules, `DEV` column filled (`nogamy-deploy`)
- [ ] the repo and DEV agree: drift check clean, or the differences listed. A clean drift check compares definitions only: the load was also run

**Business**
- [ ] matches `_context/business-rules.md`; measures only in the semantic model, never in a report
- [ ] descriptions and synonyms present for new gold columns

**Break it: where does it fail in production?**
- full volume, not the DEV sample (row counts × years)
- NULLs, empty strings, `-99`, unexpected codes, wrong case
- late-arriving or re-delivered data; a re-run of last month
- two loads at the same time; a load that fails half way
- a source column renamed or retyped (schema drift)
- someone without the developer's rights running it (permissions in TEST and PROD)

One line per real risk, with the scenario. No invented risks.

## Output

```
## Review — <branch>
Summary: <one line>
What's solid: …
Critical (blocks merge): …
Recommended: …
Minor: …
Idempotency: <answer per load>
Standards compliance: <base rules met / deviations used, from the project's deviations table (`nogamy-method`)>
Fresh eye: <`nogamy-code-reviewer` ran: yes / no, and why not>
Not verified: <what the review could not check, and why>
Improvements (AI suggestions): …
Open questions: … (also add to _context/open-questions.md if new)
```

Label each finding: iron rule / company standard / company recommendation / AI suggestion.

On Microsoft Fabric (`_context/platform.md` §2): the platform checks are in `references/fabric.md`.
