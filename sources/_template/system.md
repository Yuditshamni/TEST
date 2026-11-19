# <System name>

type: <database engine / API / files>   owner_business: <role>   owner_technical: <DBA / vendor>   status: draft
description_he: <מה המערכת עושה בארגון, ומי משתמש בה>

## Access

| Topic | Value |
|---|---|
| How we connect (driver, gateway, API, file drop) | |
| Account and its rights (no passwords here) | |
| Environment we read from (production / copy / test) | |
| Sensitive data in this source | |
| Refresh: when the source itself is updated | |
| Limits (rate, window, size) | |

## Load

| Topic | Value |
|---|---|
| Load pattern for the system (`nogamy-bronze-load`) | <FULL / FULL_MERGE / DELTA / …> |
| Config-driven or a direct pipeline, and why | |
| How the source signals a deleted row | |
| Change column that can be trusted | |

## Tables

| Table | Rows | Load | Spec | Status |
|---|---|---|---|---|
| | | | `<TABLE>.md` | draft |

## Findings

Numbered. What was learned about this source the hard way: type surprises, keys that are not unique, columns that mean something else than their name. Each one with its evidence (a count, an error text), never with rows.
