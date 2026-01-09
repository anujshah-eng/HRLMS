import os
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from connections.mysql_connection import MySQLResourceManager as DBResourceManager
from models.ai_interview_model import (
    AIInterviewers
)

db_resource_manager = DBResourceManager()

class AIInterviewRolesRepository:
    def __init__(self):
        self.db = db_resource_manager

    async def get_all_interviewers(self):
        """Get all active AI interviewers"""
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewers).filter(AIInterviewers.is_active == True)
                )
                return result.scalars().all()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_interviewer_by_id(self, interviewer_id: int):
        """Get interviewer by ID"""
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewers).filter(
                        AIInterviewers.id == interviewer_id,
                        AIInterviewers.is_active == True
                    )
                )
                return result.scalars().first()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

class RealtimeInterviewMongoRepository:
    """Repository for MongoDB operations for realtime interview sessions"""

    async def create_session(self, mongodb_collection, session_data: dict):
        """Create a new session document in MongoDB"""
        await mongodb_collection.insert_one(session_data)
        return session_data

    async def get_session_by_id(self, mongodb_collection, session_id: str):
        """Get session by session_id"""
        return await mongodb_collection.find_one({"_id": session_id})

    async def get_session_by_frontend_and_candidate(self, mongodb_collection, front_end_session_id: int, candidate_id: int):
        """Get session by front_end_session_id and candidate_id"""
        return await mongodb_collection.find_one({
            "front_end_session_id": front_end_session_id,
            "candidate_id": candidate_id
        })

    async def update_session_status(self, mongodb_collection, session_id: str, status: str):
        """Update session status"""
        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def end_session(self, mongodb_collection, session_id: str):
        """End interview session and mark as completed"""
        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": "completed",
                    "ended_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def update_conversation(self, mongodb_collection, session_id: str, conversation: list):
        """Update conversation transcript for the interview session"""
        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "conversation": conversation,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def update_conversation_and_tokens(
        self,
        mongodb_collection,
        session_id: str,
        conversation: list,
        token_usage: dict
    ):
        """Update conversation transcript and token usage together"""
        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "conversation": conversation,
                    "token_usage": token_usage,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def save_evaluation(self, mongodb_collection, session_id: str, evaluation_data: dict):
        """Save evaluation data to session and update complete token usage with all costs"""
        # Extract token usage from evaluation data
        evaluation_tokens = evaluation_data.get("token_usage", {})

        # Get current session to merge token usage
        session = await mongodb_collection.find_one({"_id": session_id})
        current_token_usage = session.get("token_usage", {}) if session else {}

        # Merge token usage with all components
        updated_token_usage = {
            "system_instructions_tokens": current_token_usage.get("system_instructions_tokens", 0),
            "realtime_api_tokens": current_token_usage.get("realtime_api_tokens", 0),
            "realtime_api_input_tokens": current_token_usage.get("realtime_api_input_tokens", 0),
            "realtime_api_output_tokens": current_token_usage.get("realtime_api_output_tokens", 0),
            "realtime_api_cost_usd": current_token_usage.get("realtime_api_cost_usd", 0.0),
            "realtime_audio_duration_seconds": current_token_usage.get("realtime_audio_duration_seconds", 0),
            "whisper_transcription_cost_usd": current_token_usage.get("whisper_transcription_cost_usd", 0.0),
            "evaluation_input_tokens": evaluation_tokens.get("evaluation_input_tokens", 0),
            "evaluation_output_tokens": evaluation_tokens.get("evaluation_output_tokens", 0),
            "evaluation_total_tokens": evaluation_tokens.get("evaluation_total_tokens", 0),
            "evaluation_cost_usd": evaluation_tokens.get("evaluation_cost_usd", 0.0)
        }

        # Calculate total tokens across entire interview
        total_tokens = (
            updated_token_usage["system_instructions_tokens"] +
            updated_token_usage["realtime_api_tokens"] +
            updated_token_usage["evaluation_total_tokens"]
        )

        # Calculate COMPLETE total cost including ALL components:
        # 1. Realtime API cost (conversation with gpt-4o-mini-realtime-preview)
        # 2. Whisper transcription cost (audio -> text)
        # 3. Evaluation cost (GPT-4o-mini for answer + overall evaluation)
        total_cost = (
            updated_token_usage["realtime_api_cost_usd"] +
            updated_token_usage["whisper_transcription_cost_usd"] +
            updated_token_usage["evaluation_cost_usd"]
        )

        updated_token_usage["total_tokens"] = total_tokens
        # updated_token_usage["total_cost_usd"] = round(total_cost, 6)

        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "evaluation": evaluation_data,
                    "status": "evaluated",
                    "token_usage": updated_token_usage,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def get_session_by_id_and_user(self, mongodb_collection, session_id: str, user_id: str):
        """
        Get session by session_id and user_id to verify ownership.

        Args:
            mongodb_collection: MongoDB collection
            session_id: Session ID to fetch
            user_id: User ID to verify ownership

        Returns:
            Session document if found and owned by user (excluding deleted), None otherwise
        """
        return await mongodb_collection.find_one({
            "session_id": session_id,
            "user_id": user_id,
            "$or": [
                {"is_deleted": {"$exists": False}},
                {"is_deleted": False}
            ]
        })



    async def soft_delete_interview_session(
        self,
        mongodb_collection,
        session_id: str,
        user_id: str
    ):
        """
        Soft delete an interview session by setting is_deleted flag.

        Args:
            mongodb_collection: MongoDB collection
            session_id: Session ID to delete
            user_id: User ID to verify ownership

        Returns:
            Update result from MongoDB
        """
        result = await mongodb_collection.update_one(
            {
                "session_id": session_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc)
                }
            }
        )
        return result

    async def soft_delete_session_by_id(
        self,
        mongodb_collection,
        session_id: str
    ):
        """
        Soft delete an interview session by setting is_deleted flag (without user check).

        Args:
            mongodb_collection: MongoDB collection
            session_id: Session ID to delete

        Returns:
            Update result from MongoDB
        """
        result = await mongodb_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.now(timezone.utc)
                }
            }
        )
    async def hard_delete_session_by_id(
        self,
        mongodb_collection,
        session_id: str
    ):
        """
        Hard delete an interview session from MongoDB.

        Args:
            mongodb_collection: MongoDB collection
            session_id: Session ID to delete

        Returns:
            Delete result from MongoDB
        """
        result = await mongodb_collection.delete_one({"_id": session_id})
        return result
