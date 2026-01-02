from enum import Enum

class CourseStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ALL = "all"
    IN_PROGRESS = "In Progress"
    
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
