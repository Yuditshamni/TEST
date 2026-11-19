# Golden questions — <domain>

| id | question_he | expected_answer | proof_sql | source_of_truth | status |
|---|---|---|---|---|---|
| GQ-001 | כמה לקוחות פעילים היו בסוף הרבעון? | <n> | SELECT COUNT(*) FROM GOLD.<TABLE> WHERE … | <the legacy report, or the source query> | draft |

Status: `draft` (value is an example) → `verified` (checked against the legacy system or the source, with the date).
