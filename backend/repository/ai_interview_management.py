import os
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from connections.postgres_connection import DBResourceManager
from models.ai_interview_model import (
    AIInterviewRoles, AIInterviewers, AIInterviewQuestions
)

db_resource_manager = DBResourceManager(db_key=os.getenv("POSTGRES_DB"))

class AIInterviewRolesRepository:
    async def get_all_roles(self):
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(select(AIInterviewRoles))
                return result.scalars().all()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_role_by_id(self, role_id: int):
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewRoles).filter(AIInterviewRoles.id == role_id)
                )
                return result.scalars().first()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_role_by_title(self, title: str):
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewRoles).filter(AIInterviewRoles.title.ilike(title))
                )
                return result.scalars().first()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def create_role(self, title: str, description: str | None):
        try:
            async with db_resource_manager.async_session() as session:
                role = AIInterviewRoles(title=title, description=description)
                session.add(role)
                await session.commit()
                await session.refresh(role)
                return role
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def update_role(self, role_id: int, title: str, description: str | None):
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewRoles).filter(AIInterviewRoles.id == role_id)
                )
                role = result.scalars().first()
                if not role:
                    return None
                role.title = title
                role.description = description
                await session.commit()
                await session.refresh(role)
                return role
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def delete_role(self, role_id: int):
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewRoles).filter(AIInterviewRoles.id == role_id)
                )
                role = result.scalars().first()
                if not role:
                    return False
                await session.delete(role)
                await session.commit()
                return True
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")




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

    async def create_question(self, question_text: str, topic: str | None, role_id: int | None):
        """Create a new interview question"""
        try:
            async with db_resource_manager.async_session() as session:
                question = AIInterviewQuestions(
                    question_text=question_text,
                    topic=topic,
                    role_id=role_id
                )
                session.add(question)
                await session.commit()
                await session.refresh(question)
                return question
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_question_by_id(self, question_id: int):
        """Get question by ID"""
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewQuestions).filter(AIInterviewQuestions.id == question_id)
                )
                return result.scalars().first()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_all_questions(self, role_id: int | None = None, is_active: bool | None = True):
        """Get all questions, optionally filtered by role_id"""
        try:
            async with db_resource_manager.async_session() as session:
                query = select(AIInterviewQuestions)
                
                if is_active is not None:
                    query = query.filter(AIInterviewQuestions.is_active == is_active)
                
                if role_id is not None:
                    query = query.filter(AIInterviewQuestions.role_id == role_id)
                
                query = query.order_by(AIInterviewQuestions.created_at.desc())
                result = await session.execute(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def update_question(self, question_id: int, question_text: str | None, topic: str | None, role_id: int | None, is_active: bool | None):
        """Update a question"""
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewQuestions).filter(AIInterviewQuestions.id == question_id)
                )
                question = result.scalars().first()
                if not question:
                    return None
                
                if question_text is not None:
                    question.question_text = question_text
                if topic is not None:
                    question.topic = topic
                if role_id is not None:
                    question.role_id = role_id

                if is_active is not None:
                    question.is_active = is_active
                
                await session.commit()
                await session.refresh(question)
                return question
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    async def delete_question(self, question_id: int):
        """Soft delete a question by setting is_active to False"""
        try:
            async with db_resource_manager.async_session() as session:
                result = await session.execute(
                    select(AIInterviewQuestions).filter(AIInterviewQuestions.id == question_id)
                )
                question = result.scalars().first()
                if not question:
                    return False
                
                question.is_active = False
                await session.commit()
                return True
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")


    # async def get_languages(self):
    #     async with db_resource_manager.async_session() as session:
    #         q = await session.execute(
    #             select(Languages).where(Languages.is_active == True).order_by(Languages.id)
    #         )
    #         return q.scalars().all()

    # async def get_avatars(self, language_id=None):
    #     async with db_resource_manager.async_session() as session:
    #         stmt = select(Avatars).where(Avatars.is_active == True)

    #         if language_id:
    #             stmt = stmt.where(Avatars.language_id == language_id)

    #         q = await session.execute(stmt)
    #         return q.scalars().all()

class RealtimeInterviewMongoRepository:
    """Repository for MongoDB operations for realtime interview sessions"""

    async def create_session(self, mongodb_collection, session_data: dict):
        """Create a new session document in MongoDB"""
        await mongodb_collection.insert_one(session_data)
        return session_data

    async def get_session_by_id(self, mongodb_collection, session_id: str):
        """Get session by session_id"""
        return await mongodb_collection.find_one({"_id": session_id})

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

    async def get_user_interview_history(
        self,
        mongodb_collection,
        user_id: str,
        search: str = None,
        round_filter: str = None,
        skip: int = 0,
        limit: int = 10
    ):
        """
        Get paginated interview history for a user.

        Args:
            mongodb_collection: MongoDB collection
            user_id: User ID to fetch history for
            search: Search query for role or interviewer name
            round_filter: Filter by interview round
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Tuple of (sessions list, total count)
        """
        # Build base query - exclude deleted interviews
        base_conditions = {
            "user_id": user_id,
            "status": "evaluated",
            "$or": [
                {"is_deleted": {"$exists": False}},
                {"is_deleted": False}
            ]
        }

        # Start with base conditions
        query = base_conditions.copy()

        # Build additional conditions
        additional_conditions = []

        # Add search filter
        if search:
            additional_conditions.append({
                "$or": [
                    {"interview_role": {"$regex": search, "$options": "i"}},
                    {"interviewer_name": {"$regex": search, "$options": "i"}}
                ]
            })

        # Add round filter (exact match)
        if round_filter and round_filter.lower() != "all rounds":
            additional_conditions.append({"interview_round": round_filter})

        # Combine conditions properly
        if additional_conditions:
            is_deleted_condition = query.pop("$or")
            query["$and"] = [
                {"$or": is_deleted_condition}
            ] + additional_conditions

        # Get total count
        total_count = await mongodb_collection.count_documents(query)

        # Fetch sessions
        cursor = mongodb_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        sessions = await cursor.to_list(length=limit)

        return sessions, total_count

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
