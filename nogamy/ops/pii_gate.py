"""Last gate before text leaves a project for Nogamy (feedback issues). Standard library only.

    python pii_gate.py --file issue.md [--project PROJECT.md]
    exit 0 = clean, exit 1 = blocked (reasons on stdout)

The agent already scrubs the text (`nogamy-feedback`); this gate catches what slipped through.
It blocks rather than redacts: a person rewrites the text, nothing is silently changed.
Blocked: e-mail, phone, Israeli ID-like numbers, card and IBAN numbers, GUIDs (workspace,
tenant, item IDs), IP addresses, connection strings and keys, URLs outside an allow-list,
and the client's own words listed in PROJECT.md (`Client:` and `Never in feedback:`).
"""
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    ("e-mail address", r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    ("phone number", r"(?<!\d)(?:\+972[-\s]?|0)(?:[23489]|5\d|7\d)[-\s]?\d{3}[-\s]?\d{4}(?!\d)"),
    ("ID-like number (9 digits)", r"(?<![\d.])\d{9}(?![\d.])"),
    ("card-like number", r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    ("IBAN", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    ("GUID (workspace / tenant / item id)", r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    ("IP address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ("connection string or key", r"(?i)\b(?:password|pwd|accountkey|sharedaccesskey|sharedaccesssignature|client_secret|secret|token|apikey|api_key)\s*[=:]"),
    ("connection string", r"(?i)\b(?:server|data source|initial catalog|user id)\s*=|jdbc:|odbc:"),
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
URL = re.compile(r"https?://([^/\s)>\]]+)", re.I)
URL_ALLOW = ("learn.microsoft.com", "docs.github.com", "github.com")  # github.com/<client org> is caught by the client words


def client_terms(project_md):
    """Words of this client that must never leave: `- Client: X` and `- Never in feedback: a, b`."""
    if not project_md or not Path(project_md).exists():
        return []
    terms = []
    for line in Path(project_md).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*(Client|Never in feedback)\s*:\s*(.+)", line)
        if m:
            value = re.sub(r"\(.*?\)", "", m.group(2))
            terms += [t.strip() for t in value.split(",") if t.strip() and "<" not in t]
    return [t for t in terms if len(t) >= 3]


def check(text, terms=()):
    reasons = []
    for label, pat in PATTERNS:
        for m in re.finditer(pat, text):
            reasons.append(f"{label}: `{_mask(m.group(0))}`")
    for m in URL.finditer(text):
        host = m.group(1).lower().split(":")[0]
        if not any(host == h or host.endswith("." + h) for h in URL_ALLOW):
            reasons.append(f"link outside the allow-list: `{host}`")
    low = text.lower()
    for t in terms:
        if t.lower() in low:
            reasons.append(f"client word from PROJECT.md: `{_mask(t)}`")
    return sorted(set(reasons))


def _mask(s):
    s = s.strip()
    return s if len(s) <= 4 else s[:2] + "…" + s[-2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--project", default="PROJECT.md")
    a = ap.parse_args()
    reasons = check(Path(a.file).read_text(encoding="utf-8"), client_terms(a.project))
    if reasons:
        print("Blocked: the text may contain personal or client data.")
        for r in reasons:
            print(f"- {r}")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
