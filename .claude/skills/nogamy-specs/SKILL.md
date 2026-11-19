---
name: nogamy-specs
description: Write and maintain source specs (sources/) and Source-to-Target specs (stt/) — describe a source system, profile a source table, fill an STT, check it is buildable, export an approved STT for client sign-off. Use when working on sources/, stt/ or _private/docs/specs/, and whenever the systems analyst defines what exists or what to build.
---

# Specs: sources and STT

The analyst writes each fact once, as text. Table definitions, loads, checks and the BI model's descriptions are derived from these files.

## Documents first (iron rule, base §5.1)

- A new domain starts with collecting documents: an STT if one exists (or building it together), the business context, what is known about the sources. Infrastructure and architecture questions come after.
- No STT → no build. The STT entity order is the build order: dimensions before facts, one entity at a time.

## sources/<system>/ — what exists

Templates: `sources/_template/system.md` (→ `<system>/README.md`), `table.md`, `relationships.md`.

- **System file first**: how we connect, which environment we read, the load pattern, how the source signals a delete. What is unknown goes to `_context/open-questions.md`.
- **Table file**: the technical part (type, nullable, key, null %, distinct count) comes from the data dictionary and a profile query (`nogamy-explore-data`). **Profile queries return counts and types only, never values of sensitive columns.**
- The systems analyst fills `meaning_he`, `values_he`, `pii`, `notes`.
- Unknown = `לא ידוע`. Empty = not checked yet. The difference matters: one was asked, the other was not.
- `pii` is filled for every column before anyone reads values from the table. Not filled → the column is treated as sensitive.
- Relationships: `sources/<system>/relationships.md`, each with its evidence (a declared key, a legacy script line, a count of orphans). A source without declared keys is common: the legacy load scripts are the evidence.

## stt/<domain>/<table>.md — what we build

Template: `stt/_template/table.md`. One file per target table.

Before setting `status: approved`, check:
- [ ] target name, grain, load pattern (SNP / SCD1 / SCD2 / Append / Delete+Insert / MERGE / Full)
- [ ] business key, surrogate-key strategy, and how fact keys resolve (`KEY_<ENTITY>`, `-99` when not found)
- [ ] dimension joins: which dimension, on which column; for an SCD2 dimension, which version (ask, never assume)
- [ ] every target column: source, transformation in words, `description_he`, `synonyms_he`, `pii`
- [ ] filters and multi-source policy stated
- [ ] open items moved to `_context/open-questions.md`, not left in the file
- [ ] the business rules it uses exist in `_context/business-rules.md`

Rules:
- `description_he` and `synonyms_he` go to the semantic model as is: write them as users speak.
- Transformation is written in words; the code is derived from it.
- Only `approved` is built (`nogamy-build-table`). Who approves: the analyst for the business columns, the data engineer for the technical ones.
- A change after approval: edit the file, set `status: changed`, say what changed in the PR. The built table follows the spec, never the other way.

## Export for sign-off: _private/docs/specs/

- File: `_private/docs/specs/<domain>_stt_v<major.minor>_<YYYY-MM-DD>.xlsx` (or the format the client signs), one sheet per table, generated from the Markdown by a script (for example Python with `openpyxl`).
- Layout per `_context/working-agreement.md` → Deliverables.
- The exported file is never edited back. Changes go to the Markdown and are exported again.
- Once the client signs: the signed file is copied to `docs/` (in Git, `docs/README.md`). Drafts never go there.

## Working from a chat tool

No repo access: the analyst uploads the pack (`tools/bundle_context.py --skills nogamy-specs,nogamy-explore-data --add sources/<system>`), the AI returns the full text of each file, and the analyst saves it in place.
