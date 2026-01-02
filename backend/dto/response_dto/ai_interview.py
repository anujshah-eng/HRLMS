from pydantic import BaseModel, field_serializer
from datetime import datetime
from uuid import UUID

class AIInterviewRoleResponseDTO(BaseModel):
    id: int
    title: str
    description: str | None

    class Config:
        from_attributes = True

class InterviewQuestionResponseDTO(BaseModel):
    id: int
    question_text: str
    topic: str | None
    role_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True

# Real-time Interview Session Response DTOs
class InterviewSessionResponseDTO(BaseModel):
    """Response for interview session"""
    id: int
    session_id: str
    user_id: UUID | str  # Accept both UUID and string
    role_id: int
    company_id: int | None
    interview_round_id: int
    avatar_id: int
    duration_minutes: int
    number_of_questions: int
    difficulty: str
    resume_url: str | None
    job_description: str | None
    camera_test_status: bool
    microphone_test_status: bool
    status: str
    current_question_index: int
    started_at: datetime | None
    completed_at: datetime | None
    mongodb_interview_id: str | None
    overall_score: float | None
    communication_score: float | None
    technical_score: float | None
    confidence_score: float | None
    structure_score: float | None
    created_at: datetime
    updated_at: datetime

    @field_serializer('user_id')
    def serialize_user_id(self, user_id: UUID | str, _info):
        """Convert UUID to string for JSON serialization"""
        return str(user_id)

    class Config:
        from_attributes = True

class QuestionResponseDTO(BaseModel):
    """Individual question in interview"""
    question_id: str
    question_text: str
    order: int
    topic: str | None

class InterviewQuestionSetDTO(BaseModel):
    """Set of questions generated for interview"""
    session_id: str
    questions: list[QuestionResponseDTO]
    total_questions: int

class PerformanceBreakdownDTO(BaseModel):
    """Performance breakdown scores"""
    communication_score: float
    technical_score: float
    confidence_score: float
    structure_score: float

class QuestionFeedbackDTO(BaseModel):
    """Feedback for individual question"""
    question: QuestionResponseDTO
    user_answer: str
    score: float
    feedback_label: str  # Excellent, Good, Fair, Poor
    what_went_well: str
    areas_to_improve: str
    improved_answer: str | None

class InterviewReportDTO(BaseModel):
    """Complete interview performance report"""
    session_id: str
    role: str
    interview_round: str
    duration_minutes: int
    completed_at: datetime
    overall_score: float
    overall_percentage: float
    performance_breakdown: PerformanceBreakdownDTO
    key_strengths: list[str]
    focus_areas: list[str]
    question_feedbacks: list[QuestionFeedbackDTO]
    recommended_next_steps: list[str] | None

class InterviewerDTO(BaseModel):
    """Interviewer voice model information"""
    id: str
    name: str
    voice_id: str
    gender: str  # "male" or "female"
    accent: str | None
    description: str | None

class InterviewHistoryItemDTO(BaseModel):
    """Single interview history item"""
    session_id: str
    role_title: str
    company_name: str | None
    interviewer_name: str
    interviewer_initials: str
    interview_round: str
    interview_date: datetime
    duration_minutes: int
    overall_score: int | None  # Total score out of 100
    status: str  # "completed", "in_progress", "evaluated"

    class Config:
        from_attributes = True

class InterviewHistoryResponseDTO(BaseModel):
    """Paginated interview history response"""
    interviews: list[InterviewHistoryItemDTO]
    total_count: int
    page: int
    page_size: int
    has_more: bool
