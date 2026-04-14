from typing import List, Optional
from pydantic import BaseModel, HttpUrl, ConfigDict
from datetime import datetime


class AnalysisBase(BaseModel):
    repo_owner: str
    repo_name: str
    pull_number: int


class AnalysisCreate(AnalysisBase):
    user_id: int
    overall_summary: Optional[str] = None
    overall_risk_score: Optional[float] = None
    final_recommendation: Optional[str] = None
    status: str = "pending"


class AnalysisUpdate(BaseModel):
    overall_summary: Optional[str] = None
    overall_risk_score: Optional[float] = None
    final_recommendation: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    is_notified: Optional[bool] = None


class AnalysisIssue(BaseModel):
    description: str
    snippet: str = ""


class AnalysisReviewBase(BaseModel):
    filename: str
    summary: Optional[str] = None
    issues: Optional[List[AnalysisIssue]] = None
    risk_score: Optional[float] = None


class AnalysisReviewCreate(AnalysisReviewBase):
    analysis_id: int


class AnalysisReviewResponse(AnalysisReviewBase):
    id: int
    analysis_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisResponse(AnalysisBase):
    id: int
    overall_summary: Optional[str]
    overall_risk_score: Optional[float]
    final_recommendation: Optional[str]
    num_files_analyzed: int

    model_config = ConfigDict(from_attributes=True)


class PRAnalysisRequest(BaseModel):
    pr_url: HttpUrl


class AnalysisStatusResponse(AnalysisBase):
    id: int
    status: str
    is_notified: bool
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryGrouped(BaseModel):
    repo_owner: str
    repo_name: str
    pull_number: int
    last_analysis_at: datetime
    analysis_count: int
    latest_status: str
    latest_risk_score: Optional[float] = None
    latest_analysis_id: int

    model_config = ConfigDict(from_attributes=True)


class AnalysisNotificationUpdate(BaseModel):
    is_notified: bool
