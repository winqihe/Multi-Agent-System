"""Shared models for multi-agent system."""

from typing import TypedDict, Literal, Optional, List
from pydantic import BaseModel, Field


# LangGraph State Definition
class CourseState(TypedDict):
    """Shared state for LangGraph orchestration."""
    topic: str
    iteration: int
    research_output: Optional[str]
    research_sources: Optional[List[str]]
    judge_status: Optional[Literal["pass", "fail"]]
    judge_feedback: Optional[str]
    judge_score: Optional[float]
    final_course: Optional[str]
    max_iterations: int


# Pydantic Models for API Request/Response

class ResearchRequest(BaseModel):
    """Request for Researcher Agent."""
    topic: str
    previous_feedback: Optional[str] = None


class ResearchResponse(BaseModel):
    """Response from Researcher Agent."""
    research_output: str
    sources: List[str] = Field(default_factory=list)


class JudgeRequest(BaseModel):
    """Request for Judge Agent."""
    topic: str
    research_output: str


class JudgeResponse(BaseModel):
    """Response from Judge Agent."""
    status: Literal["pass", "fail"]
    feedback: str
    score: float = Field(ge=0.0, le=1.0)


class ContentRequest(BaseModel):
    """Request for Content Builder Agent."""
    topic: str
    research_output: str


class ContentResponse(BaseModel):
    """Response from Content Builder Agent."""
    course_content: str
    format: str = "markdown"


class ChatRequest(BaseModel):
    """Request for App chat endpoint."""
    message: str
    user_id: str = "default_user"
    session_id: Optional[str] = None


class ProgressEvent(BaseModel):
    """SSE progress event."""
    type: Literal["progress", "result", "error", "chunk"]
    agent: Optional[str] = None
    message: Optional[str] = None
    course: Optional[str] = None
    error: Optional[str] = None
    content: Optional[str] = None