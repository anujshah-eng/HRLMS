"""AI Interview Agent - Handles question generation and answer evaluation"""

import json
import logging
import re
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_fixed

from agents.ai_interview.system_prompts.interview_prompts import (
    QUESTION_GENERATOR_PROMPT,
    EXTRACT_QA_PROMPT,
    ANSWER_EVALUATOR_PROMPT,
    OVERALL_PERFORMANCE_EVALUATOR_PROMPT
)

logger = logging.getLogger(__name__)


class AIInterviewAgent:
    """Agent for generating interview questions and evaluating answers"""

    def __init__(self, model: str = "gpt-4o-mini", conversation_processor_model: str = "gpt-4o-mini"):
        """
        Initialize the AI Interview Agent with OpenAI models
        
        Args:
            model: Model for question generation and evaluation
            conversation_processor_model: Model for processing conversations (default: o3-mini)
        """
        self.llm = ChatOpenAI(model=model, temperature=0.7)
        self.evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.conversation_processor_llm = ChatOpenAI(model=conversation_processor_model)

    async def generate_questions(
        self,
        role: str,
        interview_round: str,
        difficulty: str,
        num_questions: int = 5,
        company_name: str | None = None,
        resume_text: str | None = None,
        job_description: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions based on role, round, and context

        NOTE: This method is OPTIONAL and used only if you want to pre-generate
        questions before the interview. For duration-based interviews where AI
        asks questions dynamically, you DON'T need to call this method.

        Args:
            role: Job role (e.g., "Software Engineer")
            interview_round: Type of round (e.g., "Technical Interview")
            difficulty: Difficulty level ("Easy", "Medium", "Hard")

            company_name: Target company name (optional)
            resume_text: Candidate's resume content (optional)
            job_description: Job description text (optional)

        Returns:
            List of question dictionaries with expected answers
        """
        try:
            # Build context strings
            company_context = f" at {company_name}" if company_name else ""
            resume_context = f"Candidate's Resume:\n{resume_text}\n" if resume_text else ""
            job_description_context = f"Job Description:\n{job_description}\n" if job_description else ""

            # Format prompt
            prompt_text = QUESTION_GENERATOR_PROMPT.format(
                difficulty=difficulty,
                interview_round=interview_round,
                role=role,
                company_context=company_context,
                num_questions=num_questions,
                resume_context=resume_context,
                job_description_context=job_description_context
            )

            # Generate questions
            response = await self.llm.ainvoke([HumanMessage(content=prompt_text)])

            # Parse JSON response
            questions_json = response.content.strip()

            # Remove markdown code blocks if present
            if questions_json.startswith("```json"):
                questions_json = questions_json.replace("```json", "").replace("```", "").strip()
            elif questions_json.startswith("```"):
                questions_json = questions_json.replace("```", "").strip()

            questions = json.loads(questions_json)

            # Ensure each question has required fields and add IDs
            for idx, question in enumerate(questions):
                question['question_id'] = f"q_{idx + 1}"
                question.setdefault('order', idx + 1)
                question.setdefault('topic', 'General')

            logger.info(f"Generated {len(questions)} questions for {role} - {interview_round}")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Response content: {response.content[:500]}")
            raise Exception(f"Invalid JSON response from AI: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise

    def _normalize_input(self, raw_conversation: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Normalize input conversation by removing timestamps and extra fields
        
        Args:
            raw_conversation: Raw conversation with possible timestamp fields
            
        Returns:
            Normalized conversation with only 'role' and 'content'
        """
        normalized = []
        for msg in raw_conversation:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                normalized.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        return normalized

    def _clean_llm_output(self, text: str) -> str:
        """
        Clean LLM output to extract pure JSON
        Removes markdown code blocks and extracts JSON object
        
        Args:
            text: Raw LLM response text
            
        Returns:
            Cleaned JSON string
        """
        if not text:
            return ""

        text = text.strip()

        # Remove ```json ... ``` or ``` ... ``` wrappers
        if text.startswith("```"):
            text = re.sub(r"^```(json)?", "", text)
            text = text.replace("```", "").strip()

        # Extract JSON object if extra text exists
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return text

    def _validate_output(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the output has the correct structure
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        # Check if 'conversation' key exists
        if "conversation" not in data:
            return False
        
        conversation = data["conversation"]
        
        # Validate conversation is a list
        if not isinstance(conversation, list):
            return False
        
        # Validate each message in the conversation
        for i, msg in enumerate(conversation):
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["assistant", "user"]:
                return False
            if not isinstance(msg["content"], str):
                return False
            
            # Check alternating pattern (assistant, user, assistant, user, ...)
            if i % 2 == 0:  # Even indices should be assistant
                if msg["role"] != "assistant":
                    logger.warning(f"Expected assistant at index {i}, got {msg['role']}")
            else:  # Odd indices should be user
                if msg["role"] != "user":
                    logger.warning(f"Expected user at index {i}, got {msg['role']}")

        return True

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def _extract_qa_pairs_from_conversation(self, raw_conversation: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Internal method to extract Q&A pairs using LLM

        Args:
            raw_conversation: List of conversation messages (normalized)

        Returns:
            Dictionary with 'conversation' key containing flat array of messages

        Raises:
            ValueError: If LLM output is malformed
        """
        # Convert messages into readable format
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in raw_conversation
        ])

        # Create prompt using the imported EXTRACT_QA_PROMPT
        extract_prompt = ChatPromptTemplate.from_template(EXTRACT_QA_PROMPT)
        formatted_prompt = extract_prompt.format_messages(conversation=conversation_text)

        # Invoke LLM
        response = await self.conversation_processor_llm.ainvoke(formatted_prompt)
        raw_output = response.content or ""

        # Clean and parse response
        cleaned_output = self._clean_llm_output(raw_output)

        # Parse JSON strictly
        try:
            parsed_json = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nRaw:\n{raw_output}\nCleaned:\n{cleaned_output}")
            raise ValueError(
                f"Malformed JSON from LLM.\nRaw:\n{raw_output}\nCleaned:\n{cleaned_output}"
            )

        if not isinstance(parsed_json, dict):
            logger.error(f"Expected dict but got {type(parsed_json)}")
            raise ValueError("Output must be a JSON object with 'conversation' key.")

        # Validate output structure
        if not self._validate_output(parsed_json):
            logger.error(f"Invalid output structure: {parsed_json}")
            raise ValueError("Output does not match required format")

        conversation_length = len(parsed_json.get("conversation", []))
        logger.info(f"Successfully extracted {conversation_length // 2} Q&A pairs")

        return parsed_json

    async def process_conversation(
        self,
        raw_conversation: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process raw interview conversation to extract Q&A pairs in flat conversation format

        This is the PRIMARY method for duration-based interviews where:
        1. Interview happens for a specified duration (e.g., 30 minutes)
        2. AI asks questions dynamically during the conversation
        3. After duration ends, this method extracts all Q&A pairs
        4. Number of questions is NOT known beforehand

        Args:
            raw_conversation: List of messages with 'role', 'content', and optional 'timestamp'
                            Example: [
                                {
                                    'role': 'user',
                                    'content': 'Hello',
                                    'timestamp': '2025-12-01T05:47:03.828Z'
                                },
                                {
                                    'role': 'assistant',
                                    'content': 'Why don't we start...',
                                    'timestamp': '2025-12-01T05:47:05.327Z'
                                },
                                ...
                            ]

        Returns:
            Dictionary with 'conversation' array in flat format:
            {
                "conversation": [
                    {"role": "assistant", "content": "question text"},
                    {"role": "user", "content": "user answer"},
                    {"role": "assistant", "content": "next question"},
                    {"role": "user", "content": "next answer"},
                    ...
                ]
            }

        Raises:
            ValueError: If conversation is empty or invalid
        """
        try:
            # Validate input
            if not raw_conversation:
                logger.warning("Empty conversation provided, returning empty conversation")
                return {"conversation": []}

            if not isinstance(raw_conversation, list):
                logger.error(f"Invalid conversation type: {type(raw_conversation)}")
                raise ValueError("raw_conversation must be a list")

            logger.info(f"Processing conversation with {len(raw_conversation)} messages")

            # Normalize input (remove timestamps and extra fields)
            normalized_conversation = self._normalize_input(raw_conversation)

            if not normalized_conversation:
                logger.warning("No valid messages after normalization")
                return {"conversation": []}

            # Extract Q&A pairs using LLM (returns in flat conversation format)
            result = await self._extract_qa_pairs_from_conversation(normalized_conversation)

            logger.info(f"Successfully processed conversation")
            return result

        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            raise

    async def evaluate_answer(
        self,
        question_text: str,
        expected_answer: str,
        user_answer: str,
        role: str,
        interview_round: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer to an interview question

        Args:
            question_text: The question asked
            expected_answer: Expected answer/key points
            user_answer: Candidate's actual answer
            role: Job role
            interview_round: Interview round type
            difficulty: Difficulty level

        Returns:
            Dictionary with evaluation scores and feedback
        """
        try:
            # Format prompt
            prompt_text = ANSWER_EVALUATOR_PROMPT.format(
                difficulty=difficulty,
                interview_round=interview_round,
                role=role,
                question_text=question_text,
                expected_answer=expected_answer,
                user_answer=user_answer
            )

            # Evaluate answer
            response = await self.evaluator_llm.ainvoke([HumanMessage(content=prompt_text)])

            # Parse JSON response
            evaluation_json = response.content.strip()

            # Remove markdown code blocks if present
            if evaluation_json.startswith("```json"):
                evaluation_json = evaluation_json.replace("```json", "").replace("```", "").strip()
            elif evaluation_json.startswith("```"):
                evaluation_json = evaluation_json.replace("```", "").strip()

            evaluation = json.loads(evaluation_json)

            logger.info(f"Evaluated answer with overall score: {evaluation.get('overall_score', 0)}")
            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.error(f"Response content: {response.content[:500]}")
            raise Exception(f"Invalid JSON response from evaluator: {str(e)}")
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            raise

    async def generate_overall_evaluation(
        self,
        role: str,
        interview_round: str,
        difficulty: str,
        num_questions: int,
        question_evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate overall performance evaluation from individual question evaluations

        Args:
            role: Job role
            interview_round: Interview round type
            difficulty: Difficulty level
            num_questions: Total number of questions
            question_evaluations: List of individual question evaluation results

        Returns:
            Dictionary with overall performance metrics
        """
        try:
            # Format question evaluations for prompt
            evaluations_text = json.dumps(question_evaluations, indent=2)

            # Format prompt
            prompt_text = OVERALL_PERFORMANCE_EVALUATOR_PROMPT.format(
                role=role,
                interview_round=interview_round,
                difficulty=difficulty,
                num_questions=num_questions,
                question_evaluations=evaluations_text
            )

            # Generate overall evaluation
            response = await self.evaluator_llm.ainvoke([HumanMessage(content=prompt_text)])

            # Parse JSON response
            evaluation_json = response.content.strip()

            # Remove markdown code blocks if present
            if evaluation_json.startswith("```json"):
                evaluation_json = evaluation_json.replace("```json", "").replace("```", "").strip()
            elif evaluation_json.startswith("```"):
                evaluation_json = evaluation_json.replace("```", "").strip()

            overall_evaluation = json.loads(evaluation_json)

            logger.info(f"Generated overall evaluation with score: {overall_evaluation.get('overall_percentage', 0)}%")
            return overall_evaluation

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse overall evaluation JSON: {e}")
            logger.error(f"Response content: {response.content[:500]}")
            raise Exception(f"Invalid JSON response from evaluator: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating overall evaluation: {e}")
            raise