from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class SymptomRequest(BaseModel):
    symptoms: str


class Paper(BaseModel):
    title: str
    journal: Optional[str] = None
    year: Optional[int] = None
    summary: Optional[str] = None
    url: Optional[str] = None


class Candidate(BaseModel):
    condition_key: str
    suspected_conditions: List[str]
    recommended_departments: List[str]
    emergency: bool
    confidence: float
    confidence_label: str
    rule_id: str
    evidence: Dict[str, Any]


class TriageResponse(BaseModel):
    suspected_conditions: List[str]
    recommended_departments: List[str]
    emergency: bool
    confidence: float
    confidence_label: str
    rule_id: str
    evidence: Dict[str, Any]
    research_basis: List[Paper]
    llm_explanation: str
    disclaimer: str
    candidates: Optional[List[Candidate]] = None
