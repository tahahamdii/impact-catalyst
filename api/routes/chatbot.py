# api/routes/chatbot.py
from fastapi import APIRouter, Depends, HTTPException
from api.models.auth import get_current_user
from api.services.question_service import process_question
from api.models.auth import oauth2_scheme

router = APIRouter()

@router.get("/question")
async def ask_question(user_input: str, token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return {"answer": process_question(user_input)}
