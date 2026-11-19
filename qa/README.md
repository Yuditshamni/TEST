# qa/ — quality

```
qa/
  data/      per-table checks: PASS / FAIL queries, run after every load
  deploy/    one test document per deploy: queries to run and what each must return, a column per environment
  golden/    golden questions: business questions with a known answer
```

- `data/` and `golden/` gate a release: a failed data check stops the load; a wrong golden answer blocks the model from going out.
- `deploy/` is the record of what was checked where. It is also how a person checks a deploy the AI cannot reach.
- Every check reads counts, sums and statuses. No query returns rows of people or customers.

Skills: `nogamy-qa-checks`, `nogamy-deploy`.
