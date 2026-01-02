from typing import Optional
from fastapi import APIRouter, status, Depends, Form, UploadFile, File
from dto.response_dto.response_dto import ResponseDto
from dto.request_dto.ai_interview import (
    AIInterviewRoleCreateDTO,
    AIInterviewRoleUpdateDTO,
    QuestionCreateDTO,
    QuestionUpdateDTO
)
from services.ai_interview_management.ai_interview_management import AIInterviewRolesService
from services.ai_interview_management.realtime_interview_service import RealtimeInterviewService
from custom_utilities.custom_exception import CustomException
from custom_utilities.dependencies import get_realtime_interview_collection

router = APIRouter()
service = AIInterviewRolesService()
realtime_service = RealtimeInterviewService()

# Role Management Endpoints (CRUD Order)
@router.post("/createRole", response_model=ResponseDto, status_code=status.HTTP_201_CREATED)
async def create_role(dto: AIInterviewRoleCreateDTO):
    try:
        role = await service.create_role(dto)
        return ResponseDto(
            Data=role,
            Success=True,
            Message="Role created successfully.",
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/getRoles", response_model=ResponseDto)
async def list_roles():
    try:
        roles = await service.get_all_roles()
        return ResponseDto(
            Data=roles,
            Success=True,
            Message="Roles fetched successfully.",
            Status=status.HTTP_200_OK
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/role/{role_id}", response_model=ResponseDto)
async def get_role(role_id: int):
    try:
        role = await service.get_role_by_id(role_id)
        return ResponseDto(
            Data=role,
            Success=True,
            Message="Role fetched successfully.",
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.put("/role/{role_id}", response_model=ResponseDto)
async def update_role(role_id: int, dto: AIInterviewRoleUpdateDTO):
    try:
        role = await service.update_role(role_id, dto)
        return ResponseDto(
            Data=role,
            Success=True,
            Message="Role updated successfully.",
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/role/{role_id}", response_model=ResponseDto)
async def delete_role(role_id: int):
    try:
        await service.delete_role(role_id)
        return ResponseDto(
            Data=None,
            Success=True,
            Message="Role deleted successfully.",
            Status=status.HTTP_204_NO_CONTENT
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




# @router.get("/languages", response_model=ResponseDto)
# async def get_languages():
#     languages = await service.fetch_languages()
#     return ResponseDto(
#         Data=[LanguageDto.model_validate(lang) for lang in languages],
#         Success=True,
#         Message="Languages fetched successfully",
#         Status=status.HTTP_200_OK
#     )

# @router.get("/avatars", response_model=ResponseDto)
# async def get_avatars(language_id: int = None):
#     avatars = await service.fetch_avatars(language_id)
#     return ResponseDto(
#         Data=[AvatarDto.model_validate(a) for a in avatars],
#         Success=True,
#         Message="Avatars fetched successfully",
#         Status=status.HTTP_200_OK
#     )

# Question Management Endpoints
@router.post("/questions", response_model=ResponseDto, status_code=status.HTTP_201_CREATED)
async def create_question(dto: QuestionCreateDTO):
    """
    Create a new interview question.
    
    The question can be optionally linked to a specific role.
    """
    try:
        question = await service.create_question(dto)
        return ResponseDto(
            Data=question,
            Success=True,
            Message="Question created successfully.",
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/questions", response_model=ResponseDto)
async def list_questions(
    role_id: Optional[int] = None,
    
):
    """
    List all active interview questions.
    
    Can be filtered by role_id to get questions for a specific role.
    """
    try:
        questions = await service.get_all_questions(role_id=role_id)
        return ResponseDto(
            Data=questions,
            Success=True,
            Message="Questions fetched successfully.",
            Status=status.HTTP_200_OK
        )
    except Exception as e:
        return ResponseDto(
            Data=None,
            Success=False,
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.put("/questions/{question_id}", response_model=ResponseDto)
async def update_question(
    question_id: int,
    dto: QuestionUpdateDTO,
    
):
    """
    Update an existing interview question.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        question = await service.update_question(question_id, dto)
        return ResponseDto(
            Data=question,
            Success=True,
            Message="Question updated successfully.",
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/questions/{question_id}", response_model=ResponseDto)
async def delete_question(question_id: int):
    """
    Soft delete an interview question.
    
    The question is marked as inactive rather than being permanently deleted.
    """
    try:
        await service.delete_question(question_id)
        return ResponseDto(
            Data=None,
            Success=True,
            Message="Question deleted successfully.",
            Status=status.HTTP_204_NO_CONTENT
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
            Message=str(e),
            Status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Realtime Interview Endpoints
@router.post("/realtime-interview/session", response_model=ResponseDto)
async def create_ephemeral_session(
    interview_role: str = Form(...),
    duration_minutes: int = Form(..., ge=5, le=30),
    interviewer_id: int = Form(...),  # ID of selected interviewer
    job_description: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    # Required: Compatibility test results (must pass all tests)
    microphone_status: bool = Form(...),
    camera_status: bool = Form(...),
    # internet_status: bool = Form(...),
    # internet_speed_mbps: Optional[float] = Form(None),
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Create an ephemeral session token for OpenAI Realtime API.

    **IMPORTANT**: Call /check-compatibility FIRST to validate devices before calling this.

    **Required Compatibility:**
    - microphone_status: MUST be true
    - camera_status: MUST be true

    **If ANY compatibility check fails, session will NOT be created.**

    **Recommended Flow:**

    **Flow 1 (Recommended - Separate Check):**
    1. Call /check-compatibility to test devices
    2. If compatible, call this endpoint to create session
    3. Start interview

    **Flow 2 (Combined - Optional):**
    1. Test devices on frontend
    2. Call this endpoint with compatibility params included
    3. Session is created with compatibility data stored

    This endpoint:
    1. Optionally validates compatibility (if params provided)
    2. Generates unique session_id (UUID)
    3. Validates role
    4. Extracts resume if provided
    5. Creates system instructions
    6. Generates ephemeral token from OpenAI
    7. Returns token and WebRTC config to frontend

    Frontend then uses this token to connect DIRECTLY to OpenAI via WebRTC.
    """
    try:
        result = await realtime_service.create_ephemeral_session(
            mongodb_collection=mongodb_collection,
            interview_role=interview_role,
            company_name="Acelucid",  # Hardcoded company
            interview_round="Technical Round",  # Hardcoded round
            duration_minutes=duration_minutes,
            interviewer_id=interviewer_id,
            user_id=None,  # POC: No authentication required
            job_description=job_description,
            resume_file=resume_file,
            # Required compatibility params
            microphone_status=microphone_status,
            camera_status=camera_status,
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
    """End interview session and mark as completed."""
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
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Evaluate completed interview session.

    Provides comprehensive evaluation including:
    - Question-by-question analysis with scores and feedback
    - Overall performance breakdown
    - Key strengths and focus areas
    - Actionable recommendations
    """
    try:
        evaluation_data = await realtime_service.evaluate_interview(
            mongodb_collection=mongodb_collection,
            session_id=session_id
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
async def get_interviewers():
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
        interviewers = await realtime_service.get_interviewers()
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


@router.get("/interview-history", response_model=ResponseDto)
async def get_interview_history(
    search: Optional[str] = None,
    round: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    
    mongodb_collection = Depends(get_realtime_interview_collection)
):
    """
    Get paginated interview history for the current user.

    Query Parameters:
    - search: Search by role title or interviewer name (optional)
    - round_filter: Filter by interview round (e.g., "Technical", "Behavioral", "All Rounds")
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 50)

    Returns:
    - interviews: List of interview history items
    - total_count: Total number of interviews
    - page: Current page number
    - page_size: Items per page
    - has_more: Whether there are more pages

    Each interview item includes:
    - session_id: Unique session identifier
    - role_title: Job role (e.g., "Software Engineer")
    - company_name: Target company name
    - interviewer_name: Interviewer's name
    - interviewer_initials: Two-letter initials (e.g., "SJ" for Sarah Johnson)
    - interview_round: Round type (e.g., "Technical")
    - interview_date: When the interview was conducted
    - duration_minutes: Interview duration
    - overall_score: Score out of 100 (if evaluated)
    - status: "completed" or "evaluated"
    """
    try:
        # Validate page_size
        if page_size > 50:
            page_size = 50

        # POC: No authentication required - using test user ID
        user_id = "test_user_123"  # TODO: Replace with actual auth when implementing

        history_data = await realtime_service.get_interview_history(
            mongodb_collection=mongodb_collection,
            user_id=str(user_id),
            search=search,
            round_filter=round,
            page=page,
            page_size=page_size
        )

        return ResponseDto(
            Data=history_data,
            Success=True,
            Message="Interview history fetched successfully",
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
            Message=f"Failed to fetch interview history: {str(e)}",
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
        # POC: No authentication required - using test user ID
        user_id = "test_user_123"  # TODO: Replace with actual auth when implementing

        interview_details = await realtime_service.get_interview_details_by_session_id(
            mongodb_collection=mongodb_collection,
            session_id=session_id,
            user_id=str(user_id)
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
        # POC: No authentication required - using test user ID
        user_id = "test_user_123"  # TODO: Replace with actual auth when implementing

        result = await realtime_service.delete_interview_by_session_id(
            mongodb_collection=mongodb_collection,
            session_id=session_id,
            user_id=str(user_id)
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
        # POC: No authentication required - using test user ID
        user_id = "test_user_123"  # TODO: Replace with actual auth when implementing

        token_summary = await realtime_service.get_token_usage_summary(
            mongodb_collection=mongodb_collection,
            session_id=session_id,
            user_id=str(user_id)
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




