from sqlalchemy.orm import declarative_base
Base = declarative_base()

from models import ai_interview_model, ai_interview_conversation, ai_interview_questions  # noqa: F401