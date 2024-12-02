# api/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from api.models.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
    update_user_profile,  
    User,
    oauth2_scheme,
    get_user
)
from typing import Optional, List
from bson import ObjectId

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login and get a JWT token for the user.
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=User)
async def sign_up(
    firstName: str = Form(...),
    lastName: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    emergencyContact: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    projectsInvolved: Optional[List[str]] = Form([]),  
    role: str = Form("Volunteer"),
    status: str = Form("Active")
):
    """
    Sign up a new user with form data (username, password, etc.)
    """
    try:
        new_user = create_user(
            firstName=firstName,
            lastName=lastName,
            username=username,
            password=password,
            email=email,
            phoneNumber=phoneNumber,
            address=address,
            emergencyContact=emergencyContact,
            organization=organization,
            role=role,
            status=status,
            projectsInvolved=projectsInvolved  
        )
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Correct use of status
            detail=str(e)
        )

@router.get("/users/me/", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.put("/users/me/", response_model=User)
async def update_profile(
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    emergencyContact: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    projectsInvolved: Optional[List[str]] = Form([]),  
    role: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    token: str = Depends(oauth2_scheme)
):
    """
    Update the current user's profile data.
    """
    current_user = await get_current_user(token, oauth2_scheme)

    # Prepare the fields that the user can update
    user_data = {
        "firstName": firstName,
        "lastName": lastName,
        "email": email,
        "phoneNumber": phoneNumber,
        "address": address,
        "emergencyContact": emergencyContact,
        "organization": organization,
        "projectsInvolved": projectsInvolved,
        "role": role,
        "status": status,
    }

    # Remove None values from user_data (we shouldn't update fields with None values)
    user_data = {key: value for key, value in user_data.items() if value is not None}

    # If projectsInvolved is explicitly None or empty string, we should set it to an empty list
    if "projectsInvolved" in user_data:
        # If the user has provided an empty string or None, set to an empty list
        if user_data["projectsInvolved"] == "" or user_data["projectsInvolved"] is None:
            user_data["projectsInvolved"] = []

        # Filter valid project IDs (only valid ObjectId strings)
        user_data["projectsInvolved"] = [
            project_id for project_id in user_data["projectsInvolved"] if ObjectId.is_valid(project_id)
        ]


    try:
        updated_user = update_user_profile(current_user.username, user_data)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users/{username}", response_model=User)
async def get_user_profile(username: str, token: str = Depends(oauth2_scheme)):
    """
    Fetch a user's profile by their username.
    """
    current_user = await get_current_user(token, oauth2_scheme)
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    # You can add role-based checks here if needed

    user = get_user(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

