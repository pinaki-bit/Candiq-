from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ImprovementPriority(BaseModel):
    category: str
    impact: str  # "HIGH IMPACT", "MEDIUM IMPACT", "LOW IMPACT"
    issue: str
    why_it_matters: str
    what_to_change: str
    example: Optional[str] = None


class SectionAnalysis(BaseModel):
    detected: bool
    quality_signal: str
    recommendation: Optional[str] = None
    word_count: int = 0
    bullet_count: int = 0
    has_metrics: bool = False
    has_action_verbs: bool = False


class JobAlignment(BaseModel):
    job_provided: bool
    relevance_score: Optional[float] = None
    domain_alignment: Optional[float] = None
    required_coverage: Optional[float] = None
    preferred_coverage: Optional[float] = None
    semantic_similarity: Optional[float] = None


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None


class SkillDetail(BaseModel):
    name: str
    category: str
    domain: str
    frequency: int = 1


class ExperienceDetail(BaseModel):
    total_entries: int = 0
    action_verbs_found: List[str] = []
    weak_verbs_found: List[str] = []
    metrics_found: List[str] = []
    bullet_count: int = 0
    avg_bullet_length: float = 0.0


class FormattingCheck(BaseModel):
    has_tables: bool = False
    has_images: bool = False
    has_headers_or_footers: bool = False
    has_columns: bool = False
    uses_standard_fonts: bool = True
    file_type_ok: bool = True
    issues: List[str] = []


class CandidateATSAnalysisResponse(BaseModel):
    ats_score: float
    compliance_category: str = "GOOD"
    score_breakdown: Dict[str, float]

    contact_info: ContactInfo = ContactInfo()
    
    detected_skills: List[str] = []
    skill_details: List[SkillDetail] = []
    skill_categories: Dict[str, List[str]] = {}
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    
    sections: Dict[str, SectionAnalysis]
    
    experience_analysis: ExperienceDetail = ExperienceDetail()
    formatting: FormattingCheck = FormattingCheck()
    
    improvement_priorities: List[ImprovementPriority]
    recommendations: List[str]
    critical_issues: List[str] = []
    warnings: List[str] = []
    
    job_alignment: JobAlignment
    extraction: Dict[str, Any]
    
    word_count: int = 0
    estimated_page_count: int = 1
    readability_grade: str = "Good"
