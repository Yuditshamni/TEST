---
name: nogamy-client-readout
description: Read any document, answer, email or presentation for the client through the eyes of a non-technical stakeholder before it is sent — where they get lost, what they will ask, what is missing to say yes — and fix the language. Use before anything leaves the team.
---

# Client read-out

**Fresh eye.** For a deliverable that matters (a report, a sign-off, a presentation), also run the agent `nogamy-client-reviewer` on it. It reads only the deliverable and `PROJECT.md`, as the client would, and returns send / send after fixes / do not send. Add its findings to this output.

## Read it as the client

The reader is a business manager or a BI owner at the client. They do not know SCD, merge, medallion, or the name of any tool.

Answer these five, one line each:
1. How long will it take?
2. What happens if it fails at night? Who knows, who fixes?
3. Why do we need this? What do we get?
4. Who maintains it when the developer is not here?
5. What do I tell my management?

Then:
- **Lost at:** the first sentence where a non-technical reader stops understanding.
- **Missing to say yes:** one line.
- **The question they will ask in the meeting:** one line.

## Fix the text

- The client's language (`PROJECT.md`), in its writing direction. Field and object names in English, inside the sentence.
- Short lines. One idea per line. Each line understandable alone (`nogamy-plan-and-explain`).
- Every technical term gets plain words, or goes.
- Numbers with their meaning ("3,412 לקוחות פעילים ב-30/09"), never alone.
- Deliverable style: `_context/working-agreement.md` → Deliverables.
- Nothing internal: no commentary on people, no Nogamy-only notes, no sensitive data.

## Output

The five answers, the three lines above, the agent's verdict when it ran, then the corrected text.
