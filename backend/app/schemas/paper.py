"""
Paper Generation System - Pydantic Schema

Contains:
1. PaperConstraints - Generation constraints
2. PaperCreate - Create paper
3. PaperUpdate - Update paper
4. PaperResponse - Response models
5. PaperGenerateRequest - Generation request
6. DiagnosticGenerateRequest - Diagnostic generation request
7. ABPaperResponse - A/B paper response
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class PaperType(str, Enum):
    """Paper type enum"""
    NORMAL = "normal"
    DIAGNOSTIC = "diagnostic"
    EXAM = "exam"


class GenerationMode(str, Enum):
    """Generation mode enum"""
    MANUAL = "manual"
    AI = "ai"
    GREEDY = "greedy"
    DIAGNOSTIC = "diagnostic"


class PaperStatus(str, Enum):
    """Paper status enum"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PaperGenerationError(Exception):
    """Paper generation error"""
    
    def __init__(self, message: str, code: str = "PAPER_GENERATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"


class PaperConstraints(BaseModel):
    """Paper generation constraints"""
    total_count: int = Field(..., ge=1, le=200, description="Total question count")
    total_score: float = Field(100.0, ge=1, le=1000, description="Total score")
    estimated_time: Optional[int] = Field(None, ge=1, le=300, description="Estimated time in minutes")
    
    # Knowledge point constraints
    target_knowledge_points: List[str] = Field(default_factory=list, description="Target knowledge points")
    exclude_knowledge_points: List[str] = Field(default_factory=list, description="Excluded knowledge points")
    
    # Difficulty constraints (supports both int and str keys for compatibility)
    difficulty_distribution: Optional[Dict[str, float]] = Field(
        None, 
        description="Difficulty distribution {1: 0.2, 2: 0.4, 3: 0.3, 4: 0.1}"
    )
    target_difficulty: Optional[float] = Field(None, ge=1, le=5, description="Target difficulty")
    
    # Question type constraints
    question_type_counts: Optional[Dict[str, int]] = Field(
        None,
        description="Question type counts {single: 10, fill: 5}"
    )
    
    # Cognitive level constraints
    cognitive_levels: Optional[List[str]] = Field(
        None,
        description="Required cognitive levels L1-L6"
    )
    
    # Other constraints
    min_usage_count: int = Field(0, ge=0, description="Minimum usage count")
    max_usage_count: Optional[int] = Field(None, ge=0, description="Maximum usage count")
    require_reviewed: bool = Field(True, description="Only select reviewed questions")
    
    @field_validator('difficulty_distribution', mode='before')
    @classmethod
    def convert_int_keys_to_str(cls, v):
        """Convert int keys to strings for compatibility"""
        if v is None:
            return None
        if isinstance(v, dict):
            return {str(k): float(val) for k, val in v.items()}
        return v
    
    @model_validator(mode='after')
    def validate_difficulty_distribution(self):
        """Validate difficulty distribution sum"""
        if self.difficulty_distribution:
            total = sum(self.difficulty_distribution.values())
            if abs(total - 1.0) > 0.01:
                raise PaperGenerationError(
                    f"Difficulty distribution must sum to 1, got {total}",
                    code="INVALID_DIFFICULTY_DISTRIBUTION"
                )
        return self
    
    @model_validator(mode='after')
    def validate_question_type_counts(self):
        """Validate question type counts"""
        if self.question_type_counts:
            total = sum(self.question_type_counts.values())
            if total > self.total_count:
                raise PaperGenerationError(
                    f"Question type counts sum ({total}) exceeds total count ({self.total_count})",
                    code="QUESTION_TYPE_COUNT_CONFLICT"
                )
        return self
    
    def validate_conflicts(self) -> None:
        """Validate constraint conflicts"""
        if self.question_type_counts:
            type_count = sum(self.question_type_counts.values())
            if type_count > self.total_count:
                raise PaperGenerationError(
                    f"Question type count ({type_count}) exceeds total count ({self.total_count})"
                )
            # Check for exact match - partial counts are allowed but warn
            if type_count < self.total_count:
                raise PaperGenerationError(
                    f"Question type counts sum ({type_count}) is less than total count ({self.total_count})"
                )


class PaperCreate(BaseModel):
    """Create paper request"""
    title: str = Field(..., min_length=1, max_length=200, description="Paper title")
    subject: Optional[str] = Field(None, max_length=50, description="Subject")
    grade_level: Optional[str] = Field(None, max_length=20, description="Grade level")
    paper_type: PaperType = Field(PaperType.NORMAL, description="Paper type")
    generation_mode: GenerationMode = Field(GenerationMode.MANUAL, description="Generation mode")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Generation constraints")
    
    # Diagnostic paper specific
    source_student_id: Optional[UUID] = Field(None, description="Source student ID")
    source_diagnosis: Optional[Dict[str, Any]] = Field(None, description="Diagnosis report reference")


class PaperUpdate(BaseModel):
    """Update paper request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[PaperStatus] = None
    constraints: Optional[Dict[str, Any]] = None
    question_ids: Optional[List[UUID]] = None


class PaperQuestionItem(BaseModel):
    """Paper question item"""
    id: UUID
    order: int
    content: str
    question_type: str
    options: Optional[List[Dict[str, Any]]] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    difficulty: int
    cognitive_level: Optional[str] = None
    score: float
    knowledge_points: List[str] = []


class PaperResponse(BaseModel):
    """Paper response"""
    id: UUID
    title: str
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    paper_type: Optional[str] = "normal"
    generation_mode: Optional[str] = "manual"
    question_count: int = 0
    total_score: float = 100.0
    estimated_time: Optional[int] = None
    difficulty_distribution: Optional[Dict[str, float]] = None
    knowledge_coverage: Optional[Dict[str, float]] = None
    cognitive_distribution: Optional[Dict[str, float]] = None
    is_paired: bool = False
    paired_paper_id: Optional[UUID] = None
    status: Optional[str] = "draft"
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    @field_validator('difficulty_distribution', mode='before')
    @classmethod
    def convert_int_keys_to_str(cls, v):
        """Convert int keys to strings for compatibility"""
        if v is None:
            return None
        if isinstance(v, dict):
            return {str(k): float(val) for k, val in v.items()}
        return v
    
    model_config = {"from_attributes": True}


class PaperListItem(BaseModel):
    """Paper list item"""
    id: UUID
    title: str
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    paper_type: Optional[str] = "normal"
    question_count: int = 0
    total_score: float = 100.0
    status: Optional[str] = "draft"
    created_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class PaperListResponse(BaseModel):
    """Paper list response"""
    items: List[PaperListItem]
    total: int
    page: int
    page_size: int


class PaperWithQuestions(BaseModel):
    """Paper with questions response"""
    id: UUID
    title: str
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    paper_type: Optional[str] = "normal"
    questions: List[Dict[str, Any]] = []
    total_score: float = 100.0
    estimated_time: Optional[int] = None
    difficulty_distribution: Optional[Dict[str, float]] = None
    knowledge_coverage: Optional[Dict[str, float]] = None
    created_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class PaperGenerateRequest(BaseModel):
    """Paper generation request"""
    title: str = Field(..., min_length=1, max_length=200, description="Paper title")
    subject: Optional[str] = Field(None, max_length=50, description="Subject")
    grade_level: Optional[str] = Field(None, max_length=20, description="Grade level")
    paper_type: PaperType = Field(PaperType.NORMAL, description="Paper type")
    generation_mode: GenerationMode = Field(GenerationMode.GREEDY, description="Generation mode")
    
    # Core constraints
    total_count: int = Field(..., ge=1, le=200, description="Total question count")
    total_score: float = Field(100.0, ge=1, le=1000, description="Total score")
    estimated_time: Optional[int] = Field(None, ge=1, le=300, description="Estimated time in minutes")
    
    # Knowledge point constraints
    target_knowledge_points: List[str] = Field(default_factory=list, description="Target knowledge points")
    exclude_knowledge_points: List[str] = Field(default_factory=list, description="Excluded knowledge points")
    
    # Difficulty constraints
    difficulty_distribution: Optional[Dict[str, float]] = Field(None, description="Difficulty distribution")
    target_difficulty: Optional[float] = Field(None, ge=1, le=5, description="Target difficulty")
    
    # Question type constraints
    question_type_counts: Optional[Dict[str, int]] = Field(None, description="Question type counts")
    
    # Cognitive level constraints
    cognitive_levels: Optional[List[str]] = Field(None, description="Cognitive levels")
    
    @model_validator(mode='after')
    def validate_constraints(self):
        """Validate constraints"""
        if self.difficulty_distribution:
            total = sum(self.difficulty_distribution.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Difficulty distribution must sum to 1, got {total}")
        return self
    
    def validate_conflicts(self) -> List[str]:
        """Validate constraint conflicts and return warnings"""
        warnings = []
        if self.question_type_counts:
            type_count = sum(self.question_type_counts.values())
            if type_count > self.total_count:
                warnings.append(
                    f"Question type count ({type_count}) exceeds total count ({self.total_count}) - conflict detected"
                )
            if type_count < self.total_count:
                warnings.append(
                    f"Question type counts sum ({type_count}) is less than total count ({self.total_count})"
                )
        return warnings


class DiagnosticGenerateRequest(BaseModel):
    """Diagnostic paper generation request"""
    title: str = Field(..., min_length=1, max_length=200, description="Paper title")
    subject: Optional[str] = Field(None, max_length=50, description="Subject")
    grade_level: Optional[str] = Field(None, max_length=20, description="Grade level")
    student_id: UUID = Field(..., description="Student ID")
    
    # Diagnosis report
    diagnosis_report: Dict[str, Any] = Field(..., description="Diagnosis report")
    
    # Basic constraints
    total_count: int = Field(20, ge=1, le=200, description="Total question count")
    total_score: float = Field(100.0, ge=1, le=1000, description="Total score")
    
    @property
    def weak_points(self) -> List[str]:
        """Extract weak knowledge points"""
        return self.diagnosis_report.get("weak_points", [])
    
    @property
    def mastery_levels(self) -> Dict[str, float]:
        """Get mastery levels"""
        return self.diagnosis_report.get("mastery_levels", {})


class ABPaperRequest(BaseModel):
    """A/B paper generation request"""
    paper_id: UUID = Field(..., description="A paper ID")
    title_b: Optional[str] = Field(None, description="B paper title")
    preserve_order: bool = Field(True, description="Preserve question order")
    max_similarity: float = Field(0.6, ge=0, le=1, description="Maximum similarity threshold")


class ABPaperResponse(BaseModel):
    """A/B paper response"""
    paper_a: PaperResponse
    paper_b: PaperResponse
    similarity_score: float = 0.0
    questions_replaced: int = 0


class PaperStatistics(BaseModel):
    """Paper statistics"""
    total: int
    published: int
    draft: int
    archived: int
    by_type: Dict[str, int]
    by_subject: Dict[str, int]
    avg_question_count: float
    avg_difficulty: Optional[float] = None


class PaperGenerationResult(BaseModel):
    """Paper generation result"""
    paper: Optional[PaperResponse] = None
    questions: List[Dict[str, Any]] = []
    difficulty_distribution: Dict[str, float] = {}
    knowledge_coverage: Dict[str, float] = {}
    cognitive_distribution: Dict[str, float] = {}
    warnings: List[str] = []
    
    @field_validator('difficulty_distribution', mode='before')
    @classmethod
    def convert_int_keys_to_str(cls, v):
        """Convert int keys to strings for compatibility"""
        if v is None:
            return {}
        if isinstance(v, dict):
            return {str(k): float(val) for k, val in v.items()}
        return v
    
    model_config = {"from_attributes": True}


class PaperExportFormat(str, Enum):
    """Export format"""
    PDF = "pdf"
    WORD = "word"
    JSON = "json"
    MARKDOWN = "markdown"


class PaperExportRequest(BaseModel):
    """Export request"""
    paper_id: UUID
    format: PaperExportFormat = PaperExportFormat.PDF
    include_answers: bool = True
    include_analysis: bool = True
    include_scores: bool = True
