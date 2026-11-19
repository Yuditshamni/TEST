# nogamy-plan-and-explain — Microsoft Fabric

Read when `_context/platform.md` §2 names Fabric. Same rules as `SKILL.md`; only the examples change.

## 2. What a plan contains — who runs what

- With `tools/fabric` and the AI identity in `PROJECT.md`, the norm is L3: the agent runs the DEV steps itself.
- The plan still says each step and who runs it: migration, pipeline publish, pipeline run, checks.
- TEST and PROD: always a person. The plan says so in "מה לא נוגעים".

## 4. Example check question

```
שאלה קטנה לפני שממשיכים:
למה מפרסמים קודם pipeline אחד, מריצים אותו, ורק אז את השאר?
1. כי Fabric לא מאפשר לפרסם כמה pipelines יחד.
2. כי pipelines אחרים תלויים בו, ובדיקת drift נקייה לא מוכיחה שהוא רץ.
3. כי פרסום של כמה pipelines מוחק את ההיסטוריה של ההרצות.
```
Right answer: 2. Explanation if wrong: "בדיקת drift משווה רק הגדרות." / "רק הרצה מוכיחה שה-pipeline עובד." / "pipeline שבור יפיל את כל מי שתלוי בו."

## 5. Example plan

```
מה נעשה:
- בונים את הטבלה `GOLD.DIM_CUSTOMER` מה-STT המאושר.

מה משתנה:
- קובץ חדש: `fabric/data/WH_DWH.Warehouse/GOLD/Tables/DIM_CUSTOMER.sql`.
- קובץ חדש: `fabric/data/WH_DWH.Warehouse/SILVER/StoredProcedures/SP_DIM_CUSTOMER.sql`.
- קובץ חדש: `scripts/migrations/0012_add_dim_customer.sql`.
- קובץ בדיקות חדש: `qa/data/DIM_CUSTOMER.sql`.

איך נדע שזה עבד:
- הטבלה `GOLD.DIM_CUSTOMER` לא ריקה.
- אין לקוח שמופיע פעמיים בטבלה `GOLD.DIM_CUSTOMER`.
- הרצה שנייה של הטעינה נותנת אותו מספר שורות.

מי מריץ:
- הסוכן מריץ את `0012` ב-DEV עם `tools/migrate/run_migrations.py --as-agent`.
- הסוכן מריץ את הבדיקות ב-DEV עם `tools/fabric/wh_sql.py`.

מה לא נוגעים:
- לא נוגעים ב-workspace של TEST וב-workspace של PROD.

לאישורך:
- האם לקוח שעזב נשאר בטבלה, עם תאריך עזיבה?
```
