from fastapi import HTTPException, status, Depends
from connections.postgres_connection import DBResourceManager
from custom_utilities.authorization import get_current_user
from custom_utilities.dependencies import get_course_collection, get_quiz_collection
from enums.role_enum import UserRoleEnum

# Create DB manager
db_manager = DBResourceManager()

def get_user_tenant_id(user_id: str) -> str:
    """Get tenant_id from user"""
    with db_manager.connect() as session:
        from models.user_management import User
        user = session.query(User).filter(User.user_id == user_id).first()
        print("get_user_tenent_id works")
        return user.tenant_id if user else None

def get_tenant_plan(tenant_id: str) -> str:
    """Get subscription type for a tenant"""
    with db_manager.connect() as session:
        # from models.tenant_usage_limits import TenantUsageLimits
        # plan = session.query(TenantUsageLimits).filter(
        #     TenantUsageLimits.tenant_id == tenant_id,
        #     TenantUsageLimits.is_active == True
        # ).first()
        # return plan.subscription_type if plan else 'free'
        print("get_tenant_plan works")
        
        return 'free'

def get_plan_limits(plan_type: str) -> dict:
    """Get limits for a specific plan type"""
    plan_limits = {
        'free': {
            'max_classrooms': 10,
            'max_students_per_classroom': 20,
            'max_ai_courses': 2,
            'max_quizzes': 2,
            'max_ai_questions_per_quiz': 10
        }
    }
    print("get_plan_limits works")
    return plan_limits.get(plan_type, plan_limits['free'])

# Counting functions
def get_classroom_count(user_id: str) -> int:
    """Count classrooms from PostgreSQL"""
    with db_manager.connect() as session:
        from models.classroom_management import Classroom
        return session.query(Classroom).filter(Classroom.created_by == user_id).count()
    # print("get_classroom_count works")
    # return 30

def get_student_count(classroom_id: int) -> int:
    """Count students from PostgreSQL"""
    # with db_manager.connect() as session:
    #     from models.student import Student
    #     return session.query(Student).filter(Student.classroom_id == classroom_id).count()
    from models.classroom_management import ClassroomMember
    from models.user_management import UserRole
    
    with db_manager.connect() as session:
        count = (
            session.query(ClassroomMember)
            .join(UserRole, ClassroomMember.user_id == UserRole.user_id)
            .filter(
                ClassroomMember.class_id == classroom_id,
                UserRole.role_id == UserRoleEnum.STUDENT
            )
        )
        
    print("get_student_count works")
    return 30

def get_ai_course_count(user_id: str, course_collection) -> int:
    """Count AI courses from MongoDB"""
    return course_collection.count_documents({
        "user_id": user_id,
        "is_ai": True
    })

def get_quiz_count(user_id: str, quiz_collection) -> int:
    """Count AI quizzes from MongoDB"""
    return quiz_collection.count_documents({
        "user_id": user_id
    })

def get_ai_question_count(quiz_id: int, quiz_collection) -> int:
    """Count AI questions in a quiz from MongoDB"""
    quiz = quiz_collection.find_one({"quiz_id": quiz_id})
    if quiz and "questions" in quiz:
        return len([q for q in quiz["questions"] if q.get("is_ai", False)])
    return 0

# THE MAIN CHECK_LIMIT FUNCTION (What you were expecting)
def check_limit(user_id: str, resource_type: str, resource_id: int = None, 
                course_collection=None, quiz_collection=None):
    """Main function to check any limit"""
    # 1. Get user's tenant
    tenant_id = get_user_tenant_id(user_id)
    if not tenant_id:
        return
    
    # 2. Get tenant's plan
    plan_type = get_tenant_plan(tenant_id)
    
    # 3. Get limits for that plan
    limits = get_plan_limits(plan_type)
    
    # 4. Check the specific limit
    if resource_type == 'classroom':
        current_count = get_classroom_count(user_id)
        if current_count >= limits['max_classrooms']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan allows creating up to 10 classrooms only."
            )
    
    elif resource_type == 'student':
        current_count = get_student_count(resource_id)
        if current_count >= limits['max_students_per_classroom']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan allows a maximum of 20 students per classroom."
            )
    
    elif resource_type == 'ai_course':
        if not course_collection:
            return  # No collection, skip check
        current_count = get_ai_course_count(user_id, course_collection)
        if current_count >= limits['max_ai_courses']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan allows only 2 courses in total."
            )
    
    elif resource_type == 'ai_quiz':
        if not quiz_collection:
            return  # No collection, skip check
        current_count = get_quiz_count(user_id, quiz_collection)
        if current_count >= limits['max_quizzes']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan allows only 2 quizzes in total."
            )
    
    elif resource_type == 'ai_question':
        if not quiz_collection:
            return  # No collection, skip check
        current_count = get_ai_question_count(resource_id, quiz_collection)
        if current_count >= limits['max_ai_questions_per_quiz']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan allows only 20 AI-generated questions per quiz."
            )
    
    
# Simple dependency functions - JUST LIKE YOU HAD!
async def enforce_classroom_limit(current_user: dict = Depends(get_current_user)):
    check_limit(current_user['user_id'], 'classroom')

async def enforce_student_limit(classroom_id: int, current_user: dict = Depends(get_current_user)):
    check_limit(current_user['id'], 'student', classroom_id)

async def enforce_ai_course_limit(
    current_user: dict = Depends(get_current_user),
    course_collection = Depends(get_course_collection)
):
    check_limit(current_user['id'], 'ai_course', course_collection=course_collection)

async def enforce_ai_quiz_limit(
    current_user: dict = Depends(get_current_user),
    quiz_collection = Depends(get_quiz_collection)
):
    check_limit(current_user['id'], 'ai_quiz', quiz_collection=quiz_collection)

async def enforce_ai_question_limit(
    quiz_id: int, 
    current_user: dict = Depends(get_current_user),
    quiz_collection = Depends(get_quiz_collection)
):
    check_limit(current_user['id'], 'ai_question', quiz_id, quiz_collection=quiz_collection)
    