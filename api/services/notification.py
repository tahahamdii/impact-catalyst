from datetime import datetime
from bson import ObjectId
from api.models.notification import Notification
from api.models.get_database_collection import get_collections
import re
from typing import List, Optional

# Get the necessary collections from MongoDB
users_collection = get_collections().get('users')
notifications_collection = get_collections().get('notifications')

def find_tagged_users(content: str):
    """
    Finds all tagged users in the content (e.g., @username).
    """
    mentions = re.findall(r'@(\w+)', content)  # Match @username
    if not mentions:
        return []

    # Fetch all users that are tagged in one query
    users = list(users_collection.find({"username": {"$in": mentions}}))
    return {user['username']: user for user in users}  # Return a dictionary for quick lookups

def create_notifications(post_id: Optional[str], content: str, author_username: str, 
                         comment_id: Optional[str] = None, project_id: Optional[str] = None, 
                         team_members_usernames: List[str] = None):
    """
    Creates notifications for users either tagged in a post/comment or newly added to a project.
    
    - If `project_id` is provided, it creates project-related notifications for newly added team members.
    - If `content` is provided, it creates tag notifications for users tagged in the post/comment.
    """
    notifications = []

    # Case 1: Create tag notifications (for tagged users in a post/comment)
    if content:
        tagged_users_map = find_tagged_users(content)

        if not isinstance(tagged_users_map, dict):
            tagged_users_map = {}

        # Create notifications for tagged users
        for username, user in tagged_users_map.items():
            if username != author_username:  # Don't notify the author
                notification = {
                    'user': ObjectId(user['_id']),
                    'post_id': ObjectId(post_id) if post_id else None,  # Always set the post_id
                    'comment_id': ObjectId(comment_id) if comment_id else None,  # Optional comment_id
                    'notification_type': 'TAG',
                    'created_at': datetime.utcnow(),
                    'is_read': False,  # Notifications are unread initially
                    'tagged_by': author_username,  # Add tagged_by to the notification
                    'project_id': ObjectId(project_id) if project_id else None  # Add project_id if available
                }
                notifications.append(notification)

    # Case 2: Create project notifications for newly added team members
    if project_id and team_members_usernames:
        # Fetch the current project team members (existing members)
        existing_team_members = set(
            [user['username'] for user in users_collection.find({"projectsInvolved.projectId": ObjectId(project_id)})]
        )

        # Filter the newly added team members
        newly_added_members = [username for username in team_members_usernames if username not in existing_team_members]

        if newly_added_members:
            users = list(users_collection.find({"username": {"$in": newly_added_members}}))

            for user in users:
                if user['username'] != author_username:  # Don't notify the author
                    notification = {
                        'user': ObjectId(user['_id']),
                        'post_id': None,  # Not related to a post
                        'comment_id': None,  # Not related to a comment
                        'notification_type': 'PROJECT',
                        'created_at': datetime.utcnow(),
                        'is_read': False,  # Notifications are unread initially
                        'tagged_by': author_username,  # Who updated the project/team
                        'project_id': ObjectId(project_id)  # Add the project ID to the notification
                    }
                    notifications.append(notification)

    if notifications:
        # Insert all notifications in a batch
        notifications_collection.insert_many(notifications)