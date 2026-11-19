# bi/ — semantic models and reports

What the BI tool saves as text: the semantic model (tables, relationships, measures, descriptions, security roles) and, where supported, the reports.

```
bi/
  <project>/
    <model>/            the model in the tool's text format
    <report>/           the report in the tool's text format, if it has one
    measures.md         when the tool has no text format: every measure, its formula, its meaning
```

- Measures live in the model, never in a report.
- Descriptions and synonyms come from `stt/` and `_context/glossary.md`: written once by the analyst, copied here, never retyped.
- Security roles come from `_context/access-rules.md`.
- What a report should be (audience, questions, pages): `ui/`.

Owner: BI developer. Skill: `nogamy-semantic-model`.
