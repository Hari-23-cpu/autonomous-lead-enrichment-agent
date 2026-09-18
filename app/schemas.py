from typing import Optional
from pydantic import BaseModel, Field


class ContactPoint(BaseModel):
    email: str
    source_url: Optional[str] = None


class TeamMember(BaseModel):
    name: str
    role: Optional[str] = None
    linkedin_url: Optional[str] = None
    source_url: Optional[str] = None


class CompanyIntelligence(BaseModel):
    domain: str
    company_overview: str
    target_audience: str
    contact_points: list[ContactPoint] = Field(default_factory=list)
    leadership_team: list[TeamMember] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)