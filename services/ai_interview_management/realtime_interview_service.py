"""
Service layer for Realtime Interview Management
Handles business logic for creating, managing, and evaluating realtime interviews
"""
import os
import uuid
import logging
import json
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
from agents.ai_interview.system_prompts.interview_prompts import HR_SCREENING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class RealtimeInterviewService:
    """Service for managing realtime AI interviews using OpenAI Realtime API"""

    def __init__(self):
        
        self.mongo_repo = RealtimeInterviewMongoRepository()
        self.agent = AIInterviewAgent()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.transcription_model = os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")

        
        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        self.aws_region = os.getenv("AWS_REGION_NAME")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.prompts_dir = Path(__file__).parent.parent.parent / "agents" / "ai_interview" / "system_prompts"


    async def _notify_external_backend(self, front_end_session_id: int, status: str, score: float, token: str):
        """
        Notify external backend about interview completion.
        This runs in the background to avoid blocking the user response.
        """
        url = os.getenv("EXTERNAL_STATUS_API_URL", "https://lms.acelucid.com/api/ai/session/status")
        
        
        final_score = int(round(score)) if score is not None else 0
        
        payload = {
            "session_id": front_end_session_id,  
            "status": status.lower(),            
            "score": final_score,                
            "token": token                       
        }
        
        try:
            
            async with httpx.AsyncClient() as client:
                
                response = await client.patch(url, json=payload, timeout=5.0)
                
                if response.status_code == 200:
                    logger.info(f"✅ Notification sent for Session {front_end_session_id}: {payload}")
                else:
                    logger.warning(f"⚠️ Notification failed for Session {front_end_session_id}: {response.status_code} - {response.text}")
                    
        except Exception as e:
            
            logger.error(f"❌ Error notifying external backend: {str(e)}")

    async def create_ephemeral_session(
        self,
        mongodb_collection,
        ai_interviewers_collection,
        role_title: str,
        duration_minutes: int,
        interviewer_id: int,
        front_end_session_id: int,
        candidate_id: int,
        token: str,
        job_description: Optional[str] = None,
        skills: Optional[str] = None,
        questions: Optional[str] = None,
        microphone_status: bool = True,
        camera_status: bool = True,
        passing_score: Optional[int] = None
    ) -> dict:
        """
        Create an ephemeral session token for OpenAI Realtime API.
        
        This method:
        1. Generates unique session_id (UUID)
        2. Creates system instructions using HR_SCREENING_SYSTEM_PROMPT
        3. Generates ephemeral token from OpenAI
        4. Returns token and WebRTC config to frontend
        """
        
        if not (microphone_status and camera_status):
            compatibility_issues = []
            if not microphone_status:
                compatibility_issues.append("Microphone not working")
            if not camera_status:
                compatibility_issues.append("Camera not working")

            raise CustomException(
                f"Compatibility check failed: {', '.join(compatibility_issues)}.",
                status_code=status.HTTP_400_BAD_REQUEST
            )


        
        session_id = f"interview_{uuid.uuid4().hex}"

        
        try:
            
            repo = AIInterviewRolesRepository(ai_interviewers_collection)
            interviewer = await repo.get_interviewer_by_id(interviewer_id)
            if not interviewer:
                raise CustomException("Interviewer not found", status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.warning(f"Database query for interviewer failed, using mock data: {e}")
            
            mock_interviewers = {
                "1": {"id": 1, "name": "Priya Sharma", "voice_id": "shimmer", "gender": "Female", "accent": "Indian English"},
                "2": {"id": 2, "name": "Sarah Johnson", "voice_id": "coral", "gender": "Female", "accent": "US English"},
                "3": {"id": 3, "name": "Arjun Patel", "voice_id": "echo", "gender": "Male", "accent": "Indian English"},
                "4": {"id": 4, "name": "Michael Chen", "voice_id": "alloy", "gender": "Male", "accent": "US English"},
            }
            
            mock_data = mock_interviewers.get(str(interviewer_id))
            if not mock_data:
                logger.warning(f"Interviewer ID {interviewer_id} not found in mocks, defaulting to ID 1")
                mock_data = mock_interviewers.get("1")
            
            
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


        
        
        
        parsed_skills = []
        if skills:
            try:
                parsed_skills = json.loads(skills)
                if not isinstance(parsed_skills, list):
                     logger.warning("Skills input is not a list, converting to list")
                     parsed_skills = [str(parsed_skills)]
            except Exception as e:
                logger.error(f"Failed to parse skills JSON: {e}")
                
                parsed_skills = [s.strip() for s in skills.split(',')] if ',' in skills else [skills]

        interview_role = role_title
        
        
        final_questions_list = []
        parsed_questions = []
        questions_context_str = ""
        
        if questions:
            parsed_questions = []
            try:
                # Try parsing as JSON first
                parsed_questions = json.loads(questions)
            except Exception:
                # Fallback: Treat as raw string
                logger.debug("Failed to parse questions as JSON, treating as plain text")
                parsed_questions = questions

            if isinstance(parsed_questions, list):
                # Handle List (JSON array)
                for q in parsed_questions:
                    if isinstance(q, dict) and "question" in q:
                        final_questions_list.append({
                            "question_text": q["question"],
                            "type": q.get("type", "general"),
                            "question_id": str(uuid.uuid4())
                        })
                    elif isinstance(q, str):
                        final_questions_list.append({
                            "question_text": q,
                            "type": "general",
                            "question_id": str(uuid.uuid4())
                        })
            elif isinstance(parsed_questions, str):
                # Handle String (Split by newlines)
                lines = [line.strip() for line in parsed_questions.split('\n') if line.strip()]
                for line in lines:
                    final_questions_list.append({
                        "question_text": line,
                        "type": "general",
                        "question_id": str(uuid.uuid4())
                    })
        
        
        if final_questions_list:
            q_texts = []
            for i, q in enumerate(final_questions_list):
                 q_type = f"[{q['type']}] " if q.get('type') != 'general' else ""
                 q_texts.append(f"{i+1}. {q_type}{q['question_text']}")
            questions_context_str = "\n".join(q_texts)


        
        final_job_description = job_description or "Standard core role requirements."
        if parsed_skills:
            final_job_description += f"\n\nRequired Skills:\n{', '.join(parsed_skills)}"

        
        system_instructions = self._create_system_instructions(
            role=interview_role,
            duration=duration_minutes,
            job_description=final_job_description,
            mandatory_questions=questions_context_str
        )

        
        ephemeral_token = await self._create_openai_session(
            system_instructions=system_instructions,
            voice=interviewer.voice_id
        )

        
        is_compatible = microphone_status and camera_status
        tested_at = datetime.now(timezone.utc)

        
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            system_instruction_tokens = len(encoding.encode(system_instructions))
        except:
            
            system_instruction_tokens = len(system_instructions) // 4

        
        session_data = {
            "_id": session_id,
            "session_id": session_id,
            "front_end_session_id": front_end_session_id,
            "candidate_id": candidate_id,
            
            "role_title": interview_role, 
            "interview_role": interview_role,
            "company_name": "Acelucid Technologies Pvt. Ltd.",
            "interview_round": "HR Screening",
            "duration": duration_minutes,
            "duration_minutes": duration_minutes,
            "interviewer_id": interviewer.id,
            "interviewer_name": interviewer.name,
            "voice": interviewer.voice_id,
            "status": "initialized",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "job_description": job_description,
            "conversation": [],
            "compatibility_test": {
                "microphone_status": microphone_status,
                "camera_status": camera_status,
                "is_compatible": is_compatible,
                "tested_at": tested_at
            },
            "token_usage": {
                "system_instructions_tokens": system_instruction_tokens,
                "realtime_api_tokens": 0,
                "evaluation_tokens": 0,
                "total_tokens": system_instruction_tokens,
                "estimated_cost_usd": 0.0
            },
            "skills": parsed_skills,
            "questions": final_questions_list,
            "passing_score": passing_score, 
            "token": token,  
        }

        if mongodb_collection is not None:
            await self.mongo_repo.create_session(mongodb_collection, session_data)

        
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()

        return {
            "session_id": session_id,
            "ephemeral_token": ephemeral_token,
            "openai_api_url": "https://api.openai.com/v1/realtime",
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
                "duration": duration_minutes,
                "type": "conversational"
            }
        }

    async def _upload_resume_to_s3(self, resume_file: UploadFile, session_id: str) -> Optional[str]:
        """Upload resume to S3 and return URL"""
        try:
            
            file_extension = os.path.splitext(resume_file.filename)[1]
            s3_key = f"ai-interview/resumes/{session_id}/{uuid.uuid4()}{file_extension}"

            
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
            
            s3_url = await self._upload_resume_to_s3(resume_file, session_id)
            if not s3_url:
                print("S3 upload failed, proceeding with extraction anyway")

            
            os.makedirs("temp_resumes", exist_ok=True)
            os.makedirs("temp_output", exist_ok=True)

            temp_file_path = f"temp_resumes/resume_{session_id}_{resume_file.filename}"
            temp_output_dir = "temp_output"

            
            await resume_file.seek(0)
            async with aiofiles.open(temp_file_path, "wb") as f:
                content = await resume_file.read()
                await f.write(content)

            
            from extractipy.file_extractors import FileExtractor
            extractor = FileExtractor(verbose=False)
            extracted_data = await extractor.extract_data_from_file(temp_file_path, temp_output_dir)
            resume_context = extracted_data.get('text', '')

            
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_error:
                    print(f"Cleanup warning: {str(cleanup_error)}")

            
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
                            "threshold": 0.5,  
                            "prefix_padding_ms": 300,  
                            "silence_duration_ms": 4000  
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
        """
        Get interview flow.
        Now simplified to always use the main instructions which define the HR Screening flow.
        """
        logger.info(f"Using unified HR Screening flow for round: {interview_round}")
        return ""

    def _create_system_instructions(
        self,
        role: str,
        duration: int,
        job_description: Optional[str] = None,
        mandatory_questions: Optional[str] = None
    ) -> str:
        """Create system instructions using HR_SCREENING_SYSTEM_PROMPT"""

        
        questions_context = mandatory_questions if mandatory_questions else "No specific pre-defined questions."

        
        instructions = HR_SCREENING_SYSTEM_PROMPT.format(
            role=role,
            duration=f"{duration} minutes",
            job_description_context=job_description or "No specific job description provided.",
            questions_context=questions_context
        )

        
        logger.info(f"System instructions created from HR_SCREENING_SYSTEM_PROMPT - Role: {role}, Duration: {duration} mins")

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

        
        try:
            conversation = json.loads(conversation_json)
            if not isinstance(conversation, list):
                raise ValueError("Conversation must be an array")
        except json.JSONDecodeError:
            raise CustomException("Invalid JSON format for conversation", status_code=status.HTTP_400_BAD_REQUEST)

        agent = AIInterviewAgent()
        processed_conversation = await agent.process_conversation(conversation)

        
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            total_conversation_tokens = 0
            total_audio_duration_seconds = 0

            for message in conversation:
                
                if isinstance(message, dict):
                    
                    text_content = message.get("content", "") or message.get("transcript", "")
                    if text_content:
                        total_conversation_tokens += len(encoding.encode(text_content))

                    
                    audio_duration = (
                        message.get("audio_duration_ms", 0) or
                        message.get("audio_duration", 0) or
                        0
                    )
                    if audio_duration:
                        
                        if audio_duration > 1000:
                            total_audio_duration_seconds += audio_duration / 1000
                        else:
                            total_audio_duration_seconds += audio_duration

            
            
            session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
            if session and total_audio_duration_seconds == 0:
                
                interview_duration_minutes = session.get("duration", 0)
                total_audio_duration_seconds = interview_duration_minutes * 60
                logger.info(f"Using interview duration as audio duration: {interview_duration_minutes} minutes")

        except Exception as e:
            logger.warning(f"Error calculating conversation tokens: {e}")
            total_conversation_tokens = len(str(conversation)) // 4  

            
            session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
            if session:
                interview_duration_minutes = session.get("duration", 0)
                total_audio_duration_seconds = interview_duration_minutes * 60
            else:
                total_audio_duration_seconds = 0

        
        audio_duration_minutes = total_audio_duration_seconds / 60
        whisper_cost = audio_duration_minutes * 0.006

       
        estimated_input_tokens = total_conversation_tokens // 2
        estimated_output_tokens = total_conversation_tokens - estimated_input_tokens

        realtime_input_cost = (estimated_input_tokens / 1_000_000) * 0.60
        realtime_output_cost = (estimated_output_tokens / 1_000_000) * 2.40
        realtime_api_cost = realtime_input_cost + realtime_output_cost

        
        session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)
        current_token_usage = session.get("token_usage", {}) if session else {}

        
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

        
        interim_total_tokens = (
            updated_token_usage["system_instructions_tokens"] +
            updated_token_usage["realtime_api_tokens"]
        )
        interim_total_cost = whisper_cost + realtime_api_cost

        updated_token_usage["total_tokens"] = interim_total_tokens
        updated_token_usage["total_cost_usd"] = round(interim_total_cost, 6)

        
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

    async def evaluate_interview(self, mongodb_collection, session_id: str, passing_score: Optional[int] = None):
        """Evaluate completed interview session"""
        if mongodb_collection is None:
            raise CustomException("Database not available", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        session = await self.mongo_repo.get_session_by_id(mongodb_collection, session_id)

        if not session:
            raise CustomException("Session not found", status_code=status.HTTP_404_NOT_FOUND)

        
        if session.get("status") not in ["completed", "evaluated"]:
            raise CustomException("Interview not completed yet", status_code=status.HTTP_400_BAD_REQUEST)

       
        conversation = session.get("conversation", [])

        if not conversation:
            raise CustomException(
                "No conversation data found. Cannot evaluate empty interview.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        
        from services.ai_interview_management.realtime_interview_evaluation_service import RealtimeInterviewEvaluationService
        evaluation_service = RealtimeInterviewEvaluationService()

        
        evaluation_data = await evaluation_service.evaluate_interview_session(
            session_data=session,
            conversation_transcript=conversation,
            passing_score=passing_score
        )

        
        await self.mongo_repo.save_evaluation(mongodb_collection, session_id, evaluation_data)

        
        front_end_id = session.get("front_end_session_id")
        session_token = session.get("token", "")  
        if front_end_id:
            
            result_status = evaluation_data.get("overall_evaluation", {}).get("result", "fail")
            
            total_score = evaluation_data.get("overall_evaluation", {}).get("total_score", 0.0)
            
            
            import asyncio
            asyncio.create_task(self._notify_external_backend(
                front_end_session_id=front_end_id,
                status=str(result_status),
                score=total_score,
                token=session_token
            ))

        return evaluation_data

    async def get_interviewers(self, ai_interviewers_collection) -> list[dict]:
        """
        Get list of available interviewers with voice models from database.
        Returns 2 female and 2 male interviewers with their video assets.

        Available OpenAI voices: alloy, ash, ballad, coral, echo, sage, shimmer, verse
        """
        try:
            repo = AIInterviewRolesRepository(ai_interviewers_collection)
            interviewers_db = await repo.get_all_interviewers()

            if interviewers_db and len(interviewers_db) > 0:
                
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



    async def get_interview_details_by_session_id(
        self,
        mongodb_collection,
        session_id: str
    ) -> dict:
        """
        Get complete interview details by session ID.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to fetch details for

        Returns:
            Complete interview details including evaluation
        """
        
        session = await self.mongo_repo.get_session_by_id(
            mongodb_collection, session_id
        )

        if not session:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

        
        evaluation = session.get("evaluation", {})
        overall_evaluation = evaluation.get("overall_evaluation", {})
        questions = evaluation.get("questions", [])

        
        interviewer_name = session.get("interviewer_name", "Unknown")
        interviewer_initials = "".join([word[0].upper() for word in interviewer_name.split()[:2]])

        
        interview_details = {
            "session_id": session.get("session_id"),
            "front_end_session_id": session.get("front_end_session_id"),
            "candidate_id": session.get("candidate_id"),
            "role_title": session.get("interview_role"),
            "company_name": session.get("company_name"),
            "interview_round": session.get("interview_round"),
            "interviewer_name": interviewer_name,
            "interviewer_initials": interviewer_initials,
            "duration_minutes": session.get("duration_minutes", session.get("duration")),
            "status": session.get("status"),
            "created_at": session.get("created_at"),
            "ended_at": session.get("ended_at"),
            "evaluated_at": evaluation.get("evaluated_at")
        }

        return interview_details

    async def get_evaluation_by_session_id(
        self,
        mongodb_collection,
        front_end_session_id: int,
        candidate_id: int
    ) -> dict:
        """
        Get only the evaluation object by front_end_session_id and candidate_id.
        
        Args:
            mongodb_collection: MongoDB collection for interviews
            front_end_session_id: Front end session ID
            candidate_id: Candidate ID
            
        Returns:
            Evaluation object with total_score from overall_evaluation
        """
        session = await self.mongo_repo.get_session_by_frontend_and_candidate(
            mongodb_collection, 
            front_end_session_id, 
            candidate_id
        )
        
        if not session:
            raise CustomException("Session not found", status_code=status.HTTP_404_NOT_FOUND)
        
        evaluation = session.get("evaluation")
        
        if not evaluation:
            raise CustomException("Evaluation not found for this session", status_code=status.HTTP_404_NOT_FOUND)
        
        # Ensure the total_score from overall_evaluation is exposed at the top level
        # This fixes the issue where API was showing performance breakdown scores instead
        if "overall_evaluation" in evaluation and "total_score" in evaluation["overall_evaluation"]:
            evaluation["total_score"] = evaluation["overall_evaluation"]["total_score"]
            
        return evaluation

    async def delete_interview_by_session_id(
        self,
        mongodb_collection,
        session_id: str
    ) -> dict:
        """
        Soft delete an interview by session ID.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to delete

        Returns:
            Success message

        Raises:
            CustomException: If session not found
        """
        
        result = await self.mongo_repo.soft_delete_session_by_id(
            mongodb_collection, session_id
        )

        
        if result.matched_count == 0:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

    async def hard_delete_interview_session(
        self,
        mongodb_collection,
        session_id: str
    ) -> dict:
        """
        Hard delete an interview session by session ID.
        This permanently removes the record from the database.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to delete

        Returns:
            Success message

        Raises:
            CustomException: If session not found
        """
        
        result = await self.mongo_repo.hard_delete_session_by_id(
            mongodb_collection, session_id
        )

        
        if result.deleted_count == 0:
            raise CustomException(
                "Interview session not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return {
            "session_id": session_id,
            "message": "Interview permanently deleted successfully"
        }

    async def get_token_usage_summary(
        self,
        mongodb_collection,
        session_id: str
    ) -> dict:
        """
        Get token usage and cost summary for a specific interview session.

        Args:
            mongodb_collection: MongoDB collection for interviews
            session_id: Session ID to get token usage for

        Returns:
            Token usage breakdown and cost information

        Raises:
            CustomException: If session not found
        """
        
        session = await self.mongo_repo.get_session_by_id(
            mongodb_collection, session_id
        )

        if not session:
            raise CustomException(
                "Interview session not found or you don't have access to it",
                status_code=status.HTTP_404_NOT_FOUND
            )

        
        token_usage = session.get("token_usage", {})

        
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

                
                estimated_input_tokens = total_conversation_tokens // 2
                estimated_output_tokens = total_conversation_tokens - estimated_input_tokens
                realtime_input_cost = (estimated_input_tokens / 1_000_000) * 0.60
                realtime_output_cost = (estimated_output_tokens / 1_000_000) * 2.40
                realtime_api_cost = realtime_input_cost + realtime_output_cost

                
                token_usage["realtime_api_tokens"] = total_conversation_tokens
                token_usage["realtime_api_input_tokens"] = estimated_input_tokens
                token_usage["realtime_api_output_tokens"] = estimated_output_tokens
                token_usage["realtime_api_cost_usd"] = round(realtime_api_cost, 6)

                
                if token_usage.get("realtime_audio_duration_seconds", 0) == 0:
                    interview_duration_minutes = session.get("duration", 0)
                    audio_duration_seconds = interview_duration_minutes * 60
                    whisper_cost = (audio_duration_seconds / 60) * 0.006

                    token_usage["realtime_audio_duration_seconds"] = audio_duration_seconds
                    token_usage["whisper_transcription_cost_usd"] = round(whisper_cost, 6)

                    
                    total_cost = (
                        token_usage.get("realtime_api_cost_usd", 0.0) +
                        token_usage.get("whisper_transcription_cost_usd", 0.0) +
                        token_usage.get("evaluation_cost_usd", 0.0)
                    )
                    token_usage["total_cost_usd"] = round(total_cost, 6)

                    
                    total_tokens = (
                        token_usage.get("system_instructions_tokens", 0) +
                        token_usage.get("realtime_api_tokens", 0) +
                        token_usage.get("evaluation_total_tokens", 0)
                    )
                    token_usage["total_tokens"] = total_tokens

                logger.info(f"Recalculated tokens for session {session.get('session_id')}: {total_conversation_tokens} tokens, Realtime cost: ${realtime_api_cost:.6f}, Whisper: ${whisper_cost:.6f}")

            except Exception as e:
                logger.warning(f"Error recalculating conversation tokens: {e}")

        
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
