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
    patch_category: Optional[str] = None


class SystemicPattern(BaseModel):
    pattern: str
    category: str
    severity: str
    affected_files: List[str]
    why_it_matters: str


class TopRisk(BaseModel):
    title: str
    severity: str
    description: str
    affected_files: List[str]


class PriorityRecommendation(BaseModel):
    priority: int
    action: str
    reason: str


class CriticalAnalysis(BaseModel):
    systemic_patterns: List[SystemicPattern] = []
    top_risk: Optional[TopRisk] = None
    priority_recommendations: List[PriorityRecommendation] = []


class RepoAnalysisResponse(BaseModel):
    repo_url: str
    health_score: int
    files_analyzed: int
    total_files_found: int
    repository_intelligence: RepositoryIntelligence
    issues: Dict[str, List[Dict[str, Any]]]
    severity_counts: SeverityCounts
    pr_summary: PRSummary
    critical_analysis: CriticalAnalysis
    file_results: List[FileResult]


class FileInventory(BaseModel):
    total_files: int = 0
    by_extension: Dict[str, int] = {}
    supported: int = 0
    skipped_unsupported_type: int = 0
    skipped_oversized: int = 0
    skipped_unreadable: int = 0


class AnalyzeRepoStartResponse(BaseModel):
    """Immediate response from POST /analyze-repo — returns before the repo is
    even cloned (cloning is network-bound and must never block this response).
    Poll GET /analysis/{analysis_id}/status for file_inventory and progress."""
    analysis_id: str


class AnalysisProgress(BaseModel):
    done: int
    total: int
    current_file: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str  # "cloning" | "running" | "complete" | "failed"
    file_inventory: Optional[FileInventory] = None  # null while still cloning
    total_files_found: Optional[int] = None
    progress: AnalysisProgress
    estimated_seconds_remaining: int = 0
    error: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
