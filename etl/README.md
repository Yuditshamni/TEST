# etl/ — ingestion and orchestration items

Pipelines, jobs, flows, DAGs: whatever the project's ETL and scheduling tools call them, in the text format the tool exports (JSON, YAML, XML, Python).

```
etl/
  <project>/
    00_orchestration/     schedules and wrappers: they only call other items and wait
    01_bronze/            source → bronze
    02_silver/
    03_gold/              dimensions → facts, with quality gates
    04_qa/
    README.md             one line per item: what it does, its trigger, its dependencies
  _shared/                what all projects share: variables, generic items
```

- Names: `nogamy-naming`. Patterns: `nogamy-build-pipeline`.
- **No environment inside an item.** Server names, IDs and paths come from the mechanism in `_context/platform.md` §5.
- Connections, credentials and schedules that the tool does not export are not in Git: `_context/platform.md` §4 says where they are recorded.
- **The tool cannot export text?** Keep one `<name>.md` per item instead: source, target, parameters, schedule, dependencies, and what it runs. The spec is then the record, and a change to the item starts with a change to this file.

Owner: data engineer.
