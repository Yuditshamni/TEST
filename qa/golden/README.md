# qa/golden — golden questions

Business questions with a known correct answer, written in the users' language. Collected from the first client meeting onward: every question the client asks is a golden question.

One file per domain, `qa/golden/<domain>.md`. Template: `_template.md`.

Used three ways:
- before a release, each question is answered from the new model and compared with `expected_answer`;
- when an AI assistant answers users over the data, the same questions measure its accuracy per domain, tracked over time;
- a report spec (`ui/`) lists the questions it answers by their id.

A wrong answer is fixed in the model (a description, a synonym, a missing measure), not in a prompt.

Owner: systems analyst. Skill: `nogamy-qa-checks`.
