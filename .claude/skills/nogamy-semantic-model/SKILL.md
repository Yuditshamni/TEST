---
name: nogamy-semantic-model
description: The BI layer — the semantic model's skeleton from the STT, business descriptions and synonyms, measure drafts from the legacy measures, row-level security from the access rules, report specs, and what makes the model answer well when an AI assistant queries it. Use for anything under bi/ or ui/.
---

# Semantic model

Location: `bi/<project>/` in the BI tool's text format, or `measures.md` when it has none (`bi/README.md`); the platform's own folder in "Platform specifics". Report specs and mockups: `ui/<report>/`.

## Ownership

| Part | Who |
|---|---|
| tables, columns, relationships, descriptions, synonyms (the skeleton) | data engineer / AI, from the STT |
| measures, hierarchies, formats, security roles | BI developer (the AI drafts, the developer approves) |
| what a report shows, and to whom | BI developer + systems analyst (`ui/`) |

## Rules that hold in any BI tool

- **The model reads gold only.** No business logic rebuilt in the BI tool: a rule that is missing goes back to silver.
- **Measures live in the model**, never in a report. One definition per measure.
- **Relationships** come from `stt/<domain>/relationships.md`: every join on `KEY_<ENTITY>`.
- **Storage mode:** the tool's safest default (usually import). A faster or live mode only after a performance test, recorded as a decision in `_context/architecture.md`.
- The model and the reports go through Git and review like code, when the tool saves them as text.
- The model in DEV points at DEV data; what it points at in TEST and PROD comes from the per-environment mechanism (`nogamy-deploy`).

## A model that people and AI can read

A gold table is done when the table and every column have:

- a business name;
- a description, one short sentence, in the client's language;
- synonyms, as users say them.

They are **copied** from `stt/` (`description_he`, `synonyms_he`) and `_context/glossary.md`. Written once by the analyst, never retyped here. A missing one is fixed in the STT first.

An AI assistant that answers users reads the model, not the data: the descriptions are its only knowledge. It connects **through the model only**, so row-level security applies; a direct connection to the database would bypass it. Users of the assistant need read access on the model, and nothing more.

## Measure drafts from the legacy system

Input: `_context/legacy-measures.md`. For each row with `in_use = yes`:

1. write a draft in the BI tool's language, named as `target_measure`;
2. put the legacy expression and the business meaning in its description;
3. mark it as a draft for the BI developer to approve.

Never invent business logic that is missing from the meaning: ask the analyst. A measure is done when `nogamy-reconcile-numbers` gives it "ready".

## Security

- Roles come from `_context/access-rules.md`. A column marked `pii: yes` appears there, or is not in the model.
- Test a role as a user who has **only** that role. Builders and admins often bypass the filter.

## Golden questions

Before a release, the questions in `qa/golden/<domain>.md` are answered from the model and compared with the expected answers (`nogamy-qa-checks`). A wrong answer is fixed in the model: a description, a synonym, a missing measure.

## Platform specifics

> Skills are core and read-only in a project. Platform facts come from, in order:
> 1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`).
> 2. `_context/platform.md` §10 → `nogamy-semantic-model`: what this project adds or overrides.
> 3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| BI tool; the text format of a model and of a report; their folder | ? |
| How the model reads the data (import / live / other), and the default | ? |
| How a model is saved into the repo and published from it | ? |
| How the model is re-pointed per environment | ? |
| Row-level and column-level security: how defined, who bypasses it | ? |
| An AI assistant over the model: which, and what it needs from the model | ? |
| Licences needed to build and to view | ? |
| Known traps | ? |
