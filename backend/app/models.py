from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now():
    return datetime.now(timezone.utc)

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    applicant_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), default="General")
    document_category: Mapped[str] = mapped_column(String(100), default="Supporting documents")
    jurisdiction: Mapped[str] = mapped_column(String(100), default="Illustrative")
    status: Mapped[str] = mapped_column(String(40), default="Incomplete")
    risk_level: Mapped[str] = mapped_column(String(30), default="Unknown")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    documents: Mapped[list["Document"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    checks: Mapped[list["VerificationCheck"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    reviews: Mapped[list["ReviewDecision"]] = relationship(back_populates="application", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(40), default="not_supported")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    application: Mapped["Application"] = relationship(back_populates="documents")

class VerificationCheck(Base):
    __tablename__ = "verification_checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    rule_id: Mapped[str] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(30), default="1.0")
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(30), default="info")
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    application: Mapped["Application"] = relationship(back_populates="checks")

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(30), default="medium")
    version: Mapped[str] = mapped_column(String(30), default="1.0")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    actor: Mapped[str] = mapped_column(String(120), default="Demo Reviewer")
    decision: Mapped[str] = mapped_column(String(40))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    application: Mapped["Application"] = relationship(back_populates="reviews")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
