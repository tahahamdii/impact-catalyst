from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
from bson import ObjectId
from passlib.context import CryptContext
from api.models.get_database_collection import get_collections
from pymongo.errors import DuplicateKeyError
from jose import JWTError, jwt
import os
from fastapi.security import OAuth2PasswordBearer  

# Load environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# MongoDB collections
users_collections = get_collections().get("users")
projects_collections = get_collections().get("projects")

# Password hash 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User Model
class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    disabled: Optional[bool] = None
    role: Optional[str] = None
    address: Optional[str] = None
    phoneNumber: Optional[str] = None
    emergencyContact: Optional[str] = None
    organization: Optional[str] = None
    projectsInvolved: Optional[List[dict]] = []  

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str  
        }

class UserInDB(User):
    hashed_password: str

# Token model
class TokenData(BaseModel):
    username: Optional[str] = None

# Password hashing functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# User retrieval and authentication
def get_user(username: str) -> Optional[UserInDB]:
    user_data = users_collections.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Create a new user
def create_user(
    firstName: str, lastName: str, username: str, password: str,
    email: Optional[str] = None, phoneNumber: Optional[str] = None,
    address: Optional[str] = None, emergencyContact: Optional[str] = None, organization: Optional[str] = None, 
    role: Optional[str] = None, status: str = "Active",
    projectsInvolved: Optional[List[str]] = None
):
    # Hash the password
    hashed_password = get_password_hash(password)

    # If projectsInvolved is provided, fetch the project names from the database
    if projectsInvolved:
        # Filter out empty strings or invalid project IDs
        valid_project_ids = [project_id for project_id in projectsInvolved if project_id and len(project_id) == 24]
        # Convert valid project IDs to ObjectId
        project_ids = [ObjectId(project_id) for project_id in valid_project_ids]
        
        # Fetch project details (names) for each projectId
        projects = projects_collections.find({"_id": {"$in": project_ids}})
        
        # Create a list of dictionaries with projectId and projectName
        projectsInvolved = [
            {"projectId": str(project["_id"]), "projectName": project["projectName"]}
            for project in projects
        ]
    else:
        projectsInvolved = []  

    # Create the new user document
    new_user = {
        "firstName": firstName,
        "lastName": lastName,
        "username": username,
        "hashed_password": hashed_password,
        "email": email,
        "phoneNumber": phoneNumber,
        "address": address,
        "emergencyContact": emergencyContact,
        "organization": organization,
        "role": role,
        "status": status,
        "disabled": False,
        "projectsInvolved": projectsInvolved  
    }

    try:
        # Insert user into MongoDB
        result = users_collections.insert_one(new_user)

        # Add the generated _id to the new_user dictionary
        new_user['id'] = str(result.inserted_id)  # Convert ObjectId to string

        return UserInDB(**new_user)  # Return the UserInDB object with the ID
    except DuplicateKeyError:
        raise ValueError("Username already taken")

# Get current user from token
async def get_current_user(token: str, oauth2_scheme):
    exception = JWTError()
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  
        if username is None:
            raise exception

        # Create TokenData instance from payload
        token_data = TokenData(username=username)
    except JWTError:
        raise exception

    
    user = get_user(username=token_data.username)
    if user is None:
        raise exception

    return user

# Update the user's profile in the database
def update_user_profile(username: str, user_data: dict) -> UserInDB:
    user = get_user(username)

    if not user:
        raise ValueError("User not found")

    # Ensure 'projectsInvolved' is not updated by user
    if "projectsInvolved" in user_data:
        del user_data["projectsInvolved"]  # Remove the 'projectsInvolved' field from the user data

    # Only update fields that are provided and not None
    update_fields = {key: value for key, value in user_data.items() if value is not None}

    # Update the user's data in MongoDB
    users_collections.update_one(
        {"username": username},
        {"$set": update_fields}
    )

    # Fetch the updated user
    updated_user_data = users_collections.find_one({"username": username})

    # Add 'id' from '_id' if missing
    updated_user_data['id'] = str(updated_user_data['_id'])  # Convert ObjectId to string

    return UserInDB(**updated_user_data)

def get_user(username: str) -> Optional[UserInDB]:
    user_data = users_collections.find_one({"username": username})
    if user_data:
        # Add the '_id' field to the user model
        user_data['id'] = str(user_data['_id'])  
        return UserInDB(**user_data)


