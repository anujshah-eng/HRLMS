from fastapi import Request

def get_ai_interviewers_collection(request: Request):
    """Get MongoDB collection for AI interviewers"""
    return request.app.state.ai_interviewers_collection

def get_realtime_interview_collection(request: Request):
    """Get MongoDB collection for realtime interview sessions"""
    return request.app.state.realtime_interview_collection
