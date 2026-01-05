from fastapi import Request

def get_realtime_interview_collection(request: Request):
    """Get MongoDB collection for realtime interview sessions"""
    return request.app.state.realtime_interview_collection
