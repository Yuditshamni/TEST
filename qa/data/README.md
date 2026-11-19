# qa/data — data checks

One `.sql` file per target table, `qa/data/<GOLD TABLE>.sql`, written by the `nogamy-build-table` skill from the STT and extended by hand. One more file for the project: `qa/data/QA_<PROJECT>_END_TO_END.sql`.

Each check returns one row: `check_name | actual | expected | result`, with `PASS` or `FAIL`.

Minimum per table: rows exist · the key is unique · no NULL key · every dimension key exists in its dimension (or is `-99`) · totals equal the source · coded columns hold accepted values only.

How a file is run depends on the AI's access level (`AGENTS.md`): the AI runs it in DEV, or hands it to a person and reads the pasted result. Then the load runs again and the checks run again: the same result = idempotent.

Skill: `nogamy-qa-checks`.
