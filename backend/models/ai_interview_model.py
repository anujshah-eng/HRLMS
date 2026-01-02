from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from models import Base

class AIInterviewRoles(Base):
    __tablename__ = "ai_interview_roles" 

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=E1102
    # created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # pylint: disable=E1102
    # updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    def __repr__(self):
        return f"<AIInterviewRoles(id={self.id}, title='{self.title}')>"

class AIInterviewers(Base):
    __tablename__ = "ai_interviewers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    voice_id = Column(String(50), nullable=False)  # OpenAI voice model (alloy, echo, shimmer, etc.)
    gender = Column(String(10), nullable=False)  # male or female
    accent = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)
    greet_video = Column(String(500), nullable=True)
    video_blink_1 = Column(String(500), nullable=True)
    video_blink_2 = Column(String(500), nullable=True)
    video_dubb = Column(String(500), nullable=True)
    img = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=E1102
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # pylint: disable=E1102

    def __repr__(self):
        return f"<AIInterviewers(id={self.id}, name='{self.name}', voice_id='{self.voice_id}')>"

class AIInterviewQuestions(Base):
    __tablename__ = "ai_interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String(2000), nullable=False)
    topic = Column(String(100), nullable=True)
    role_id = Column(Integer, nullable=True)  # Can link to specific role
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=E1102
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # pylint: disable=E1102

    def __repr__(self):
        return f"<AIInterviewQuestions(id={self.id}, question_text='{self.question_text[:50]}...')>"
