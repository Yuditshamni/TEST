---
name: nogamy-reconcile-numbers
description: Validate numbers before anyone outside the team sees them — reconcile the new DWH with the legacy system and with the source, rule out the common pitfalls, and give a ready / with caveats / needs revision verdict. Use before a demo, a sign-off, a report release, or any number sent to the client.
---

# Reconcile and validate numbers

Users trust a number only if it matches the one they know, or if we can explain why it does not.

## 1. Same question?

- Which legacy measure is this? (`_context/legacy-measures.md`: app, expression, meaning.) No legacy system: the source query is the reference.
- Same population (who is counted), same period, same "as of" date, same filters?
- A deliberate difference (a bug fixed, a new rule) → it must be written in `_context/business-rules.md`, with who approved it.

## 2. Reconcile at three levels

| Level | Compare | Tolerance |
|---|---|---|
| total | DWH vs legacy vs source | exact for counts; `< 0.01` for amounts |
| by month | DWH vs legacy | same |
| by one dimension (a status, a unit) | DWH vs legacy | same; the first breakdown that differs points to the cause |

Counts and sums only, never rows. Who runs the queries follows the access level (`_context/platform.md` §7); the AI uses the read-only query command in `PROJECT.md` → Agent tools. The legacy numbers usually come from a person who reads them off the old system.

An independent pass, by someone who did not build the table: the agent `nogamy-data-qa`.

## 3. Pitfalls to rule out

- Join fan-out: the row count grew after a join.
- An incomplete period compared with a full one.
- A changing denominator between periods.
- An average of averages instead of a weighted average.
- Time zone: UTC dates vs local dates at month boundaries.
- `-99` rows counted as real members.
- Case and trailing spaces in codes (`A` vs `a`).
- A population the legacy system excludes without saying so (look for the business rule that names it).
- Different refresh times: one side read before the nightly load, the other after.

## 4. Output

```
## Reconciliation — <measure> — <date>
Verdict: ready | with caveats | needs revision
| level | DWH | legacy | source | diff | explained by |
Caveats to tell the client: …
Open questions: … (also to _context/open-questions.md)
```

A difference without an explanation = "needs revision". Never round a difference away. A reconciled measure becomes a golden question (`qa/golden/`), status `verified`.

On Microsoft Fabric (`_context/platform.md` §2): `references/fabric.md`.
