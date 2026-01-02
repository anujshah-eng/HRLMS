from enum import Enum

class QuestionLevel(str, Enum):
    EASY = 'Easy'
    MEDIUM = 'Medium'
    HARD = 'Hard'

class QuestionType(str, Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    OPEN_ENDED = "OPEN_ENDED"

class QuizStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"

class QuizFilterType(str, Enum):
    ALL = "all"
    DRAFT = "Draft"
    PUBLISHED = "Published"

class InputType(str, Enum):
    PROMPT = "prompt"
    FILE = "file"
    URL = "url"
    COURSE = "course"
