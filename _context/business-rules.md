# Business rules

Rules that today live in people's heads, or inside the expressions of the system we replace. One row per rule. The `nogamy-review` skill checks code and measures against this file.

| id | rule_he | applies_to | source_of_truth | status |
|---|---|---|---|---|
| BR-001 | הזמנה מבוטלת אינה נספרת במכירות | GOLD.SALES_FACT_ORDERS, כל מדדי המכירות | מערכת קיימת: דוח מכירות, מסך ראשי | example |

Status: `draft` → `approved`. A deliberate difference from the legacy system is written here, as a rule, with who approved it. Delete the `example` row when the first real rule is added.
