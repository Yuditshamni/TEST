# Golden questions — sales

| id | question_he | expected_answer | proof_sql | source_of_truth | status |
|---|---|---|---|---|---|
| GQ-001 | כמה לקוחות פעילים יש לאקמה? | 5 | SELECT COUNT(*) FROM GOLD.SALES_DIM_CUSTOMER WHERE IS_ACTIVE_IND = 1 AND KEY_CUSTOMER <> '-99' | the example's bronze rows (migration `0005`): 7 customers, 2 with status `I`; C-1005 counted once, not twice (BR-001) | draft |
| GQ-002 | כמה לקוחות יש בכל פלח? | קמעונאות 4, סיטונאות 2, לא ידוע 1 | SELECT SEGMENT_NAME, COUNT(*) FROM GOLD.SALES_DIM_CUSTOMER WHERE KEY_CUSTOMER <> '-99' GROUP BY SEGMENT_NAME | the example's bronze rows: `RT` ×4, `WH` ×2 (C-1005 once), `XX` ×1 (BR-003) | draft |

Status: `draft` (value is an example) → `verified` (checked against the legacy system or the source, with the date).
The expected answers hold for the example's invented test data only. In a project they come from the legacy report or the source, and the status moves to `verified` with the date.
