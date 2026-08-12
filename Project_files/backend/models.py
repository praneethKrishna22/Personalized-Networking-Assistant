"""Pydantic schemas used by the FastAPI backend."""
from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateStartersRequest(BaseModel):
    event_description: str = Field(..., min_length=3, description="Description of the event/topic")
    interests: List[str] = Field(default_factory=list, description="User's stated interests")
    num_starters: int = Field(3, ge=1, le=5, description="How many conversation starters to return")


class StarterItem(BaseModel):
    id: int
    starter: str


class GenerateStartersResponse(BaseModel):
    themes: List[str]
    starters: List[StarterItem]


class FactCheckRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Topic or claim to verify")


class FactCheckResponse(BaseModel):
    query: str
    found: bool
    summary: Optional[str] = None
    url: Optional[str] = None
    options: List[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    history_id: int
    useful: bool


class HistoryItem(BaseModel):
    id: int
    event_description: str
    interests: str
    themes: str
    starter: str
    useful: Optional[bool] = None
    created_at: str
