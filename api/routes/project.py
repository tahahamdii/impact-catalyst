from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.models.projects import create_project, projects_collections, users_collections, ProjectResponse, ProjectCreateRequest
from api.models.auth import oauth2_scheme, get_current_user
from bson import ObjectId
from api.services.project_service import update_project
from api.services.notification import create_notifications

router = APIRouter()

@router.post("/projects/", response_model=ProjectResponse)
async def create_project_route(
    project_data: ProjectCreateRequest,
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    if not project_data.teamMembers:
        raise HTTPException(status_code=400, detail="At least one team member must be assigned to the project")
    
    try:
        # Fetch the user details for each team member based on username
        usernames = project_data.teamMembers
        team_members_data = []

        # Query users by username
        users = users_collections.find({"username": {"$in": usernames}})
        
        # Extract the found usernames and userIds
        found_usernames = {user["username"]: str(user["_id"]) for user in users}
        
        # Check if there are any missing usernames
        missing_usernames = [username for username in usernames if username not in found_usernames]
        
        if missing_usernames:
            raise HTTPException(status_code=404, detail=f"Users not found: {', '.join(missing_usernames)}")
        
        # Create the team_members_data to include userId and username
        for username in usernames:
            user_id = found_usernames[username]
            team_members_data.append({
                "userId": user_id,
                "username": username
            })
        
        # Create the project with the team_members_data (already contains userId and username)
        project = create_project(
            projectName=project_data.projectName,
            description=project_data.description,
            status=project_data.status,
            startDate=project_data.startDate,
            endDate=project_data.endDate,
            donor=project_data.donor,
            budget=project_data.budget,
            location=project_data.location,
            objectives=project_data.objectives,
            teamMembersData=team_members_data  # Pass the list of dictionaries (userId + username) here
        )

        # Extract the project_id from the newly created project
        project_id = str(project["_id"])

        # Create notifications for newly added team members
        create_notifications(
            post_id=None,  # No post related to project creation
            content=None,  # No content related to the project creation
            author_username=current_user.username,
            project_id=project_id,
            team_members_usernames=usernames  # Newly added team members to notify
        )

        # Return the project, making sure it's in the Pydantic format (with id converted to string)
        return ProjectResponse.from_mongo(project)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")



@router.get("/projects/", response_model=List[ProjectResponse])
async def get_projects_route(
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    try:
        # Fetch all projects from the database
        projects = list(projects_collections.find())

        # Convert each project to the Project model
        response_projects = [ProjectResponse.from_mongo(project) for project in projects]

        # Return the list of projects as the response model
        return response_projects
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_route(
    project_id: str,
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    try:
        # Fetch the project from MongoDB using the provided project_id
        project = projects_collections.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert ObjectId to string for project data
        project["_id"] = str(project["_id"])

        # Iterate over team members to ensure userId and username are returned
        for team_member in project.get("teamMembers", []):
            team_member["userId"] = str(team_member["userId"])  
            team_member["username"] = team_member.get("username") 
        
        return ProjectResponse.from_mongo(project)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")
    
    
@router.get("/project/count", response_model=int)
async def get_project_count_route(
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    try:
        print("Attempting to count total projects...")
        
        # Count the documents in the collection
        total_project_count = projects_collections.count_documents({})

        print(f"Total project count: {total_project_count}")

        return total_project_count

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching total project count: {str(e)}")
    

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project_route(
    project_id: str,
    project_data: ProjectCreateRequest,
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)
    
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Call the update_project service function
    return await update_project(project_id, project_data, current_user)