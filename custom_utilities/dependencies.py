from fastapi import Request

def get_quiz_collection(request: Request):
    return request.app.state.quiz_collection

def get_course_collection(request: Request):
    return request.app.state.course_collection

def get_student_quiz_attempts_collection(request: Request):
    return request.app.state.student_quiz_collection

def get_realtime_interview_collection(request: Request):
    """Get MongoDB collection for realtime interview sessions"""
    return request.app.state.realtime_interview_collection
