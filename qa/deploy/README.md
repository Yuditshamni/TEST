# qa/deploy — one test document per deploy

`qa/deploy/<branch topic>.md`, written by the AI in the same PR as the change. Template: `_template.md`. Rules: skill `nogamy-deploy`.

Ready-to-run queries and what each must return, so whoever deploys checks the result without thinking up the checks. One column per environment: DEV is filled before the PR; TEST and PROD by whoever deployed there.

The filled document stays in the repo: it is the record of what was checked where.
