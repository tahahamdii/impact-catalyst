from fastapi import APIRouter, Depends, HTTPException
from api.services.notification import notifications_collection
from bson import ObjectId
from api.models.notification import Notification
from typing import List


router = APIRouter()

# Get notifications for a user
@router.get("/notifications/{user_id}", response_model=List[Notification])
async def get_notifications(user_id: str):
    # Fetch notifications from the database
    notifications_cursor = notifications_collection.find({
        'user': ObjectId(user_id),
        'is_read': False
    }).sort('created_at', -1)  # Sort notifications by creation date

    # Convert MongoDB notifications to a list with proper field mapping
    notifications_list = [
        {**notification, 
         "id": str(notification["_id"]),  # Convert _id to id
         "user": str(notification["user"]), 
         "post_id": str(notification["post_id"]) if notification.get("post_id") else None,
         "comment_id": str(notification["comment_id"]) if notification.get("comment_id") else None,
         "tagged_by": notification.get("tagged_by"),
         "project_id": str(notification.get("project_id")) if "project_id" in notification else None  
        }
        for notification in notifications_cursor
    ]

    return notifications_list

# Mark notifications as read
@router.post("/mark_notifications_as_read/{user_id}")
async def mark_notifications_as_read(user_id: str):
    # Check if user_id is a valid ObjectId
    try:
        user_object_id = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    # Mark notifications as read
    result = notifications_collection.update_many(
        {'user': user_object_id, 'is_read': False},
        {'$set': {'is_read': True}}
    )

    # Handle the case where no notifications were marked as read
    if result.modified_count == 0:
        return {"status": "no_updates", "message": "No unread notifications found for this user."}
    
    return {"status": "success", "marked_as_read": result.modified_count}

# Mark a specific notification as read
@router.post("/mark_notification_as_read/{user_id}/{notification_id}")
async def mark_notification_as_read(user_id: str, notification_id: str):
    # Check if user_id and notification_id are valid ObjectId
    try:
        user_object_id = ObjectId(user_id)
        notification_object_id = ObjectId(notification_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user_id or notification_id format")
    
    # Find the specific notification by user and notification_id
    notification = notifications_collection.find_one({
        '_id': notification_object_id,
        'user': user_object_id
    })

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or does not belong to the user")

    # Update the specific notification to mark it as read
    result = notifications_collection.update_one(
        {'_id': notification_object_id},
        {'$set': {'is_read': True}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to mark notification as read")

    return {"status": "success", "message": f"Notification {notification_id} marked as read."}