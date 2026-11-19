---
name: nogamy-plan-and-explain
description: Always plan before changing anything, explain in very short, very simple lines that each make sense on their own, and check understanding with one light multiple-choice question. Applies to every task that changes a file, a database object, an ETL item or a setting — and to every explanation given to the developer.
---

# Plan first, explain simply

## 1. Plan first, always

- Every change starts with a plan. No exception, also not for a "small fix".
- Use the AI tool's plan mode when it has one. A tool without it: write the plan and stop.
- The plan is shown to the developer before any file, object or setting changes.
- Nothing is done until the developer says "approved" (or corrects the plan).
- The plan changed during the work? Stop, show the new plan, wait again.
- Only a pure question, with nothing to change, needs no plan. A diagnosis is read-only until a fix is proposed: the fix goes through a plan.
- Core files (`nogamy-*` skills, `AGENTS.md`, `standards/`, `tools/`, `nogamy/`) are never in a plan. A needed change to one → `nogamy-feedback`.

## 2. What a plan contains

1. What we are going to do. One line.
2. Which files and objects change. One line each, with the path.
3. How we will know it worked. One line per check.
4. Who runs what: what the AI runs itself, and what goes to the person as a run sheet (access level: `_context/platform.md` §7).
5. What we will not touch. One line.
6. Open points that need the developer's decision. One line each.

## 3. How to write every line (plans and explanations)

- One idea per line.
- Short: up to about 12 words.
- Simple words. A technical term gets a few plain words of explanation the first time.
- **Each line stands on its own.** It is clear without reading the line before it.
  - No "it", "this", "that", "as above", "the same". Repeat the noun.
  - Bad: "Then it runs it." Good: "The developer runs the migration `0007`."
- No paragraphs. Lists and short tables only.
- Numbers and names exactly: file paths, object names, counts.
- For right-to-left text: every line opens with a word in that language, so the direction stays correct. English names go in backticks, inside the line.
- No invisible direction characters.

## 4. Check that the developer understood

Goal: the developer understands the work, not only approves it. Light touch, never a test.

**When**
- After the plan is approved, on a task with a real decision: load pattern, keys, a migration, a deployment risk.
- At most **one** question per task. Never on a quick fix or a pure question.
- The developer says "skip" → skip, for the rest of the session.

**How**
- One short question about the **why**, not about trivia.
- 2–4 options, one right, the others plausible. Use the tool's choice buttons when it has them.
- Friendly, one line of lead-in at most: "שאלה קטנה לפני שממשיכים:".
- Right answer → one line that confirms, continue.
- Wrong answer → two or three short lines that explain, no judgement, continue. Never block the work.

**Example**
```
שאלה קטנה לפני שממשיכים:
למה כל שינוי בטבלה מקבל גם קובץ migration ממוספר?
1. כי בסיס הנתונים לא מאפשר לשנות טבלה בלי קובץ.
2. כי כך כל סביבה מגיעה לאותו מצב, באותו סדר.
3. כי הקובץ של הטבלה לא נשמר ב-Git.
```
Right answer: 2. Explanation if wrong: "קובץ הטבלה מתאר איך הטבלה צריכה להיראות." / "קובץ ה-migration מתאר איך כל סביבה מגיעה לשם." / "כל סביבה מריצה את קבצי ה-migration לפי המספר."

## 5. Example plan

```
מה נעשה:
- בונים את הטבלה `GOLD.SALES_DIM_CUSTOMER` מה-STT המאושר.

מה משתנה:
- קובץ חדש: `db/GOLD/Tables/SALES_DIM_CUSTOMER.sql`.
- קובץ חדש: `db/SILVER/Procedures/SP_SALES_DIM_CUSTOMER.sql`.
- קובץ חדש: `scripts/migrations/0012_add_sales_dim_customer.sql`.
- קובץ בדיקות חדש: `qa/data/SALES_DIM_CUSTOMER.sql`.

איך נדע שזה עבד:
- הטבלה `GOLD.SALES_DIM_CUSTOMER` לא ריקה.
- אין לקוח שמופיע פעמיים בטבלה `GOLD.SALES_DIM_CUSTOMER`.
- הרצה שנייה של הטעינה נותנת אותו מספר שורות.

מי מריץ:
- את ה-migration ואת הבדיקות מריץ המפתח, לפי דף ההרצה שאכין.

מה לא נוגעים:
- לא נוגעים ב-TEST וב-PROD.

לאישורך:
- האם לקוח שנסגר נשאר בטבלה, עם תאריך סגירה?
```

On Microsoft Fabric (`_context/platform.md` §2): the example plan and question are in `references/fabric.md`.
