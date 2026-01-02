from enum import Enum

class ContentTypeEnum(str, Enum):
    COURSE = "course"
    QUIZ = "quiz"
    ANNOUNCEMENT = "announcement"

class QueryPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"