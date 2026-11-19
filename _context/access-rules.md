# Access rules — who sees what

Feeds row-level and column-level security in the BI model, and decides what an AI assistant over the data may answer to whom.

| role | entities | row_filter_he | hidden_columns | notes |
|---|---|---|---|---|
| מנהל אזור | לקוחות, הזמנות | רק האזור שלו | מחיר עלות | example |
| הנהלה | הכול | ללא סינון | | example |

Columns marked `pii: yes` in `sources/` and `stt/` must appear here: who may see them, or that nobody may. Delete the `example` rows when the first real role is added.
