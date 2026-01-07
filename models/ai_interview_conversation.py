from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from enums.quiz_system.questions import QuestionLevel

class Question(BaseModel):
    """
    Represents a question asked during an AI interview session.

    Attributes:
        question_id (str): Unique identifier for the question.
        question_text (str): Text of the question asked.
        expected_answer (Optional[str]): Model or reference answer expected.
        order (int): Display order of the question.
    """
    question_id: str
    question_text: str
    expected_answer: Optional[str] = None
    order: int
    topic: Optional[str] = None

class Evaluation(BaseModel):
    """
    Represents detailed AI evaluation metrics for a single question.

    Attributes:
        communication_score (float): Score for communication clarity (0–10).
        confidence_score (float): Score for self-assurance (0–10).
        technical_score (float): Score for technical knowledge (0–10).
        structure_score (float): Score for logical flow and organization (0–10).
    """
    communication_score: Optional[float] = 0
    confidence_score: Optional[float] = 0
    technical_score: Optional[float] = 0
    structure_score: Optional[float] = 0

class InterviewConversationItem(BaseModel):
    """
    Represents a single conversation item in an AI interview session.

    Attributes:
        question (Question): Question asked to the user.
        user_answer (Optional[str]): The answer provided by the user.
        improved_answer (Optional[str]): AI-suggested improved version.
        score (float): Score obtained for this question.
        feedback_label (FeedbackLabel): Feedback label ("Excellent", "Good", etc.).
        what_went_well (Optional[str]): Summary of strong points in the response.
        areas_to_improve (Optional[str]): Summary of weak points to work on.
        evaluation (Evaluation): AI-generated detailed evaluation for this question.
    """
    question: Question
    user_answer: Optional[str] = None
    improved_answer: Optional[str] = None
    score: Optional[float] = 0
    feedback_label: Optional[str] = None
    what_went_well: Optional[str] = None
    areas_to_improve: Optional[str] = None
    evaluation: Optional[Evaluation] = None

class OverallInterviewEvaluation(BaseModel):
    """
    Represents the overall evaluation summary for a completed interview.

    Attributes:
        communication_score (float): Overall communication score (average/weighted).
        confidence_score (float): Overall confidence score.
        technical_score (float): Overall technical score.
        structure_score (float): Overall structure score.
        overall_score (float): Final score out of 100.
        overall_percentage (float): Final percentage score.
        key_strengths (Optional[List[str]]): List of key strengths identified.
        focus_areas (Optional[List[str]]): List of areas requiring improvement.
    """
    communication_score: Optional[float] = 0
    confidence_score: Optional[float] = 0
    technical_score: Optional[float] = 0
    structure_score: Optional[float] = 0
    overall_score: Optional[float] = 0
    overall_percentage: Optional[float] = 0
    key_strengths: Optional[List[str]] = []
    focus_areas: Optional[List[str]] = []

class InterviewConversation(BaseModel):
    """
    Represents a full AI interview session record including:
    - User's answers
    - AI evaluation for each question
    - Overall performance summary

    Attributes:
        interview_id (str): Unique identifier for the interview session.
        user_id (str): Identifier of the candidate.
        role_id (str): Identifier for the interview role (e.g., Software Engineer).
        company_id (Optional[str]): Target company ID.
        interviewee_name: Optional[str] = None: Name of the interviewee.
        interviewer_name (Optional[str]): Assigned interviewer or AI agent name.
        difficulty (InterviewDifficulty): Difficulty level of the interview.
        duration (Optional[int]): Total duration of the interview (in minutes).
        status (str): Current status (in-progress, completed, etc.).
        conversation_items (List[InterviewConversationItem]): List of all Q&A with evaluation.
        overall_evaluation (Optional[OverallInterviewEvaluation]): Summary of overall performance.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
        is_active (bool): Indicates if the record is active.
    """
    interview_id: str
    user_id: str
    role_id: str
    company_id: Optional[str] = None
    interviewee_name: Optional[str] = None
    interviewer_name: Optional[str] = None
    number_of_questions: Optional[int] = None
    difficulty: QuestionLevel
    duration: Optional[int] = None
    status: str
    conversation_items: Optional[List[InterviewConversationItem]] = None
    overall_evaluation: Optional[OverallInterviewEvaluation] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = True
