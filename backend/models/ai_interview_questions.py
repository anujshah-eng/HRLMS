from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from bson import ObjectId
from enums.ai_interview import InterviewStatus, InterviewLevel


# Helper for MongoDB ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        
        def validate(value):
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)
        
        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            )
        )

class Question(BaseModel):
    question_id: str
    question_text: str
    expected_answer: Optional[str] = None
    order: int
    topic: Optional[str] = None

class Interview(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    role_id: int
    company_id: int
    interview_round: Optional[str] = None
    resume_url: Optional[str] = None
    # target_company: Optional[str] = None
    job_description: Optional[str] = None
    number_of_questions: Optional[int] = None
    interviewer_name: Optional[str] = None
    camera_test_status: Optional[bool] = False
    microphone_test_status: Optional[bool] = False
    difficulty: InterviewLevel
    status: Optional[InterviewStatus]
    score: Optional[float] = 0.0
    questions: Optional[List[Question]] = []

    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Config:
        json_encoders = {ObjectId: str}
        from_attributes = True
