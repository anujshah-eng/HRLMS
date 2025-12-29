from enum import Enum

class TeacherRole(str, Enum):
    PROFESSOR = "Professor"
    ASSOCIATE_PROFESSOR = "Associate Professor"
    ASSISTANT_PROFESSOR = "Assistant Professor"
    LECTURER = "Lecturer"
    TUTOR = "Tutor"
    OTHER = "Other"

class TeacherFilterType(str, Enum):
    ACTIVE = "active"
    PENDING_INVITES = "pending_invites"
    BY_DEPARTMENT = "by_department"

class UserType(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
