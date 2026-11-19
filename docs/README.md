# docs/ — critical documents

The one place in Git where Office and PDF files are allowed.
For final documents that were signed or approved, kept to maintain the project: the architecture document, final specs, signed STT, signed test documents.
One folder; a developer may add subfolders if they want.

## Rules

- **The AI writes here only a final, signed or approved document.** Anything else it produces (drafts, versions under review, presentations, exports) goes to `_private/docs/`.
- **What a person put here stays here.** The AI never moves, renames or deletes it.
- **The AI reads this folder only when asked.** It is an archive, never a source of truth. The truth is the Markdown: `_context/`, `sources/`, `stt/`, `qa/`.
- **No real people or customer rows, no secrets:** the file is in Git.
- Allowed types: `.md`, `.pdf`, `.doc(x)`, `.xls(x)`, `.ppt(x)`. Archives, emails and HTML stay out of Git.

Owner: project lead.
