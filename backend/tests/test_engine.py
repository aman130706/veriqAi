from types import SimpleNamespace
from app.engine import summarize, run_checks

def test_summarize_flags_failed_checks():
    status, risk, score = summarize([{"status": "failed"}, {"status": "passed"}])
    assert status == "Incomplete"
    assert risk == "High"
    assert score > 0

def test_empty_documents_require_review_and_fail():
    app = SimpleNamespace(applicant_name="Demo Person")
    checks = run_checks(app, [], [])
    assert any(c["rule_id"] == "DOC-001" and c["status"] == "failed" for c in checks)
    assert any(c["rule_id"] == "OCR-001" and c["status"] == "review" for c in checks)

def test_name_match_is_only_text_match():
    app = SimpleNamespace(applicant_name="Avery Morgan")
    doc = SimpleNamespace(extracted_text="Applicant: Avery Morgan",)
    checks = run_checks(app, [doc], [])
    assert any(c["rule_id"] == "MATCH-001" and c["status"] == "passed" for c in checks)
