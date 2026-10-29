from .database import Base, engine, SessionLocal
from .models import Application, ComplianceRule, Document, AuditEvent
Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if db.query(Application).count() == 0:
        samples = [
            ("VRQ-2026-001", "Avery Morgan", "Business registration", "Verified", "Low", 8),
            ("VRQ-2026-002", "Jordan Lee", "Identity review", "Incomplete", "High", 65),
            ("VRQ-2026-003", "Taylor Quinn", "Permit application", "Needs Review", "Medium", 49),
            ("VRQ-2026-004", "Casey Rowan", "Vendor onboarding", "Needs Review", "Medium", 42),
            ("VRQ-2026-005", "Morgan Ellis", "Grant application", "Incomplete", "High", 70),
        ]
        for ref, name, cat, status, risk, score in samples:
            a = Application(reference=ref, applicant_name=name, category=cat, document_category="Supporting documents",
                            jurisdiction="Illustrative profile", status=status, risk_level=risk, risk_score=score)
            db.add(a)
        db.flush()
        for rule_id, name, desc, sev in [
            ("DOC-001", "Supporting document present", "At least one supporting document is attached.", "high"),
            ("OCR-001", "Readable text available", "Extractable text is available for review.", "medium"),
            ("MATCH-001", "Applicant name consistency", "Applicant name appears in extracted document text.", "medium"),
            ("DATE-001", "Expiry indicator", "Simple expired-date indicators are screened; manual confirmation required.", "low"),
            ("DOC-002", "Illustrative file requirement", "Example rule only; not a legal requirement.", "medium"),
        ]:
            db.add(ComplianceRule(rule_id=rule_id, name=name, description=desc, severity=sev, version="1.0", enabled=True))
        db.add(AuditEvent(actor="seed-script", action="demo.seeded", detail="Synthetic demo records created"))
        db.commit()
finally:
    db.close()
if __name__ == "__main__":
    print("Seed complete. Synthetic demo data is ready.")
