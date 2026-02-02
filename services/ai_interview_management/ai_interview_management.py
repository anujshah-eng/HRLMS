from fastapi import status
from repository.ai_interview_management import AIInterviewRolesRepository
from dto.request_dto.ai_interview import QuestionCreateDTO, QuestionUpdateDTO
from dto.response_dto.ai_interview import AIInterviewRoleResponseDTO, InterviewQuestionResponseDTO
from custom_utilities.custom_exception import CustomException

class AIInterviewRolesService:
    def __init__(self, repo: AIInterviewRolesRepository = AIInterviewRolesRepository()):
        self.repo = repo

    async def get_all_roles(self):
        roles = await self.repo.get_all_roles()
        return [AIInterviewRoleResponseDTO.model_validate(role) for role in roles]

    async def get_role_by_id(self, role_id: int):
        role = await self.repo.get_role_by_id(role_id)
        if not role:
            raise CustomException("Role not found", status_code=status.HTTP_404_NOT_FOUND)
        return AIInterviewRoleResponseDTO.model_validate(role)

    async def create_role(self, dto: AIInterviewRoleResponseDTO):
        if await self.repo.get_role_by_title(dto.title):
            raise CustomException("Role with this title already exists.", status_code=status.HTTP_400_BAD_REQUEST)
        role = await self.repo.create_role(dto.title, dto.description)
        return AIInterviewRoleResponseDTO.model_validate(role)

    async def update_role(self, role_id: int, dto: AIInterviewRoleResponseDTO):
        existing = await self.repo.get_role_by_title(dto.title)
        if existing and existing.id != role_id:
            raise CustomException("Role with this title already exists.", status_code=status.HTTP_400_BAD_REQUEST)
        role = await self.repo.update_role(role_id, dto.title, dto.description)
        if not role:
            raise CustomException("Role not found", status_code=status.HTTP_404_NOT_FOUND)
        return AIInterviewRoleResponseDTO.model_validate(role)

    async def delete_role(self, role_id: int):
        deleted = await self.repo.delete_role(role_id)
        if not deleted:
            raise CustomException("Role not found", status_code=status.HTTP_404_NOT_FOUND)
        return True

    async def create_question(self, dto: QuestionCreateDTO):
        """Create a new interview question"""
        question = await self.repo.create_question(
            question_text=dto.question_text,
            topic=dto.topic,
            role_id=dto.role_id
        )
        return InterviewQuestionResponseDTO.model_validate(question)

    async def get_question_by_id(self, question_id: int):
        """Get question by ID"""
        question = await self.repo.get_question_by_id(question_id)
        if not question:
            raise CustomException("Question not found", status_code=status.HTTP_404_NOT_FOUND)
        return InterviewQuestionResponseDTO.model_validate(question)

    async def get_all_questions(self, role_id: int | None = None):
        """Get all active questions"""
        questions = await self.repo.get_all_questions(role_id=role_id, is_active=True)
        return [InterviewQuestionResponseDTO.model_validate(q) for q in questions]

    async def update_question(self, question_id: int, dto: QuestionUpdateDTO):
        """Update an existing question"""
        question = await self.repo.update_question(
            question_id=question_id,
            question_text=dto.question_text,
            topic=dto.topic,
            role_id=dto.role_id,
            is_active=dto.is_active
        )
        if not question:
            raise CustomException("Question not found", status_code=status.HTTP_404_NOT_FOUND)
        return InterviewQuestionResponseDTO.model_validate(question)

    async def delete_question(self, question_id: int):
        """Soft delete a question"""
        deleted = await self.repo.delete_question(question_id)
        if not deleted:
            raise CustomException("Question not found", status_code=status.HTTP_404_NOT_FOUND)
        return True


   