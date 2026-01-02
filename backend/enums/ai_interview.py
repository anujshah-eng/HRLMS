from enum import Enum

class InterviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CHEATING =  "cheating"

    def __str__(self) -> str:
        return self.value

class InterviewLevel(str, Enum):
    EASY = 'Easy'
    MEDIUM = 'Medium'
    HARD = 'Hard'