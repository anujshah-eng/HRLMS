from pydantic import BaseModel, Field

# Real-time Interview Session DTOs
class CreateInterviewSessionDTO(BaseModel):
    """Step 1: Create interview session with basic setup"""
    role_title: str = Field(..., description="Selected role title")
    interview_round_id: int = Field(..., description="Selected interview round ID")
    skills: list[str] | None = Field(None, description="List of skills")
    questions: list[dict] | None = Field(None, description="List of questions")

class UpdateSessionContextDTO(BaseModel):
    """Step 2: Add context (resume, company, job description)"""
    company_id: int | None = Field(None, description="Target company ID")
    resume_url: str | None = Field(None, max_length=500, description="S3 URL of uploaded resume")
    job_description: str | None = Field(None, max_length=2000, description="Job description text")

class UpdateSessionOptionsDTO(BaseModel):
    """Step 3: Choose duration and interviewer"""
    duration_minutes: int = Field(..., ge=5, le=30, description="Interview duration (5, 10, 20, 30)")
    avatar_id: int = Field(..., description="Selected avatar/interviewer ID")
    number_of_questions: int | None = Field(None, ge=1, le=20, description="Number of questions")
    difficulty: str = Field("Medium", pattern="^(Easy|Medium|Hard)$")

class DeviceCheckDTO(BaseModel):
    """Step 4: Update device check status"""
    camera_test_status: bool = Field(..., description="Camera test passed")
    microphone_test_status: bool = Field(..., description="Microphone test passed")

class SubmitAnswerDTO(BaseModel):
    """Submit answer during interview"""
    question_index: int = Field(..., ge=0, description="Index of the question being answered")
    audio_transcription: str = Field(..., max_length=5000, description="Transcribed audio answer")
    answer_duration_seconds: float | None = Field(None, description="Time taken to answer")
