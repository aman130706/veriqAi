import csv, io, os, uuid
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .database import Base, engine, get_db
from .models import Application, Document, VerificationCheck, ComplianceRule, ReviewDecision, AuditEvent
from .schemas import ApplicationCreate, ReviewInput
from .config import settings
from .engine import ALLOWED_EXTENSIONS, extract_text, run_checks, summarize

Base.metadata.create_all(bind=engine)
storage = Path(settings.storage_dir)
storage.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="VERIQ AI API", version="1.0.0", description="Demo application and document verification API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def log(db, action, detail="", application_id=None, actor="system"):
    db.add(AuditEvent(application_id=application_id, actor=actor, action=action, detail=detail[:1000]))

def serialize(a):
    return {"id": a.id, "reference": a.reference, "applicant_name": a.applicant_name, "category": a.category,
            "document_category": a.document_category, "jurisdiction": a.jurisdiction, "status": a.status,
            "risk_level": a.risk_level, "risk_score": a.risk_score, "created_at": a.created_at.isoformat(),
            "document_count": len(a.documents)}

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "mode": "demo" if settings.demo_mode else "configured", "ai_provider": "not_configured", "ocr": "local text/PDF parser only"}

@app.get("/api/v1/applications")
def list_applications(q: str = "", status: str = "", limit: int = Query(100, ge=1, le=250), db: Session = Depends(get_db)):
    query = db.query(Application)
    if q:
        query = query.filter((Application.reference.ilike(f"%{q}%")) | (Application.applicant_name.ilike(f"%{q}%")))
    if status:
        query = query.filter(Application.status == status)
    return [serialize(a) for a in query.order_by(desc(Application.created_at)).limit(limit).all()]

@app.post("/api/v1/applications", status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    if db.query(Application).filter_by(reference=payload.reference).first():
        raise HTTPException(409, "Application reference already exists")
    a = Application(**payload.model_dump(), status="Incomplete", risk_level="Unknown")
    db.add(a); db.flush()
    log(db, "application.created", f"Application {a.reference} created", a.id, "demo-user")
    db.commit(); db.refresh(a)
    return serialize(a)

@app.get("/api/v1/applications/{application_id}")
def get_application(application_id: int, db: Session = Depends(get_db)):
    a = db.get(Application, application_id)
    if not a: raise HTTPException(404, "Application not found")
    result = serialize(a)
    result["documents"] = [{"id": d.id, "name": d.original_name, "size_bytes": d.size_bytes, "content_type": d.content_type,
                            "extraction_status": d.extraction_status, "text_available": bool(d.extracted_text)} for d in a.documents]
    result["checks"] = [{"id": c.id, "rule_id": c.rule_id, "rule_version": c.rule_version, "title": c.title,
                         "status": c.status, "severity": c.severity, "explanation": c.explanation} for c in a.checks]
    result["reviews"] = [{"id": r.id, "decision": r.decision, "note": r.note, "actor": r.actor, "created_at": r.created_at.isoformat()} for r in a.reviews]
    return result

@app.post("/api/v1/applications/{application_id}/documents", status_code=201)
async def upload_document(application_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    a = db.get(Application, application_id)
    if not a: raise HTTPException(404, "Application not found")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "Unsupported file type. Allowed: PDF, TXT, PNG, JPG.")
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
    stored = f"{uuid.uuid4().hex}{ext}"
    path = storage / stored
    path.write_bytes(data)
    text, extraction_status = extract_text(path, ext)
    d = Document(application_id=a.id, original_name=Path(file.filename or "upload").name,
                 stored_name=stored, content_type=file.content_type or "application/octet-stream",
                 size_bytes=len(data), extracted_text=text, extraction_status=extraction_status)
    db.add(d); log(db, "document.uploaded", f"Stored {d.original_name} ({len(data)} bytes); extraction={extraction_status}", a.id, "demo-user")
    db.commit(); db.refresh(d)
    return {"id": d.id, "name": d.original_name, "size_bytes": d.size_bytes, "extraction_status": d.extraction_status,
            "text_available": bool(d.extracted_text)}

@app.post("/api/v1/applications/{application_id}/verify")
def verify(application_id: int, db: Session = Depends(get_db)):
    a = db.get(Application, application_id)
    if not a: raise HTTPException(404, "Application not found")
    rules = db.query(ComplianceRule).all()
    checks = run_checks(a, a.documents, rules)
    db.query(VerificationCheck).filter_by(application_id=a.id).delete()
    for c in checks: db.add(VerificationCheck(application_id=a.id, **c))
    status, risk, score = summarize(checks)
    a.status, a.risk_level, a.risk_score = status, risk, score
    log(db, "verification.completed", f"{len(checks)} deterministic checks executed; status={status}", a.id, "verification-engine")
    db.commit(); db.refresh(a)
    return {"application": serialize(a), "checks": checks, "notice": "Deterministic screening only. No AI authenticity model or external registry was called."}

@app.post("/api/v1/applications/{application_id}/review")
def review(application_id: int, payload: ReviewInput, db: Session = Depends(get_db)):
    a = db.get(Application, application_id)
    if not a: raise HTTPException(404, "Application not found")
    if payload.decision not in {"approve", "reject", "request_information", "override_review"}:
        raise HTTPException(422, "Unsupported decision")
    if payload.decision in {"reject", "override_review"} and len(payload.note.strip()) < 8:
        raise HTTPException(422, "A documented reason of at least 8 characters is required")
    previous = a.status
    if payload.decision == "approve": a.status = "Verified"
    elif payload.decision == "reject": a.status = "Rejected"
    else: a.status = "Needs Review"
    db.add(ReviewDecision(application_id=a.id, actor=payload.actor, decision=payload.decision, note=payload.note))
    log(db, "review.decision", f"{previous} -> {a.status}; decision={payload.decision}; reason={payload.note}", a.id, payload.actor)
    db.commit()
    return {"application": serialize(a), "message": "Review decision recorded"}

@app.get("/api/v1/compliance/rules")
def get_rules(db: Session = Depends(get_db)):
    return [{"id": r.id, "rule_id": r.rule_id, "name": r.name, "description": r.description, "severity": r.severity,
             "version": r.version, "enabled": r.enabled} for r in db.query(ComplianceRule).order_by(ComplianceRule.rule_id).all()]

@app.get("/api/v1/audit-logs")
def audit_logs(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.query(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(limit).all()
    return [{"id": x.id, "application_id": x.application_id, "actor": x.actor, "action": x.action,
             "detail": x.detail, "created_at": x.created_at.isoformat()} for x in rows]

@app.get("/api/v1/reports/applications.csv")
def export_csv(db: Session = Depends(get_db)):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Reference", "Applicant", "Category", "Status", "Risk Level", "Risk Score", "Documents", "Created At"])
    for a in db.query(Application).order_by(desc(Application.created_at)).all():
        writer.writerow([a.reference, a.applicant_name, a.category, a.status, a.risk_level, a.risk_score, len(a.documents), a.created_at.isoformat()])
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=veriq-applications-report.csv"})

@app.get("/api/v1/metrics")
def metrics(db: Session = Depends(get_db)):
    apps = db.query(Application).all()
    return {"applications": len(apps), "documents": db.query(Document).count(),
            "awaiting_review": sum(a.status == "Needs Review" for a in apps),
            "verified": sum(a.status == "Verified" for a in apps),
            "pass_rate": round(100 * sum(a.status == "Verified" for a in apps) / len(apps)) if apps else 0,
            "demo": True}
