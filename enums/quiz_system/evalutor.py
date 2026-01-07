from enum import Enum

class KnowledgeLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class AnswerType(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    SKIPPED = "skipped"

class AttemptedFilterTypeEnum(str, Enum):
    SUBMITTED = "submitted"
    AUTO_SUBMITTED = "auto submitted"
    NOT_SUBMITTED = "not submitted"
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    ALL = "all"

class SortField(str, Enum):
    NAME = "name"
    SCORE = "score"
    FINISHED_AT = "finished_at"
    STATUS = "status"

class QuizStatusFilter(str, Enum):
    ALL = "All"
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
