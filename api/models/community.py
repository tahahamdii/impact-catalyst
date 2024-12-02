from pydantic import BaseModel
from datetime import datetime
from typing import List

class Comment(BaseModel):
    id: str
    content: str
    author: str
    created_at: datetime

class CommunityPost(BaseModel):
    id: str
    title: str
    content: str
    author: str
    created_at: datetime
    comments: List[Comment] = []  

class CommunityPostCreate(BaseModel):
    title: str
    content: str
