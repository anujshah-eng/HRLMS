"""
Realtime Interview Evaluation Service
Evaluates completed real-time interviews and provides comprehensive feedback
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from agents.ai_interview.interview_agent import AIInterviewAgent
from repository.ai_interview_management import AIInterviewRolesRepository

logger = logging.getLogger(__name__)


class RealtimeInterviewEvaluationService:
    """
    Service for evaluating completed real-time interviews.
    Provides question-by-question evaluation and overall performance analysis.
    """

    def __init__(self):
        self.interview_agent = AIInterviewAgent()
        self.repo = AIInterviewRolesRepository()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            return len(encoding.encode(text))
        except:
            # Fallback: ~1 token per 4 characters
            return len(text) // 4

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD based on GPT-4o-mini pricing
        Input: $0.150 per 1M tokens
        Output: $0.600 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 0.150
        output_cost = (output_tokens / 1_000_000) * 0.600
        return round(input_cost + output_cost, 6)

    async def evaluate_interview_session(
        self,
        session_data: Dict,
        conversation_transcript: List[Dict],
        passing_score: Optional[int] = None
    ) -> Dict:
        """
        Evaluate complete interview session with question-by-question and overall analysis.

        Args:
            session_data: Session metadata (role_id, company_id, interview_round, etc.)
            conversation_transcript: List of conversation messages with role and content

        Returns:
            Comprehensive evaluation with questions and overall performance
        """
        try:
            # Extract role and company info
            # role_id = session_data.get("role_id")
            # company_id = session_data.get("company_id")
            interview_round = session_data.get("interview_round", "Technical Round")

            # role = self.repo.get_role_by_id(role_id)
            # company = self.repo.get_company_by_id(company_id)

            # if not role or not company:
            #     raise ValueError("Invalid role or company")

            # Extract Q&A pairs from conversation
            qa_pairs = self._extract_qa_pairs(conversation_transcript["conversation"])

            # Handle case where interview was exited early with no valid answers
            if not qa_pairs or len(qa_pairs) == 0:
                logger.warning("No valid question-answer pairs found. Interview likely exited early.")
                # Return zero score evaluation
                return {
                    "session_id": session_data.get("session_id"),
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "interview_context": {
                        "role": session_data.get("interview_role"),
                        "company": session_data.get("company_name"),
                        "interview_round": interview_round,
                        "duration_minutes": session_data.get("duration", 0),
                        "total_questions": 0
                    },
                    "questions": [],
                    "overall_evaluation": {
                        "total_score": 0,
                        "feedback_label": "Poor",
                        "key_strengths": ["Interview was exited before any questions were answered"],
                        "focus_areas": [
                            "Complete the full interview to receive proper evaluation",
                            "Prepare thoroughly before starting the interview",
                            "Allocate sufficient time for the interview session"
                        ],
                        "performance_breakdown": {
                            "communication": 0,
                            "technical_knowledge": 0,
                            "confidence": 0,
                            "structure": 0
                        }
                    },
                    "token_usage": {
                        "evaluation_input_tokens": 0,
                        "evaluation_output_tokens": 0,
                        "evaluation_total_tokens": 0,
                        "evaluation_cost_usd": 0.0
                    }
                }

            logger.info(f"Evaluating {len(qa_pairs)} questions for session")

            # Track token usage for evaluation
            total_input_tokens = 0
            total_output_tokens = 0

            # Evaluate each question
            question_evaluations = []
            for idx, qa in enumerate(qa_pairs, 1):
                try:
                    # Estimate input tokens for this question evaluation
                    input_text = f"Question: {qa['question']}\nAnswer: {qa['answer']}\nRole: {session_data.get('interview_role')}"
                    question_input_tokens = self._estimate_tokens(input_text)

                    evaluation = await self.interview_agent.evaluate_answer(
                        question_text=qa["question"],
                        expected_answer="",  # Realtime interviews don't have pre-defined expected answers
                        user_answer=qa["answer"],
                        role=session_data.get("interview_role"),
                        interview_round=interview_round,
                        difficulty="Medium"  # Default difficulty for realtime interviews
                    )

                    # Estimate output tokens (evaluation response)
                    output_text = str(evaluation)
                    question_output_tokens = self._estimate_tokens(output_text)

                    # Accumulate tokens
                    total_input_tokens += question_input_tokens
                    total_output_tokens += question_output_tokens

                    # Format question evaluation
                    question_eval = {
                        "question_number": idx,
                        "question": qa["question"],
                        "score": evaluation.get("question_score", 0),
                        "feedback_label": evaluation.get("feedback_label", "Fair"),
                        "user_answer": evaluation.get("user_answer", qa["answer"]),
                        "improved_answer": evaluation.get("improved_answer", ""),
                        "what_went_well": evaluation.get("what_went_well", []),
                        "areas_to_improve": evaluation.get("areas_to_improve", []),
                        "performance_breakdown": {
                            "communication": evaluation.get("performance_breakdown", {}).get("communication", 0),
                            "technical_knowledge": evaluation.get("performance_breakdown", {}).get("technical_knowledge", 0),
                            "confidence": evaluation.get("performance_breakdown", {}).get("confidence", 0),
                            "structure": evaluation.get("performance_breakdown", {}).get("structure", 0)
                        }
                    }

                    question_evaluations.append(question_eval)
                    logger.info(f"Question {idx} evaluated with score: {question_eval['score']}/10")

                except Exception as e:
                    logger.error(f"Error evaluating question {idx}: {str(e)}")
                    # Add placeholder evaluation for failed questions
                    question_evaluations.append({
                        "question_number": idx,
                        "question": qa["question"],
                        "score": 0,
                        "feedback_label": "Error",
                        "user_answer": qa["answer"],
                        "improved_answer": "Evaluation failed",
                        "what_went_well": [],
                        "areas_to_improve": ["Could not evaluate this answer"],
                        "performance_breakdown": {
                            "communication": 0,
                            "technical_knowledge": 0,
                            "confidence": 0,
                            "structure": 0
                        }
                    })

            # Generate overall evaluation
            # Estimate input tokens for overall evaluation
            overall_input_text = f"Role: {session_data.get('interview_role')}\nQuestions: {len(qa_pairs)}\nEvaluations: {str(question_evaluations)[:500]}"
            overall_input_tokens = self._estimate_tokens(overall_input_text)

            overall_evaluation = await self.interview_agent.generate_overall_evaluation(
                role=session_data.get("interview_role"),
                interview_round=interview_round,
                difficulty="Medium",
                num_questions=len(qa_pairs),
                question_evaluations=question_evaluations
            )

            # Estimate output tokens for overall evaluation
            overall_output_text = str(overall_evaluation)
            overall_output_tokens = self._estimate_tokens(overall_output_text)

            # Add overall evaluation tokens
            total_input_tokens += overall_input_tokens
            total_output_tokens += overall_output_tokens

            # Calculate total evaluation tokens and cost
            total_evaluation_tokens = total_input_tokens + total_output_tokens
            evaluation_cost = self._calculate_cost(total_input_tokens, total_output_tokens)

            logger.info(f"Evaluation completed. Tokens used: {total_evaluation_tokens} (Input: {total_input_tokens}, Output: {total_output_tokens}), Cost: ${evaluation_cost}")

            # Build final evaluation response
            evaluation_result = {
                "session_id": session_data.get("session_id"),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "interview_context": {
                    "role": session_data.get("interview_role"),
                    "company":session_data.get("company_name"),
                    "interview_round": interview_round,
                    "duration_minutes": session_data.get("duration", 0),
                    "total_questions": len(qa_pairs)
                },
                "questions": question_evaluations,
                "overall_evaluation": {
                    "total_score": overall_evaluation.get("total_score", 0),
                    "result": ("pass" if passing_score is not None and overall_evaluation.get("total_score", 0) >= passing_score else "fail") if passing_score is not None else None,
                    "feedback_label": overall_evaluation.get("feedback_label", "Fair"),
                    "key_strengths": overall_evaluation.get("key_strengths", []),
                    "focus_areas": overall_evaluation.get("focus_areas", []),
                    "performance_breakdown": {
                        "communication": overall_evaluation.get("performance_breakdown", {}).get("communication", 0),
                        "technical_knowledge": overall_evaluation.get("performance_breakdown", {}).get("technical_knowledge", 0),
                        "confidence": overall_evaluation.get("performance_breakdown", {}).get("confidence", 0),
                        "structure": overall_evaluation.get("performance_breakdown", {}).get("structure", 0)
                    }
                },
                "token_usage": {
                    "evaluation_input_tokens": total_input_tokens,
                    "evaluation_output_tokens": total_output_tokens,
                    "evaluation_total_tokens": total_evaluation_tokens,
                    # "evaluation_cost_usd": evaluation_cost
                }
            }

            logger.info(f"Evaluation completed with overall score: {evaluation_result['overall_evaluation']['total_score']}/100")
            return evaluation_result

        except Exception as e:
            logger.error(f"Error evaluating interview session: {str(e)}")
            raise

    def _extract_qa_pairs(self, conversation: List[Dict]) -> List[Dict]:
        """
        Extract question-answer pairs from conversation transcript.

        Args:
            conversation: List of messages with role and content

        Returns:
            List of Q&A pairs
        """
        qa_pairs = []
        current_question = None

        for message in conversation:
            role = message.get("role", "")
            content = message.get("content", "").strip()

            if not content:
                continue

            # Assistant messages are questions
            if role == "assistant":
                # If we have a pending question without answer, save it
                if current_question and not current_question.get("answer"):
                    # Save question without answer (might be interrupted)
                    current_question["answer"] = "[No answer provided]"
                    qa_pairs.append(current_question)

                # Start new question
                current_question = {
                    "question": content,
                    "answer": None,
                    "question_timestamp": message.get("timestamp")
                }

            # User messages are answers
            elif role == "user" and current_question:
                current_question["answer"] = content
                current_question["answer_timestamp"] = message.get("timestamp")
                qa_pairs.append(current_question)
                current_question = None

        # Handle last question if unanswered
        if current_question and not current_question.get("answer"):
            current_question["answer"] = "[Interview ended before answer]"
            qa_pairs.append(current_question)

        # Filter out pairs without proper answers or placeholder answers
        qa_pairs = [
            qa for qa in qa_pairs
            if qa.get("answer")
            and not qa["answer"].startswith("[")
            and qa["answer"].strip() != ""
            and len(qa["answer"].strip()) > 3  # At least a few characters
        ]

        return qa_pairs
