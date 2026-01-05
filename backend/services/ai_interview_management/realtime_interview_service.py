"""
Service layer for Realtime Interview Management
Handles business logic for creating, managing, and evaluating realtime interviews
"""
import os
import uuid
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx
import aioboto3
import aiofiles
from fastapi import status, UploadFile
from custom_utilities.custom_exception import CustomException
from repository.ai_interview_management import AIInterviewRolesRepository, RealtimeInterviewMongoRepository
from agents.ai_interview.interview_agent import AIInterviewAgent

logger = logging.getLogger(__name__)

class RealtimeInterviewService:
    """Service for managing realtime AI interviews using OpenAI Realtime API"""

    def __init__(self):
        self.repo = AIInterviewRolesRepository()
        self.mongo_repo = RealtimeInterviewMongoRepository()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # self.transcription_model = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")
        # Transcription model configuration
        # Options: "whisper-1" (standard, cost-effective)
        # For better accuracy with accents/noise, consider upgrading in future
        self.transcription_model = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")

        # S3 configuration
        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        self.aws_region = os.getenv("AWS_REGION_NAME")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # System prompts directory - located in agents/ai_interview/system_prompts
        # Go up to project root: services/ai_interview_management -> services -> root
        self.prompts_dir = Path(__file__).parent.parent.parent / "agents" / "ai_interview" / "system_prompts"


    async def create_ephemeral_session(
        self,
        mongodb_collection,
        interview_role: str,
        company_name: str,
        interview_round: str,
        duration_minutes: int,
        interviewer_id: int,
        user_id: str,
        job_description: Optional[str] = None,
        resume_file: Optional[UploadFile] = None,
        # Required compatibility test results
        microphone_status: bool = True,
        camera_status: bool = True,
        # internet_status: bool = True,
        # internet_speed_mbps: Optional[float] = None
    ) -> dict:
        """
        Create an ephemeral session token for OpenAI Realtime API.

        This method:
        1. Generates unique session_id (UUID)
        2. Validates role and company
        3. Extracts resume if provided
        4. Creates system instructions
        5. Generates ephemeral token from OpenAI
        6. Returns token and WebRTC config to frontend
        """
        # Validate compatibility - ALL must be true
        if not (microphone_status and camera_status):
            compatibility_issues = []
            if not microphone_status:
                compatibility_issues.append("Microphone not working")
            if not camera_status:
                compatibility_issues.append("Camera not working")
            # if not internet_status:
            #     compatibility_issues.append("Internet not connected")

            raise CustomException(
                f"Compatibility check failed: {', '.join(compatibility_issues)}.",
                status_code=status.HTTP_400_BAD_REQUEST
            )


        # Generate unique session_id
        session_id = f"interview_{uuid.uuid4().hex}"

        # Get interviewer details (with fallback to mock data)
        try:
            interviewer = await self.repo.get_interviewer_by_id(interviewer_id)
            if not interviewer:
                raise CustomException("Interviewer not found", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.warning(f"Database query for interviewer failed, using mock data: {e}")
            # Fallback to mock interviewer data
            mock_interviewers = {
                "1": {"id": 1, "name": "Priya Sharma", "voice_id": "shimmer", "gender": "Female", "accent": "Indian English"},
                "2": {"id": 2, "name": "Sarah Johnson", "voice_id": "coral", "gender": "Female", "accent": "US English"},
                "3": {"id": 3, "name": "Arjun Patel", "voice_id": "echo", "gender": "Male", "accent": "Indian English"},
                "4": {"id": 4, "name": "Michael Chen", "voice_id": "alloy", "gender": "Male", "accent": "US English"},
            }
            
            mock_data = mock_interviewers.get(str(interviewer_id))
            if not mock_data:
                raise CustomException("Interviewer not found", status_code=status.HTTP_404_NOT_FOUND)
            
            # Create a mock interviewer object with required attributes
            class MockInterviewer:
                def __init__(self, data):
                    self.id = data["id"]
                    self.name = data["name"]
                    self.voice_id = data["voice_id"]
                    self.gender = data["gender"]
                    self.accent = data["accent"]
                    self.greet_video = None
                    self.video_blink_1 = None
                    self.video_blink_2 = None
                    self.video_dubb = None
                    self.img = None
            
            interviewer = MockInterviewer(mock_data)


        # Get interview round (with fallback to mock data)
        try:
            interview_round_obj = await self.repo.get_interview_round_by_name(interview_round)
            if not interview_round_obj:
                # Fallback to mock interview round
                logger.warning(f"Interview round not found in database, using mock data for: {interview_round}")
                class MockInterviewRound:
                    def __init__(self, name):
                        self.name = name
                        self.id = 1
                interview_round_obj = MockInterviewRound(interview_round)
        except AttributeError as e:
            # Repository doesn't have this method - use mock data
            logger.warning(f"Repository method not available, using mock interview round: {e}")
            class MockInterviewRound:
                def __init__(self, name):
                    self.name = name
                    self.id = 1
            interview_round_obj = MockInterviewRound(interview_round)
        except Exception as e:
            # Any other database error - use mock data
            logger.warning(f"Database error for interview round, using mock data: {e}")
            class MockInterviewRound:
                def __init__(self, name):
                    self.name = name
                    self.id = 1
            interview_round_obj = MockInterviewRound(interview_round)

        # Extract resume if provided
        resume_context = await self._extract_resume(resume_file, session_id) if resume_file else None

        # Create system instructions
        system_instructions = self._create_system_instructions(
            role=interview_role,
            company=company_name,
            interview_round=interview_round_obj.name,
            duration=duration_minutes,
            resume_context=resume_context,
            job_description=job_description
        )

        # Create ephemeral token from OpenAI with interviewer's voice
        ephemeral_token = await self._create_openai_session(
            system_instructions=system_instructions,
            voice=interviewer.voice_id
        )

        # Prepare compatibility test data
        is_compatible = microphone_status and camera_status
        tested_at = datetime.now(timezone.utc)

        # Calculate system instruction tokens (approximate)
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            system_instruction_tokens = len(encoding.encode(system_instructions))
        except:
            # Fallback approximation: ~1 token per 4 characters
            system_instruction_tokens = len(system_instructions) // 4

        # Store session info in MongoDB
        session_data = {
            "_id": session_id,
            "session_id": session_id,
            "user_id": user_id,
            "interview_role": interview_role,
            "company_name": company_name,
            "interview_round": interview_round,
            "duration": duration_minutes,
            "duration_minutes": duration_minutes,
            "interviewer_id": interviewer.id,
            "interviewer_name": interviewer.name,
            "voice": interviewer.voice_id,
            "status": "initialized",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "resume_context": resume_context,
            "job_description": job_description,
            "conversation": [],
            "compatibility_test": {
                "microphone_status": microphone_status,
                "camera_status": camera_status,
                # "internet_status": internet_status,
                # "internet_speed_mbps": internet_speed_mbps,
                "is_compatible": is_compatible,
                "tested_at": tested_at
            },
            "token_usage": {
                "system_instructions_tokens": system_instruction_tokens,
                "realtime_api_tokens": 0,  # Will be updated during/after interview
                "evaluation_tokens": 0,  # Will be updated after evaluation
                "total_tokens": system_instruction_tokens,
                "estimated_cost_usd": 0.0  # Will be calculated after interview
            }
        }

        if mongodb_collection is not None:
            await self.mongo_repo.create_session(mongodb_collection, session_data)

        # Calculate token expiration
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()

        return {
            "session_id": session_id,
            "ephemeral_token": ephemeral_token,
            "openai_api_url": "https://api.openai.com/v1/realtime",
            # "model": "gpt-4o-realtime-preview-2024-12-17",
            "model": "gpt-4o-mini-realtime-preview-2024-12-17",
            "voice": interviewer.voice_id,
            "expires_at": expires_at,
            "interviewer": {
                "id": interviewer.id,
                "name": interviewer.name,
                "voice_id": interviewer.voice_id,
                "gender": interviewer.gender,
                "accent": interviewer.accent,
                "greet_video": interviewer.greet_video,
                "video_blink_1": interviewer.video_blink_1,
                "video_blink_2": interviewer.video_blink_2,
                "video_dubb": interviewer.video_dubb,
                "img": interviewer.img
            },
            "webrtc_config": {
                "iceServers": [
                    {
                        "urls": [
                            "stun:stun.l.google.com:19302",
                            "stun:stun1.l.google.com:19302"
                        ]
                    }
                ],
                "iceTransportPolicy": "all",
                "bundlePolicy": "balanced",
                "rtcpMuxPolicy": "require"
            },
            "interview_context": {
                "role": interview_role,
                "company": company_name,
                "round": interview_round,
                "duration": duration_minutes,
                "type": "conversational"
            }
        }

    async def _upload_resume_to_s3(self, resume_file: UploadFile, session_id: str) -> Optional[str]:
        """Upload resume to S3 and return URL"""
        try:
            # Generate S3 key
            file_extension = os.path.splitext(resume_file.filename)[1]
            s3_key = f"ai-interview/resumes/{session_id}/{uuid.uuid4()}{file_extension}"

            # Upload to S3
            session = aioboto3.Session()
            async with session.client(
                's3',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            ) as s3_client:
                content = await resume_file.read()
                await s3_client.put_object(
                    Bucket=self.s3_bucket_name,
                    Key=s3_key,
                    Body=content,
                    ContentType=resume_file.content_type or 'application/pdf'
                )

            # Return S3 URL
            s3_url = f"https://{self.s3_bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            return s3_url

        except Exception as e:
            print(f"S3 upload error: {str(e)}")
            return None

    async def _extract_resume(self, resume_file: UploadFile, session_id: str) -> Optional[str]:
        """Extract text from resume file using S3 and extractipy"""
        temp_file_path = None
        temp_output_dir = None
        try:
            # Upload to S3 first
            s3_url = await self._upload_resume_to_s3(resume_file, session_id)
            if not s3_url:
                print("S3 upload failed, proceeding with extraction anyway")

            # Create temp directories
            os.makedirs("temp_resumes", exist_ok=True)
            os.makedirs("temp_output", exist_ok=True)

            temp_file_path = f"temp_resumes/resume_{session_id}_{resume_file.filename}"
            temp_output_dir = "temp_output"

            # Reset file pointer and save locally
            await resume_file.seek(0)
            async with aiofiles.open(temp_file_path, "wb") as f:
                content = await resume_file.read()
                await f.write(content)

            # Extract text using extractipy (with output directory like material management)
            from extractipy.file_extractors import FileExtractor
            extractor = FileExtractor(verbose=False)
            extracted_data = await extractor.extract_data_from_file(temp_file_path, temp_output_dir)
            resume_context = extracted_data.get('text', '')

            # Clean up temp files immediately
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Cleanup warning: {str(cleanup_error)}")

            # Clean up extracted output file
            if temp_output_dir:
                import glob
                for f in glob.glob(os.path.join(temp_output_dir, "*")):
                    try:
                        os.remove(f)
                    except:
                        pass

            return resume_context

        except Exception as e:
            print(f"Resume extraction error: {str(e)}")
            # Ensure cleanup even on error
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            return None

    async def _create_openai_session(self, system_instructions: str, voice: str) -> str:
        """Create ephemeral token from OpenAI using direct HTTP request"""
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    "https://api.openai.com/v1/realtime/sessions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini-realtime-preview-2024-12-17",
                        "voice": voice,
                        "instructions": system_instructions,
                        "modalities": ["text", "audio"],
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": self.transcription_model
                        },
                        "input_audio_noise_reduction": {
                            "type": "far_field"                 
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "threshold": 0.3,  # Lower threshold for better detection (was 0.5)
                            "prefix_padding_ms": 1000,  # More context before speech (was 300)
                            "silence_duration_ms": 3000  # Wait longer for pauses (was 500)
                        },
                        "temperature": 0.8,
                        "max_response_output_tokens": 4096
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    raise CustomException(
                        f"OpenAI API error: {response.status_code} - {response.text}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                session_data = response.json()
                ephemeral_token = session_data.get("client_secret", {}).get("value")

                if not ephemeral_token:
                    raise CustomException(
                        "Failed to retrieve ephemeral token from OpenAI response",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return ephemeral_token

        except CustomException:
            raise
        except Exception as e:
            print(f"OpenAI session creation error: {str(e)}")
            raise CustomException(
                f"Failed to create OpenAI session: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) from e

    def _load_prompt_from_file(self, filename: str) -> str:
        """Load prompt content from markdown file"""
        try:
            file_path = self.prompts_dir / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filename}")
            raise CustomException(
                f"Prompt file not found: {filename}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Error loading prompt file {filename}: {str(e)}")
            raise CustomException(
                f"Error loading prompt file: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_round_specific_flow(self, interview_round: str, role: str, company: str = "") -> str:
        """Get interview flow and questions specific to the interview round from markdown files"""

        round_lower = interview_round.lower()

        # Determine which prompt file to load based on interview round
        if "warm" in round_lower or "warmup" in round_lower or "warm up" in round_lower:
            prompt_file = "round_warmup.md"
            prompt_content = self._load_prompt_from_file(prompt_file)
            logger.info(f"Loading WARM-UP round prompt for interview_round: {interview_round}")
        elif "technical" in round_lower or "tech" in round_lower:
            prompt_file = "round_technical.md"
            prompt_content = self._load_prompt_from_file(prompt_file)
            logger.info(f"Loading TECHNICAL round prompt for interview_round: {interview_round}")
        elif "managerial" in round_lower or "manager" in round_lower:
            prompt_file = "round_managerial.md"
            prompt_content = self._load_prompt_from_file(prompt_file)
            logger.info(f"Loading MANAGERIAL round prompt for interview_round: {interview_round}")
        elif "hr" in round_lower or "human" in round_lower:
            prompt_file = "round_hr.md"
            prompt_content = self._load_prompt_from_file(prompt_file)
            logger.info(f"Loading HR round prompt for interview_round: {interview_round}")
        else:
            # Default/General round
            prompt_file = "round_general.md"
            prompt_content = self._load_prompt_from_file(prompt_file)
            logger.warning(f"No specific round match for '{interview_round}', using general round")

        # Replace placeholders with actual values
        prompt_content = prompt_content.replace("{role}", role)
        prompt_content = prompt_content.replace("{company}", company or '')

        return prompt_content

    def _create_system_instructions(
        self,
        role: str,
        company: str,
        interview_round: str,
        duration: int,
        resume_context: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> str:
        """Create system instructions for the AI interviewer by loading from markdown file"""

        # Build context section
        context_parts = []
        if resume_context:
            context_parts.append(f"Candidate's Resume:\n{resume_context}")
        if job_description:
            context_parts.append(f"Job Description:\n{job_description}")

        context_section = "\n\n".join(context_parts) if context_parts else "No additional context provided."

        # Load main instructions template from file
        main_instructions = self._load_prompt_from_file("main_instructions.md")

        # Get round-specific flow (passing company for HR round)
        round_specific_flow = self._get_round_specific_flow(interview_round, role, company)

        # Replace all placeholders in the template
        instructions = main_instructions.replace("{interview_round}", interview_round)
        instructions = instructions.replace("{role}", role)
        # Handle company placeholder - add "at [company]" only if company is provided
        company_text = f" at {company}" if company else ""
        instructions = instructions.replace("{company}", company_text)
        instructions = instructions.replace("{duration}", str(duration))
        instructions = instructions.replace("{interview_round_upper}", interview_round.upper())
        instructions = instructions.replace("{round_specific_flow}", round_specific_flow)
        instructions = instructions.replace("{resume_context}", resume_context or "")
        instructions = instructions.replace("{job_description}", job_description or "")
        instructions = instructions.replace("{context_section}", context_section)

        # Log the interview configuration for debugging
        logger.info(f"System instructions created - Round: {interview_round}, Role: {role}, Company: {company or 'None'}, Duration: {duration} mins")
        logger.debug(f"Round-specific flow preview: {round_specific_flow[:200]}...")

        return instructions

    async def end_interview_session(self, mongodb_collection, session_id: str):
        """End interview session and mark as completed"""
        if mongodb_collection is not None:
            result = await self.mongo_repo.end_session(mongodb_collection, session_id)

            if result.matched_count == 0:
                raise CustomException("Session not found", status_code=status.HTTP_404_NOT_FOUND)

        return {
            "session_id": session_id,
            "status": "completed"
        }

    async def update_conversation(
        self,
        mongodb_collection,
        session_id: str,
        conversation_json: str
    ):
        """Update conversation transcript for the interview session and track tokens"""
        import json
        import tiktoken

        if mongodb_collection is None:
            raise CustomException("Database not available", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Parse conversation JSON
        try:
            conversation = json.loads(conversation_json)
            if not isinstance(conversation, list):
                raise ValueError("Conversation must be an array")
        except json.JSONDecodeError:
            raise CustomException("Invalid JSON format for conversation", status_code=status.HTTP_400_BAD_REQUEST)

        agent = AIInterviewAgent()
        processed_conversation = await agent.process_conversation(conversation)

        # Calculate Realtime API tokens from conversation
        # The conversation contains all AI and user exchanges during the interview
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            total_conversation_tokens = 0
            total_audio_duration_seconds = 0

            for message in conversation:
                # Count text tokens from message content
                if isinstance(message, dict):
                    # Get message content (from 'content' or 'transcript' field)
                    text_content = message.get("content", "") or message.get("transcript", "")
                    if text_content:
                        total_conversation_tokens += len(encoding.encode(text_content))

                    # Track audio duration if available (for Whisper cost)
                    # Check multiple possible field names for audio duration
                    audio_duration = (
                        message.get("audio_duration_ms", 0) or
                        message.get("audio_duration", 0) or
                        0
                    )
                    if audio_duration:
                        # Convert to seconds if in milliseconds (value > 1000 likely means ms)
                        if audio_duration > 1000:
                            total_audio_duration_seconds += audio_duration / 1000
                        else:
                            total_audio_duration_seconds += audio_duration

            # If no audio duration in messages, estimate from interview duration
            # Get session to check interview duration
            session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
            if session and total_audio_duration_seconds == 0:
                # Use interview duration as fallback for audio duration
                interview_duration_minutes = session.get("duration", 0)
                total_audio_duration_seconds = interview_duration_minutes * 60
                logger.info(f"Using interview duration as audio duration: {interview_duration_minutes} minutes")

        except Exception as e:
            logger.warning(f"Error calculating conversation tokens: {e}")
            total_conversation_tokens = len(str(conversation)) // 4  # Fallback estimation

            # Estimate audio duration from interview duration
            session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
            if session:
                interview_duration_minutes = session.get("duration", 0)
                total_audio_duration_seconds = interview_duration_minutes * 60
            else:
                total_audio_duration_seconds = 0

        # Calculate Whisper transcription cost
        # Whisper pricing: $0.006 per minute
        audio_duration_minutes = total_audio_duration_seconds / 60
        whisper_cost = audio_duration_minutes * 0.006

        # Calculate Realtime API cost for conversation
        # gpt-4o-mini-realtime-preview pricing:
        # - Text input: $0.60 per 1M tokens
        # - Text output: $2.40 per 1M tokens
        # Note: We're estimating 50/50 split between user (input) and AI (output)
        # For more accurate calculation, we'd need to track input/output separately
        estimated_input_tokens = total_conversation_tokens // 2
        estimated_output_tokens = total_conversation_tokens - estimated_input_tokens

        realtime_input_cost = (estimated_input_tokens / 1_000_000) * 0.60
        realtime_output_cost = (estimated_output_tokens / 1_000_000) * 2.40
        realtime_api_cost = realtime_input_cost + realtime_output_cost

        # Get current session to update token usage
        session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
        current_token_usage = session.get("token_usage", {}) if session else {}

        # Update token usage with conversation data
        updated_token_usage = {
            "system_instructions_tokens": current_token_usage.get("system_instructions_tokens", 0),
            "realtime_api_tokens": total_conversation_tokens,
            "realtime_api_input_tokens": estimated_input_tokens,
            "realtime_api_output_tokens": estimated_output_tokens,
            "realtime_api_cost_usd": round(realtime_api_cost, 6),
            "realtime_audio_duration_seconds": total_audio_duration_seconds,
            "whisper_transcription_cost_usd": round(whisper_cost, 6),
            "evaluation_input_tokens": current_token_usage.get("evaluation_input_tokens", 0),
            "evaluation_output_tokens": current_token_usage.get("evaluation_output_tokens", 0),
            "evaluation_total_tokens": current_token_usage.get("evaluation_total_tokens", 0),
            "evaluation_cost_usd": current_token_usage.get("evaluation_cost_usd", 0.0)
        }

        # Calculate interim total (before evaluation)
        interim_total_tokens = (
            updated_token_usage["system_instructions_tokens"] +
            updated_token_usage["realtime_api_tokens"]
        )
        interim_total_cost = whisper_cost + realtime_api_cost

        updated_token_usage["total_tokens"] = interim_total_tokens
        updated_token_usage["total_cost_usd"] = round(interim_total_cost, 6)

        # Update session with conversation AND token usage
        result = await self.mongo_repo.update_conversation_and_tokens(
            mongodb_collection,
            session_id,
            processed_conversation,
            updated_token_usage
        )

        if result.matched_count == 0:
            raise CustomException("Session not found", status_code=status.HTTP_404_NOT_FOUND)

        logger.info(
            f"Conversation updated. Messages: {len(conversation)}, "
            f"Tokens: {total_conversation_tokens}, "
            f"Audio: {audio_duration_minutes:.2f}min, "
            f"Costs - Realtime API: ${realtime_api_cost:.6f}, Whisper: ${whisper_cost:.6f}, Total: ${interim_total_cost:.6f}"
        )

        return {
            "session_id": session_id,
            "conversation_messages": len(conversation),
            "realtime_api_tokens": total_conversation_tokens,
            "realtime_api_cost_usd": round(realtime_api_cost, 6),
            "audio_duration_minutes": round(audio_duration_minutes, 2),
            "whisper_cost_usd": round(whisper_cost, 6),
            "total_cost_usd": round(interim_total_cost, 6)
        }

    async def evaluate_interview(self, mongodb_collection, session_id: str):
        """Evaluate completed interview session"""
        if mongodb_collection is None:
            raise CustomException("Database not available", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)

        if not session:
            raise CustomException("Session not found", status_code=status.HTTP_404_NOT_FOUND)

        # Allow evaluation for both "completed" and "evaluated" status (for re-evaluation)
        if session.get("status") not in ["completed", "evaluated"]:
            raise CustomException("Interview not completed yet", status_code=status.HTTP_400_BAD_REQUEST)

        # Get conversation transcript
        conversation = session.get("conversation", [])

        if not conversation:
            raise CustomException(
                "No conversation data found. Cannot evaluate empty interview.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Initialize evaluation service
        from services.ai_interview_management.realtime_interview_evaluation_service import RealtimeInterviewEvaluationService
        evaluation_service = RealtimeInterviewEvaluationService()

        # Evaluate the interview
        evaluation_data = await evaluation_service.evaluate_interview_session(
            session_data=session,
            conversation_transcript=conversation
        )

        # Store evaluation in database
        await self.mongo_repo.save_evaluation(mongodb_collection, session_id, evaluation_data)

        return evaluation_data

    async def get_interviewers(self) -> list[dict]:
        """
        Get list of available interviewers with voice models from database.
        Returns 2 female and 2 male interviewers with their video assets.

        Available OpenAI voices: alloy, ash, ballad, coral, echo, sage, shimmer, verse
        """
        try:
            interviewers_db = await self.repo.get_all_interviewers()

            if interviewers_db and len(interviewers_db) > 0:
                # Database has interviewers - use them
                interviewers = []
                for interviewer in interviewers_db:
                    interviewers.append({
                        "id": str(interviewer.id),
                        "name": interviewer.name,
                        "voice_id": interviewer.voice_id,
                        "gender": interviewer.gender,
                        "accent": interviewer.accent,
                        "description": interviewer.description,
                        "greet_video": interviewer.greet_video,
                        "video_blink_1": interviewer.video_blink_1,
                        "video_blink_2": interviewer.video_blink_2,
                        "video_dubb": interviewer.video_dubb,
                        "img": interviewer.img
                    })
                return interviewers
        except Exception as e:
            logger.warning(f"Database query failed, using mock data: {e}")
        
        # Fallback: Return mock interviewers for testing (POC mode)
        logger.info("Using mock interviewer data (database not available)")
        return [
            {
                "id": "1",
                "name": "Priya Sharma",
                "voice_id": "shimmer",
                "gender": "Female",
                "accent": "Indian English",
                "description": "Experienced technical interviewer with expertise in software engineering",
                "greet_video": None,
                "video_blink_1": None,
                "video_blink_2": None,
                "video_dubb": None,
                "img": None
            },
            {
                "id": "2",
                "name": "Sarah Johnson",
                "voice_id": "coral",
                "gender": "Female",
                "accent": "US English",
                "description": "Senior HR interviewer specializing in behavioral assessments",
                "greet_video": None,
                "video_blink_1": None,
                "video_blink_2": None,
                "video_dubb": None,
                "img": None
            },
            {
                "id": "3",
                "name": "Arjun Patel",
                "voice_id": "echo",
                "gender": "Male",
                "accent": "Indian English",
                "description": "Tech lead with focus on system design interviews",
                "greet_video": None,
                "video_blink_1": None,
                "video_blink_2": None,
                "video_dubb": None,
                "img": None
            },
            {
                "id": "4",
                "name": "Michael Chen",
                "voice_id": "alloy",
                "gender": "Male",
                "accent": "US English",
                "description": "Engineering manager focused on leadership and technical skills",
                "greet_video": None,
                "video_blink_1": None,
                "video_blink_2": None,
                "video_dubb": None,
                "img": None
            }
        ]

    async def get_interview_history(
        self,
        mongodb_collection,
        user_id: str,
        search: Optional[str] = None,
        round_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        Get paginated interview history for a user with search and filter options.

        Args:
            mongodb_collection: MongoDB collection for interviews
            user_id: User ID to fetch history for
            search: Search query for role or interviewer name
            round_filter: Filter by interview round (e.g., "Technical", "Behavioral")
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with interviews list, pagination info
        """
        # Calculate pagination
        skip = (page - 1) * page_size

        # Repository layer: Fetch sessions from database with filters
        sessions, total_count = await self.mongo_repo.get_user_interview_history(
            mongodb_collection=mongodb_collection,
            user_id=user_id,
            search=search,
            round_filter=round_filter,
            skip=skip,
            limit=page_size
        )

        # Business logic: Calculate pagination metadata
        has_more = total_count > (page * page_size)

        # Business logic: Format response data
        interviews = []
        for session in sessions:
            # Get interviewer initials
            interviewer_name = session.get("interviewer_name", "Unknown")
            initials = "".join([word[0].upper() for word in interviewer_name.split()[:2]])

            # Get overall score from evaluation.overall_evaluation.total_score
            evaluation = session.get("evaluation", {})
            overall_evaluation = evaluation.get("overall_evaluation", {})
            total_score = overall_evaluation.get("total_score")

            interview_item = {
                "session_id": session.get("session_id") or str(session.get("_id")),
                "role_title": session.get("interview_role", "Unknown Role"),
                "company_name": session.get("company_name"),
                "interviewer_name": interviewer_name,
                "interviewer_initials": initials,
                "interview_round": session.get("interview_round", "General"),
                "interview_date": session.get("created_at"),
                "duration_minutes": session.get("duration", 30),
                "overall_score": total_score,
                "status": session.get("status", "completed")
            }

            interviews.append(interview_item)

        return {
            "interviews": interviews,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": has_more
        }

    async def get_interview_details_by_session_id(
        self,
        mongodb_collection,
        session_id: str,
        user_id: str
    ) -> dict:
        """
        Get complete interview details by session ID.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to fetch details for
            user_id: User ID to verify ownership

        Returns:
            Complete interview details including evaluation
        """
        # Repository layer: Fetch session with user ownership verification
        session = await self.mongo_repo.get_session_by_id_and_user(
            mongodb_collection, session_id, user_id
        )

        if not session:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Business logic: Extract and format evaluation data
        evaluation = session.get("evaluation", {})
        overall_evaluation = evaluation.get("overall_evaluation", {})
        questions = evaluation.get("questions", [])

        # Business logic: Format interviewer details
        interviewer_name = session.get("interviewer_name", "Unknown")
        interviewer_initials = "".join([word[0].upper() for word in interviewer_name.split()[:2]])

        # Business logic: Build formatted response
        interview_details = {
            "session_id": session.get("session_id"),
            "role_title": session.get("interview_role"),
            "company_name": session.get("company_name"),
            "interview_round": session.get("interview_round"),
            "interviewer_name": interviewer_name,
            "interviewer_initials": interviewer_initials,
            "duration_minutes": session.get("duration_minutes", session.get("duration")),
            "status": session.get("status"),
            "created_at": session.get("created_at"),
            "ended_at": session.get("ended_at"),
            "evaluated_at": evaluation.get("evaluated_at"),
            "conversation": session.get("conversation", []),
            "evaluation": {
                "total_score": overall_evaluation.get("total_score"),
                "feedback_label": overall_evaluation.get("feedback_label"),
                "key_strengths": overall_evaluation.get("key_strengths", []),
                "focus_areas": overall_evaluation.get("focus_areas", []),
                "performance_breakdown": overall_evaluation.get("performance_breakdown", {}),
                "questions": questions
            } if evaluation else None
        }

        return interview_details

    async def delete_interview_by_session_id(
        self,
        mongodb_collection,
        session_id: str,
        user_id: str
    ) -> dict:
        """
        Soft delete an interview by session ID.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to delete
            user_id: User ID to verify ownership

        Returns:
            Success message

        Raises:
            CustomException: If session not found or user doesn't have access
        """
        # Repository layer: Perform soft delete operation
        result = await self.mongo_repo.soft_delete_interview_session(
            mongodb_collection, session_id, user_id
        )

        # Business logic: Verify deletion was successful
        if result.matched_count == 0:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return {
            "session_id": session_id,
            "message": "Interview deleted successfully"
        }

    async def get_token_usage_summary(
        self,
        mongodb_collection,
        session_id: str,
        user_id: str
    ) -> dict:
        """
        Get token usage and cost summary for a specific interview session.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to get token usage for
            user_id: User ID to verify ownership

        Returns:
            Token usage breakdown and cost information

        Raises:
            CustomException: If session not found or user doesn't have access
        """
        # Repository layer: Fetch session with user ownership verification
        session = await self.mongo_repo.get_session_by_id_and_user(
            mongodb_collection, session_id, user_id
        )

        if not session:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Business logic: Extract token usage data
        token_usage = session.get("token_usage", {})

        # Fallback: If conversation tokens are 0 but conversation exists, recalculate
        if token_usage.get("realtime_api_tokens", 0) == 0 and session.get("conversation"):
            try:
                import tiktoken
                encoding = tiktoken.encoding_for_model("gpt-4o-mini")
                conversation = session.get("conversation", [])
                total_conversation_tokens = 0

                for message in conversation:
                    if isinstance(message, dict):
                        text_content = message.get("content", "") or message.get("transcript", "")
                        if text_content:
                            total_conversation_tokens += len(encoding.encode(text_content))

                # Calculate Realtime API cost
                estimated_input_tokens = total_conversation_tokens // 2
                estimated_output_tokens = total_conversation_tokens - estimated_input_tokens
                realtime_input_cost = (estimated_input_tokens / 1_000_000) * 0.60
                realtime_output_cost = (estimated_output_tokens / 1_000_000) * 2.40
                realtime_api_cost = realtime_input_cost + realtime_output_cost

                # Update token_usage with recalculated values
                token_usage["realtime_api_tokens"] = total_conversation_tokens
                token_usage["realtime_api_input_tokens"] = estimated_input_tokens
                token_usage["realtime_api_output_tokens"] = estimated_output_tokens
                token_usage["realtime_api_cost_usd"] = round(realtime_api_cost, 6)

                # If audio duration is 0, use interview duration as estimate
                if token_usage.get("realtime_audio_duration_seconds", 0) == 0:
                    interview_duration_minutes = session.get("duration", 0)
                    audio_duration_seconds = interview_duration_minutes * 60
                    whisper_cost = (audio_duration_seconds / 60) * 0.006

                    token_usage["realtime_audio_duration_seconds"] = audio_duration_seconds
                    token_usage["whisper_transcription_cost_usd"] = round(whisper_cost, 6)

                    # Recalculate COMPLETE total cost with ALL components
                    total_cost = (
                        token_usage.get("realtime_api_cost_usd", 0.0) +
                        token_usage.get("whisper_transcription_cost_usd", 0.0) +
                        token_usage.get("evaluation_cost_usd", 0.0)
                    )
                    token_usage["total_cost_usd"] = round(total_cost, 6)

                    # Recalculate total tokens
                    total_tokens = (
                        token_usage.get("system_instructions_tokens", 0) +
                        token_usage.get("realtime_api_tokens", 0) +
                        token_usage.get("evaluation_total_tokens", 0)
                    )
                    token_usage["total_tokens"] = total_tokens

                logger.info(f"Recalculated tokens for session {session.get('session_id')}: {total_conversation_tokens} tokens, Realtime cost: ${realtime_api_cost:.6f}, Whisper: ${whisper_cost:.6f}")

            except Exception as e:
                logger.warning(f"Error recalculating conversation tokens: {e}")

        # Business logic: Build formatted token usage summary with ALL cost components
        token_summary = {
            "session_id": session.get("session_id"),
            "interview_role": session.get("interview_role"),
            "company_name": session.get("company_name"),
            "interview_round": session.get("interview_round"),
            "status": session.get("status"),
            "duration_minutes": session.get("duration", 0),
            "token_usage": {
                "system_instructions_tokens": token_usage.get("system_instructions_tokens", 0),
                "realtime_conversation": {
                    "model": "gpt-4o-mini-realtime-preview-2024-12-17",
                    "total_tokens": token_usage.get("realtime_api_tokens", 0),
                    "input_tokens": token_usage.get("realtime_api_input_tokens", 0),
                    "output_tokens": token_usage.get("realtime_api_output_tokens", 0),
                    "cost_usd": token_usage.get("realtime_api_cost_usd", 0.0),
                    "pricing": {
                        "input_per_1m_tokens": 0.60,
                        "output_per_1m_tokens": 2.40
                    },
                    "audio_duration_seconds": token_usage.get("realtime_audio_duration_seconds", 0),
                    "audio_duration_minutes": round(token_usage.get("realtime_audio_duration_seconds", 0) / 60, 2)
                },
                "transcription": {
                    "model": "whisper-1",
                    "cost_usd": token_usage.get("whisper_transcription_cost_usd", 0.0),
                    "pricing_per_minute": 0.006
                },
                "evaluation": {
                    "model": "gpt-4o-mini",
                    "input_tokens": token_usage.get("evaluation_input_tokens", 0),
                    "output_tokens": token_usage.get("evaluation_output_tokens", 0),
                    "total_tokens": token_usage.get("evaluation_total_tokens", 0),
                    "cost_usd": token_usage.get("evaluation_cost_usd", 0.0),
                    "pricing": {
                        "input_per_1m_tokens": 0.150,
                        "output_per_1m_tokens": 0.600
                    }
                },
                "totals": {
                    "total_tokens": token_usage.get("total_tokens", 0),
                    "total_cost_usd": token_usage.get("total_cost_usd", 0.0),
                    "cost_breakdown": {
                        "realtime_api_conversation": token_usage.get("realtime_api_cost_usd", 0.0),
                        "whisper_transcription": token_usage.get("whisper_transcription_cost_usd", 0.0),
                        "evaluation_processing": token_usage.get("evaluation_cost_usd", 0.0)
                    }
                }
            },
            "created_at": session.get("created_at"),
            "evaluated_at": session.get("evaluation", {}).get("evaluated_at")
        }

        return token_summary
