from datetime import datetime, timezone
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".png", ".jpg", ".jpeg"}
MAX_BYTES_DEFAULT = 10 * 1024 * 1024

def extract_text(path: Path, extension: str):
    if extension == ".txt":
        try:
            return path.read_text(encoding="utf-8", errors="replace"), "completed"
        except OSError:
            return None, "failed"
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages).strip()
            return (text, "completed") if text else (None, "no_text_found")
        except Exception:
            return None, "failed"
    return None, "skipped_ocr_unavailable"

def run_checks(application, documents, rules):
    checks = []
    def add(rule_id, title, status, severity, explanation):
        checks.append({"rule_id": rule_id, "rule_version": "1.0", "title": title,
                       "status": status, "severity": severity, "explanation": explanation})
    if not documents:
        add("DOC-001", "Supporting document present", "failed", "high",
            "No document is attached. Upload at least one supported document.")
    else:
        add("DOC-001", "Supporting document present", "passed", "info",
            f"{len(documents)} document(s) are attached.")
    if not documents or not any(d.extracted_text and d.extracted_text.strip() for d in documents):
        add("OCR-001", "Readable text available", "review", "medium",
            "No extractable text is available. Image OCR is not configured; a reviewer should inspect the file.")
    else:
        add("OCR-001", "Readable text available", "passed", "info",
            "Text was extracted from at least one document using the configured local parser.")
    text = "\n".join((d.extracted_text or "") for d in documents).lower()
    name = application.applicant_name.lower().strip()
    if name and text and name in text:
        add("MATCH-001", "Applicant name consistency", "passed", "info",
            "Applicant name appears in extracted text. This is a text match, not identity verification.")
    elif text:
        add("MATCH-001", "Applicant name consistency", "review", "medium",
            "Applicant name was not found as an exact substring in extracted text; formatting or OCR limitations may explain this.")
    else:
        add("MATCH-001", "Applicant name consistency", "skipped", "info",
            "Skipped because no document text was available.")
    if "expired" in text or "expiry date: 2020" in text or "expiry: 2020" in text:
        add("DATE-001", "Expiry indicator", "failed", "high",
            "Text contains a simple expiry indicator that may be outdated. Confirm the actual date manually.")
    else:
        add("DATE-001", "Expiry indicator", "review", "low",
            "No reliable expiry-date parser is configured. This check cannot confirm validity.")
    for rule in rules:
        if not rule.enabled:
            continue
        if rule.rule_id == "DOC-002":
            status = "passed" if documents else "failed"
            explanation = "Illustrative rule: at least one supporting file is attached." if documents else "Illustrative rule failed: no supporting file is attached."
            add(rule.rule_id, rule.name, status, rule.severity, explanation)
    return checks

def summarize(checks):
    failed = sum(c["status"] == "failed" for c in checks)
    review = sum(c["status"] == "review" for c in checks)
    if failed:
        return "Incomplete", "High", min(95, 45 + failed * 15 + review * 5)
    if review:
        return "Needs Review", "Medium", min(75, 25 + review * 12)
    return "Verified", "Low", 8
