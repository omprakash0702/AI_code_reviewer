from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RepoAnalysisRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None


class RepositoryIntelligence(BaseModel):
    repo_type: str
    architecture_summary: str
    important_modules: List[str]
    detected_frameworks: List[str]
    primary_language: str


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class PRSummary(BaseModel):
    files_analyzed: int
    critical_risks: int
    main_findings: str
    recommendation: str
    recommendation_reason: str


class FileResult(BaseModel):
    filename: str
    issues: List[Dict[str, Any]]
    patch: str


class RepoAnalysisResponse(BaseModel):
    repo_url: str
    health_score: int
    files_analyzed: int
    total_files_found: int
    repository_intelligence: RepositoryIntelligence
    issues: Dict[str, List[Dict[str, Any]]]
    severity_counts: SeverityCounts
    pr_summary: PRSummary
    file_results: List[FileResult]
