from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional
from api.models.get_database_collection import get_collections

# MongoDB collections
projects_collections = get_collections().get("projects")
users_collections = get_collections().get("users")

class ProjectCreateRequest(BaseModel):
    projectName: str
    description: str
    status: str
    startDate: str
    endDate: Optional[str] = None
    donor: Optional[str] = None
    budget: Optional[float] = None
    location: List[str] = []
    objectives: List[str] = []
    teamMembers: List[str] = []  
    

class ProjectResponse(BaseModel):
    id: str  # This will hold the MongoDB ObjectId, converted to string
    projectName: str
    description: str
    status: str
    startDate: str
    endDate: Optional[str]
    donor: Optional[str]
    budget: Optional[float]
    location: List[str]
    objectives: List[str]
    teamMembers: List[dict]

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str  # Converts ObjectId to string in the response
        }

    @classmethod
    def from_mongo(cls, mongo_dict: dict):
        mongo_dict['id'] = str(mongo_dict.pop('_id', None))  # Rename _id to id
        return cls(**mongo_dict)

def create_project(
    projectName: str, description: str, status: str, startDate: str, 
    endDate: Optional[str] = None, donor: Optional[str] = None, 
    budget: Optional[float] = None, location: Optional[str] = None,
    objectives: List[str] = [], teamMembersData: List[dict] = []  # Accept team member data as input
):
    # Create the new project dictionary
    new_project = {
        "projectName": projectName,
        "description": description,
        "status": status,
        "startDate": startDate,
        "endDate": endDate,
        "donor": donor,
        "budget": budget,
        "teamMembers": teamMembersData,  # Directly use the provided team member data
        "location": location,
        "objectives": objectives
    }

    # Insert the new project into the projects collection
    result = projects_collections.insert_one(new_project)
    project_id = result.inserted_id  # Get the inserted project ID
    
    # Update each user (team member) involved in this project
    for user_data in teamMembersData:
        users_collections.update_one(
            {"_id": ObjectId(user_data["userId"])},
            {"$addToSet": {"projectsInvolved": {"projectId": str(project_id), "projectName": projectName}}}
        )

    # Add the ObjectId to the project data before returning
    new_project["id"] = str(project_id)  # Ensure ObjectId is converted to string

    return new_project


