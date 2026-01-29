from typing import Optional
from fastapi import APIRouter, status, Depends, Form, UploadFile, File
from dto.response_dto.response_dto import ResponseDto
from services.ai_interview_management.realtime_interview_service import RealtimeInterviewService
from custom_utilities.custom_exception import CustomException
from custom_utilities.dependencies import get_realtime_interview_collection, get_ai_interviewers_collection

router = APIRouter()
realtime_service = RealtimeInterviewService()

# Realtime Interview Endpoints
@router.post("/realtime-interview/session", response_model=ResponseDto)
async def create_ephemeral_session(
    role_title: str = Form(...),
    duration_minutes: int = Form(..., ge=5, le=30),
    interviewer_id: int = Form(...),
    front_end_session_id: int = Form(...),
    candidate_id: int = Form(...),
    token: str = Form(...),  # Authentication token from frontend
    job_description: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),  # JSON string of list[str]
    questions: Optional[str] = Form(None), # JSON string of list[dict]
    microphone_status: bool = Form(...),
    camera_status: bool = Form(...),
    passing_score: Optional[int] = Form(None), # Capture passing score from frontend
    # internet_status: bool = Form(...),
    # internet_speed_mbps: Optional[float] = Form(None),
    
    mongodb_collection = Depends(get_realtime_interview_collection),
    ai_interviewers_collection = Depends(get_ai_interviewers_collection)
):
    """
    Create an ephemeral session token for OpenAI Realtime API.

    **IMPORTANT**: Call /check-compatibility FIRST to validate devices before calling this.

    **Required Compatibility:**
    - microphone_status: MUST be true
    - camera_status: MUST be true

    **If ANY compatibility check fails, session will NOT be created.**

    **Optional Configuration:**
    - skills: JSON list of skills (e.g. ["React", "Python"])
    - questions: JSON list of questions (e.g. [{"type": "short_answer", "question": "..."}])
    - job_description: Text description of the job
    
    This endpoint:
    1. Optionally validates compatibility (if params provided)
    2. Generates unique session_id (UUID)
    3. Creates system instructions based on role, JD, skills, and questions.
    4. Generates ephemeral token from OpenAI
    5. Returns token and WebRTC config to frontend

    Frontend then uses this token to connect DIRECTLY to OpenAI via WebRTC.
    """
    try:
        result = await realtime_service.create_ephemeral_session(
            mongodb_collection=mongodb_collection,
            ai_interviewers_collection=ai_interviewers_collection,
            role_title=role_title,
            duration_minutes=duration_minutes,
            interviewer_id=interviewer_id,
            front_end_session_id=front_end_session_id,
            candidate_id=candidate_id,
            token=token,
            job_description=job_description,
            skills=skills,
            questions=questions,
            # Required compatibility params
            microphone_status=microphone_status,
            camera_status=camera_status,
            passing_score=passing_score
            # internet_status=internet_status,
            # internet_speed_mbps=internet_speed_mbps
        )

        return ResponseDto(
            Data=result,
            Success=True,
            Message="Ephemeral session created successfully",
            Status=status.HTTP_201_CREATED
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to create session: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/realtime-interview/end", response_model=ResponseDto)
async def end_interview_session(
    session_id: str = Form(...),
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    End interview session and mark as completed.
    
    This endpoint invalidates the session and prevents further updates.
    It should be called when the user explicitly ends the interview or when the timer runs out.
    """
    try:
        result = await realtime_service.end_interview_session(
            mongodb_collection=mongodb_collection,
            session_id=session_id
        )

        return ResponseDto(
            Data=result,
            Success=True,
            Message="Interview session ended successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to end session: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/realtime-interview/update-conversation", response_model=ResponseDto)
async def update_conversation(
    session_id: str = Form(...),
    conversation_json: str = Form(...),
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Update conversation transcript for the interview session.
    
    This endpoint is used to sync the client-side conversation state with the server.
    It acts as a backup and allows for persistence of the interview dialog for later analysis.

    conversation_json format:
    [
        {"role": "assistant", "content": "Tell me about yourself", "timestamp": "2024-01-01T10:00:00Z"},
        {"role": "user", "content": "I am a software engineer...", "timestamp": "2024-01-01T10:00:30Z"},
        ...
    ]
    """
    try:
        result = await realtime_service.update_conversation(
            mongodb_collection=mongodb_collection,
            session_id=session_id,
            conversation_json=conversation_json
        )

        return ResponseDto(
            Data=result,
            Success=True,
            Message="Conversation updated successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to update conversation: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/realtime-interview/evaluate", response_model=ResponseDto)
async def evaluate_interview(
    session_id: str = Form(...),
    passing_score: Optional[int] = Form(None),
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Evaluate completed interview session using AI.

    This triggers a comprehensive analysis of the interview transcript.
    
    Features:
    - Overall performance scoring
    - Detailed feedback on strengths and weaknesses
    - Question-by-question analysis
    - Actionable recommendations for the candidate
    
    Note: This process may take a few seconds as it involves LLM processing.
    """
    try:
        evaluation_data = await realtime_service.evaluate_interview(
            mongodb_collection=mongodb_collection,
            session_id=session_id,
            passing_score=passing_score
        )

        return ResponseDto(
            Data=evaluation_data,
            Success=True,
            Message="Interview evaluation completed successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Evaluation failed: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/interviewers", response_model=ResponseDto)
async def get_interviewers(
    ai_interviewers_collection = Depends(get_ai_interviewers_collection)
):
    """
    Get list of available interviewers with voice models.

    Returns 2 female and 2 male interviewers:
    - Priya Sharma (Female, Indian English, shimmer voice)
    - Sarah Johnson (Female, US English, coral voice)
    - Arjun Patel (Male, Indian English, echo voice)
    - Michael Chen (Male, US English, alloy voice)

    Each interviewer has:
    - Unique ID
    - Name
    - Voice ID (OpenAI voice model)
    - Gender
    - Accent
    - Description
    """
    try:
        interviewers = await realtime_service.get_interviewers(ai_interviewers_collection)
        return ResponseDto(
            Data=interviewers,
            Success=True,
            Message="Interviewers fetched successfully",
            Status=status.HTTP_200_OK
        )

    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to fetch interviewers: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





@router.get("/interview-details/{session_id}", response_model=ResponseDto)
async def get_interview_details(
    session_id: str,
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Get complete interview details by session ID.

    Path Parameters:
    - session_id: Unique session identifier

    Returns complete interview data including:
    - Session metadata (role, company, interviewer, duration, etc.)
    - Timestamps (created, started, ended, evaluated)
    - Full conversation transcript
    - Evaluation results (if evaluated):
      - Total score out of 100
      - Feedback label (Excellent, Good, Fair, Poor)
      - Key strengths
      - Focus areas for improvement
      - Performance breakdown (communication, technical, confidence, structure)
      - Question-by-question analysis with scores and feedback

    Use this endpoint to display detailed interview report after completion.
    """
    try:
        interview_details = await realtime_service.get_interview_details_by_session_id(
            mongodb_collection=mongodb_collection,
            session_id=session_id
        )

        return ResponseDto(
            Data=interview_details,
            Success=True,
            Message="Interview details fetched successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to fetch interview details: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/interview/evaluation", response_model=ResponseDto)
async def get_interview_evaluation(
    front_end_session_id: int,
    candidate_id: int,
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Get evaluation object by front_end_session_id and candidate_id.
    
    Query Parameters:
    - front_end_session_id: Frontend session ID
    - candidate_id: Candidate ID
    
    Returns:
    - Evaluation object containing score, feedback, breakdown etc.
    """
    try:
        evaluation = await realtime_service.get_evaluation_by_session_id(
            mongodb_collection=mongodb_collection,
            front_end_session_id=front_end_session_id,
            candidate_id=candidate_id
        )

        return ResponseDto(
            Data=evaluation,
            Success=True,
            Message="Evaluation fetched successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to fetch evaluation: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/interview/{session_id}", response_model=ResponseDto)
async def delete_interview_by_session_id(
    session_id: str,
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Soft delete an interview session by session ID.

    Path Parameters:
    - session_id: Unique session identifier

    This endpoint performs a soft delete by setting is_deleted flag to True.
    The interview will no longer appear in interview history but the data is preserved.
    Only the owner of the interview session can delete it.

    Returns:
    - Success message with session_id
    """
    try:
        result = await realtime_service.delete_interview_by_session_id(
            mongodb_collection=mongodb_collection,
            session_id=session_id
        )

        return ResponseDto(
            Data=result,
            Success=True,
            Message="Interview deleted successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to delete interview: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/interview/{session_id}/hard", response_model=ResponseDto)
async def hard_delete_interview(
    session_id: str,
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Hard delete an interview session by session ID.
    
    Path Parameters:
    - session_id: Unique session identifier
    
    This endpoint PERMANENTLY removes the interview session from the database.
    This action cannot be undone.
    
    Returns:
    - Success message
    """
    try:
        result = await realtime_service.hard_delete_interview_session(
            mongodb_collection=mongodb_collection,
            session_id=session_id
        )

        return ResponseDto(
            Data=result,
            Success=True,
            Message="Interview permanently deleted successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to delete interview: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/interview/{session_id}/token-usage", response_model=ResponseDto)
async def get_token_usage_summary(
    session_id: str,
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Get token usage and cost summary for a specific interview session.

    Path Parameters:
    - session_id: Unique session identifier

    Returns detailed token usage breakdown including:
    - System instructions tokens (initial prompt)
    - Realtime API tokens (interview conversation)
    - Evaluation tokens (input/output for answer and overall evaluation)
    - Total tokens consumed
    - Total cost in USD

    Only the owner of the interview session can access this information.

    Returns:
    - Token usage breakdown and cost information
    """
    try:
        token_summary = await realtime_service.get_token_usage_summary(
            mongodb_collection=mongodb_collection,
            session_id=session_id
        )

        return ResponseDto(
            Data=token_summary,
            Success=True,
            Message="Token usage summary retrieved successfully",
            Status=status.HTTP_200_OK
        )

    except CustomException as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=e.status_code
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=f"Failed to retrieve token usage: {str(e)}",
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
