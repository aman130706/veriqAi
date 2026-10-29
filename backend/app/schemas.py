from pydantic import BaseModel, Field
from datetime import datetime

class ApplicationCreate(BaseModel):
    reference: str = Field(min_length=2, max_length=80)
    applicant_name: str = Field(min_length=2, max_length=200)
    category: str = "General"
    document_category: str = "Supporting documents"
    jurisdiction: str = "Illustrative"

class ReviewInput(BaseModel):
    decision: str
    note: str = ""
    actor: str = "Demo Reviewer"

class ApplicationOut(BaseModel):
    id: int
    reference: str
    applicant_name: str
    category: str
    document_category: str
    jurisdiction: str
    status: str
    risk_level: str
    risk_score: int
    created_at: datetime
    document_count: int = 0
    class Config:
        from_attributes = True
