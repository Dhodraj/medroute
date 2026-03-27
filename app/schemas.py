from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class TriageLevel(str, Enum):
    """Triage levels based on clinical urgency"""
    EMERGENCY = "emergency"
    URGENT = "urgent" 
    SEMI_URGENT = "semi_urgent"
    NON_URGENT = "non_urgent"


class Symptom(BaseModel):
    """Structured symptom representation"""
    name: str = Field(..., description="Name of the symptom")
    duration: Optional[str] = Field(None, description="Duration of the symptom")
    severity: Optional[str] = Field(None, description="Severity level (mild, moderate, severe, unknown)")
    location: Optional[str] = Field(None, description="Body location if applicable")
    additional_info: Optional[str] = Field(None, description="Additional context about the symptom")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Symptom name cannot be empty")
        return v.strip().lower()

    @validator('severity')
    def validate_severity(cls, v):
        if v is not None:
            allowed_severities = ['mild', 'moderate', 'severe', 'unknown']
            if v.lower() not in allowed_severities:
                return 'unknown'
            return v.lower()
        return v


class TriageRequest(BaseModel):
    """Request model for triage endpoint"""
    query: str = Field(..., min_length=1, max_length=2000, description="Free-text health complaint")

    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Query cannot be empty")
        return v.strip()


class TriageResponse(BaseModel):
    """Response model for triage endpoint"""
    input: str = Field(..., description="Original input query")
    symptoms: List[Symptom] = Field(default_factory=list, description="Extracted symptoms")
    triage_level: TriageLevel = Field(..., description="Assigned triage level")
    recommendation: str = Field(..., description="Recommendation text")
    disclaimer: str = Field(
        default="This is not a medical diagnosis. Consult a licensed doctor.",
        description="Medical disclaimer"
    )
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in triage decision")
    processing_time_ms: Optional[int] = Field(None, description="Total processing time in milliseconds")


class AgentInput(BaseModel):
    """Base input model for agent processing"""
    query: str
    symptoms: List[Symptom] = Field(default_factory=list)
    triage_level: Optional[TriageLevel] = None
    recommendation: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        # Removed use_enum_values to keep enums as enum objects
        pass


class AgentOutput(BaseModel):
    """Base output model for agent processing"""
    query: str
    symptoms: List[Symptom] = Field(default_factory=list)
    triage_level: Optional[TriageLevel] = None
    recommendation: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        # Keep enums as enum objects for internal processing
        pass


class LogEntry(BaseModel):
    """Database log entry model"""
    id: Optional[int] = None
    input_text: str
    symptoms: str  # JSON string representation
    triage_level: str
    recommendation: str
    confidence_score: Optional[float] = None
    llm_model_version: str = Field(alias="model_version")  # Avoid protected namespace
    processing_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        protected_namespaces = ()
