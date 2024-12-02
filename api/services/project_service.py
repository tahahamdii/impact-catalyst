from typing import List
from fastapi import HTTPException
from bson import ObjectId
from api.models.projects import ProjectCreateRequest
from api.models.projects import projects_collections, users_collections, ProjectResponse
from api.services.notification import create_notifications


from bson import ObjectId
from fastapi import HTTPException
from api.services.notification import create_notifications

async def update_project(project_id: str, project_data: ProjectCreateRequest, current_user) -> ProjectResponse:
    try:
        # Ensure that the project_id is a valid ObjectId
        try:
            project_object_id = ObjectId(project_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid project ID format")
        
        # Fetch the project from the database
        project = projects_collections.find_one({"_id": project_object_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if the user is part of the project team
        if not any(team_member['username'] == current_user.username for team_member in project.get("teamMembers", [])):
            raise HTTPException(status_code=403, detail="You are not part of this project")

        # Prepare the update data for the project
        update_data = {}

        # Handle basic project fields
        if project_data.projectName:
            update_data["projectName"] = project_data.projectName
        if project_data.description:
            update_data["description"] = project_data.description
        if project_data.status:
            update_data["status"] = project_data.status
        if project_data.startDate:
            update_data["startDate"] = project_data.startDate
        if project_data.endDate:
            update_data["endDate"] = project_data.endDate
        if project_data.donor:
            update_data["donor"] = project_data.donor
        if project_data.budget:
            update_data["budget"] = project_data.budget
        if project_data.location:
            update_data["location"] = project_data.location
        if project_data.objectives:
            update_data["objectives"] = project_data.objectives

        # If the teamMembers field has been updated, handle it
        if project_data.teamMembers:
            usernames = project_data.teamMembers
            # Fetch users by username and convert cursor to a list
            users_cursor = users_collections.find({"username": {"$in": usernames}})
            users = list(users_cursor)

            # Build the team members list with userId and username
            team_member_usernames = []
            missing_usernames = []
            for username in usernames:
                user = next((user for user in users if user['username'] == username), None)
                if user:
                    team_member_usernames.append({
                        "userId": str(user["_id"]),
                        "username": user["username"]
                    })
                else:
                    missing_usernames.append(username)

            # If any usernames are missing, raise an error
            if missing_usernames:
                raise HTTPException(status_code=404, detail=f"Users not found: {', '.join(missing_usernames)}")

            # Add the updated teamMembers to the project update data
            update_data["teamMembers"] = team_member_usernames

            # Determine newly added users by comparing with the existing team members
            existing_usernames = {team_member['username'] for team_member in project.get('teamMembers', [])}
            newly_added_usernames = set(usernames) - existing_usernames

            # Only trigger notifications if there are newly added team members
            if newly_added_usernames:
                # Log the newly added users for debugging purposes
                print(f"Newly added team members: {newly_added_usernames}")
                create_notifications(
                    post_id=None,  # No post related to project creation
                    content=None,  # No content related to the project creation
                    author_username=current_user.username,
                    project_id=project_id,
                    team_members_usernames=list(newly_added_usernames)  # Newly added team members to notify
                )

        # Update the project in the database
        updated_project = projects_collections.find_one_and_update(
            {"_id": project_object_id},
            {"$set": update_data},
            return_document=True
        )

        if not updated_project:
            raise HTTPException(status_code=500, detail="Error updating project")

        # After updating the project, update the user documents for each team member
        if "teamMembers" in update_data:
            for team_member in update_data["teamMembers"]:
                user_id = ObjectId(team_member["userId"])
                project_info = {"projectId": str(project_id), "projectName": project_data.projectName}

                # Update the user's projectsInvolved field
                users_collections.update_one(
                    {"_id": user_id, "projectsInvolved.projectId": str(project_id)},  
                    {"$set": {
                        "projectsInvolved.$": project_info  
                    }}
                )

                # If the user doesn't already have the project, add it
                users_collections.update_one(
                    {"_id": user_id, "projectsInvolved.projectId": {"$ne": str(project_id)}},  
                    {"$addToSet": {"projectsInvolved": project_info}}  
                )

        # Return the updated project as a ProjectResponse
        return ProjectResponse.from_mongo(updated_project)

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")
