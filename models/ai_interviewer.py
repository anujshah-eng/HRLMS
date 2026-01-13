from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class AIInterviewer(BaseModel):
    id: int  # Legacy integer ID from MySQL
    name: str
    voice_id: str
    gender: str
    accent: Optional[str] = None
    description: Optional[str] = None
    greet_video: Optional[str] = None
    video_blink_1: Optional[str] = None
    video_blink_2: Optional[str] = None
    video_dubb: Optional[str] = None
    img: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
