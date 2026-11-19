---
name: nogamy-build-pipeline
description: Write an ingestion or orchestration item (pipeline, job, flow, DAG) in the repo — naming, folders, master and child pattern, config-driven or direct, run order with quality gates, retry policy, and no hard-coded environment. Use when creating or changing anything under etl/, or when deciding how loads are ordered and scheduled.
---

# Pipelines and jobs

Whatever the tool calls them. Names: `nogamy-naming`. Source of the patterns: Nogamy's pipeline methodology in `standards/`.

## Where

```
etl/<project>/
  00_orchestration/     schedule and wrappers: they only call other items and wait
  01_bronze/            a wrapper per domain; a master per source group; a child per source table
  03_gold/              dimensions → facts, with quality gates
etl/_shared/            generic items (quality gate), shared variables
etl/<project>/README.md one line per item: what it does, its trigger, its dependencies
```

(A platform reference may set another root, e.g. `references/fabric.md`. The rules stay.)

- Every new item gets its line in the README, in the same commit.
- The tool cannot export text → one `<name>.md` per item instead (`etl/README.md`). The rules below still hold.
- A try-out item (a connection test, a comparison, a demo nobody will schedule) lives in a `TRY` folder in the tool, never in a project folder or the root. Like `TRY_` objects (`nogamy-db-objects`) it never reaches the main branch; the repo-vs-DEV check lists it, and the developer deletes it when done.

## Patterns

- **Config or direct**, per source system (`nogamy-bronze-load`). Direct: one item with the copy, the gate and its values as parameter defaults.
- **Master and child** (config): the master reads the active config rows of a group, loops over them (in parallel, with a limit), and calls one child per row, waiting for it. The child loads one table.
- **Children do not know the config table.** They get parameters. Each child can be run and tested alone.
- **Nothing source-specific typed into an item.** Table, schema and entity names come from config or parameters. A new source table = a new config row.
- Tokens and shared lookups are fetched once, before the loop.
- **Window:** from config; a special-dates row may override it for one run; advanced only after the bronze gate passes (`nogamy-bronze-load`).
- **API sources:** credentials live in the tool's connection or secret store, never in the item. Prove the call by hand first, then build.
- **Gold order:** dimensions in parallel → wait for all (`Finish Dims`) → dimensions gate → facts → wait (`Finish Facts`) → facts gate. A fact that depends on another fact says so explicitly.
- **A fact runs only if its own dimensions and its own bronze tables passed.** One failed bronze table must not stop unrelated entities, and must not let a dependent entity run on empty data.
- **Orchestration items** hold only calls and waits. No logic.
- Every parameter that has a sensible default gets one.

## Retry

- A load that failed is investigated, not retried: default no retry on procedure steps, with a long timeout.
- A retry is allowed only for a step that is **safe to repeat**, and only for a cause the platform documents as transient (a write conflict, a throttled call). Typical: an update of a table that parallel children share (the config window), and the bronze merge procedure. Say which in the item's README line.

## Status

An item can end in success while a step inside it failed (a later step that runs "on completion"). After a run, read the status of every step, not only of the item.

## No hard-coded environment

- Server names, database names, IDs, paths, child-item IDs: **never** typed into an item.
- They come from the per-environment mechanism in `_context/platform.md` §5 (a parameter file, a variable set, a config table), by name. Every variable an item uses is declared in it.
- A child is called by name or through that mechanism, never by a call type that writes the DEV ID of the child into the item.
- Connections are referenced by name or by a placeholder; the real value per environment lives outside Git.
- A change in the mechanism itself (a new variable, a new connection) is listed in the deployment note: it must exist in the target **before** the deploy (`nogamy-deploy`). Creating a connection or giving an identity a role is a permission change, for an admin, not the AI.

## Publish and test

Who does it follows the access level (`_context/platform.md` §7); at L0–L2 it is a run sheet (`nogamy-dev-workflow`).

1. Per-environment values first, when they changed.
2. The item to DEV, into the tool folder that mirrors the repo folder.
3. Run it; read the status of every step; then the table checks.
4. A definition that matches the repo does not prove the item runs. Run it.

A change many items depend on (a new connection, a new step type): check its prerequisites, publish one item, run it, then publish the rest.

## Before you finish

- [ ] dependencies complete; parameter names match between caller and callee
- [ ] procedure and schema names exist in the database
- [ ] no server, ID, path or environment name typed into the item
- [ ] every per-environment value the item uses is declared and exists in DEV
- [ ] README line added
- [ ] run in DEV, every step's status read

## Platform specifics

Skills are core and read-only in a project. Platform facts come from, in order:
1. `references/<platform>.md` in this folder, for each platform named in `_context/platform.md` §2 (shipped: `fabric.md`, `adf.md`, `airflow.md`).
2. `_context/platform.md` §10 → `nogamy-build-pipeline`: what this project adds or overrides.
3. Neither exists → the table below is the question list: fill the answers in `_context/platform.md` §10 at setup (`nogamy-project-setup`), verified in the official docs (`nogamy-platform-watch`).

| Topic | This project |
|---|---|
| ETL tool, orchestration tool | ? |
| Text format of an item in the repo; how it is exported and published | ? |
| How a child item is called | ? |
| Per-environment values: the mechanism and its syntax inside an item | ? |
| Connections: how they are referenced; who may create them | ? |
| Parallelism limit in a loop | ? |
| Default retry and timeout per step type | ? |
| How a schedule is defined, and whether it is in Git | ? |
| What must be done by hand in the tool's UI | ? |
| Known traps | ? |
