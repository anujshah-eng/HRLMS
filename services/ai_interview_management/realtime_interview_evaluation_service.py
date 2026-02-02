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
            
            if passing_score is None:
                passing_score = session_data.get("passing_score")
            
           
            interview_round = session_data.get("interview_round", "Technical Round")

            

            qa_pairs = self._extract_qa_pairs(conversation_transcript["conversation"])

            
            if not qa_pairs or len(qa_pairs) == 0:
                logger.warning("No valid question-answer pairs found. Interview likely exited early.")
                
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

            
            total_input_tokens = 0
            total_output_tokens = 0

           
            question_evaluations = []
            for idx, qa in enumerate(qa_pairs, 1):
                try:
                    
                    input_text = f"Question: {qa['question']}\nAnswer: {qa['answer']}\nRole: {session_data.get('interview_role')}"
                    question_input_tokens = self._estimate_tokens(input_text)

                    evaluation = await self.interview_agent.evaluate_answer(
                        question_text=qa["question"],
                        expected_answer="",  
                        user_answer=qa["answer"],
                        role=session_data.get("interview_role"),
                        interview_round=interview_round,
                        difficulty="Medium"  
                    )

                    
                    output_text = str(evaluation)
                    question_output_tokens = self._estimate_tokens(output_text)

                    
                    total_input_tokens += question_input_tokens
                    total_output_tokens += question_output_tokens

                    
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

           
            
            overall_input_text = f"Role: {session_data.get('interview_role')}\nQuestions: {len(qa_pairs)}\nEvaluations: {str(question_evaluations)[:500]}"
            overall_input_tokens = self._estimate_tokens(overall_input_text)

            overall_evaluation = await self.interview_agent.generate_overall_evaluation(
                role=session_data.get("interview_role"),
                interview_round=interview_round,
                difficulty="Medium",
                num_questions=len(qa_pairs),
                question_evaluations=question_evaluations
            )

            
            overall_output_text = str(overall_evaluation)
            overall_output_tokens = self._estimate_tokens(overall_output_text)

            
            total_input_tokens += overall_input_tokens
            total_output_tokens += overall_output_tokens

           
            total_evaluation_tokens = total_input_tokens + total_output_tokens
            evaluation_cost = self._calculate_cost(total_input_tokens, total_output_tokens)

            logger.info(f"Evaluation completed. Tokens used: {total_evaluation_tokens} (Input: {total_input_tokens}, Output: {total_output_tokens}), Cost: ${evaluation_cost}")

            
            duration_minutes = session_data.get("duration", 0)
            minimum_questions_required = duration_minutes / 2
            questions_asked = len(qa_pairs)
            
            
            interview_complete = questions_asked >= minimum_questions_required
            
            if interview_complete:
                
                adjusted_total_score = overall_evaluation.get("total_score", 0)
                completeness_status = "Complete"
                completeness_message = f"Interview completed successfully with {questions_asked} questions."
            else:
                
                total_scored_points = sum(q.get("score", 0) for q in question_evaluations)
                max_possible_points = minimum_questions_required * 10  
                
                
                adjusted_total_score = (total_scored_points / max_possible_points) * 100 if max_possible_points > 0 else 0
                completeness_status = "Incomplete"
                completeness_message = f"Interview incomplete. Only {questions_asked}/{minimum_questions_required:.1f} minimum questions covered."
                
                logger.warning(f"Interview ended early: {questions_asked} questions vs {minimum_questions_required:.1f} minimum required. Adjusted score: {adjusted_total_score:.1f}%")

            
            evaluation_result = {
                "session_id": session_data.get("session_id"),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "interview_context": {
                    "role": session_data.get("interview_role"),
                    "company":session_data.get("company_name"),
                    "interview_round": interview_round,
                    "duration_minutes": session_data.get("duration", 0),
                    "total_questions": len(qa_pairs),
                    "minimum_questions_required": minimum_questions_required,
                    "completeness_status": completeness_status,
                    "completeness_message": completeness_message
                },
                "questions": question_evaluations,
                "overall_evaluation": {
                    "total_score": round(adjusted_total_score, 2),
                    "result": (("pass" if passing_score is not None and adjusted_total_score >= passing_score else "fail") if passing_score is not None else None),
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

            
            if role == "assistant":
                
                if current_question and not current_question.get("answer"):
                    
                    current_question["answer"] = "[No answer provided]"
                    qa_pairs.append(current_question)

                
                current_question = {
                    "question": content,
                    "answer": None,
                    "question_timestamp": message.get("timestamp")
                }

            
            elif role == "user" and current_question:
                current_question["answer"] = content
                current_question["answer_timestamp"] = message.get("timestamp")
                qa_pairs.append(current_question)
                current_question = None

        
        if current_question and not current_question.get("answer"):
            current_question["answer"] = "[Interview ended before answer]"
            qa_pairs.append(current_question)

        
        qa_pairs = [
            qa for qa in qa_pairs
            if qa.get("answer")
            and not qa["answer"].startswith("[")
            and qa["answer"].strip() != ""
            and len(qa["answer"].strip()) > 3  
        ]

        return qa_pairs
