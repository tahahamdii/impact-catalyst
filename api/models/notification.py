from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from typing import Optional

class Notification(BaseModel):
    id: str
    user: str  
    post_id: Optional[str]  
    comment_id: Optional[str]  
    notification_type: str
    created_at: datetime
    is_read: bool
    tagged_by: Optional[str]  
    project_id: Optional[str]

    class Config:
        json_encoders = {
            ObjectId: str,
        }
        from_attributes = True
