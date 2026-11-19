# ui/ — reports

One folder per report: what the report should be. The report itself and the semantic model, when the BI tool saves them as text, live in `bi/`.

```
ui/
  _template/
  <report>/
    spec.md              audience, the questions it answers, pages, filters, measures used, security
    mockup.png           image export (PNG); no PDF or Office files here (_private/docs/, or docs/ when signed)
```

Rules: visuals use measures from the semantic model only; no measure is defined inside a report.
Owner: BI developer. The spec is written with the systems analyst. Every question a report answers is also a golden question (`qa/golden/`).
