# api/routes/community.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from bson import ObjectId
from api.models.auth import oauth2_scheme, get_current_user
from api.models.community import CommunityPost, CommunityPostCreate, Comment
from api.models.get_database_collection import get_collections
from api.services.notification import create_notifications  

router = APIRouter()

community_collection = get_collections().get('community')

@router.get("/community/posts/", response_model=List[CommunityPost])
async def get_community_posts(token: str = Depends(oauth2_scheme)):
    posts_cursor = community_collection.find({})
    posts = []

    for post in posts_cursor:
        post['id'] = str(post.pop('_id'))  

        # Fix: Ensure we use the comment's existing 'id' (not regenerate it)
        for comment in post.get("comments", []):
            comment['id'] = str(comment['id']) 

        posts.append(post)

    return posts

@router.get("/community/posts/{post_id}/", response_model=CommunityPost)
async def get_community_post_by_id(post_id: str, token: str = Depends(oauth2_scheme)):
    post = community_collection.find_one({"_id": ObjectId(post_id)})
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post['id'] = str(post.pop('_id')) 

    # Fix: Use existing 'id' of the comment rather than generating a new ObjectId
    for comment in post.get("comments", []):
        comment['id'] = str(comment['id'])  

    return post

# Create a new community post
@router.post("/community/posts/", response_model=CommunityPost)
async def create_community_post(post: CommunityPostCreate, token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)

    # Create the new post
    new_post = {
        "title": post.title,
        "content": post.content,
        "author": current_user.username,  
        "created_at": datetime.utcnow().isoformat(),
        "comments": []  # Initially, no comments
    }

    # Insert the post into the database
    result = community_collection.insert_one(new_post)
    new_post['id'] = str(result.inserted_id)  # Add the new post ID

    # Create notifications for any tagged users in the post content
    create_notifications(new_post['id'], post.content, current_user.username)

    return new_post


# Add a comment to an existing post
@router.post("/community/posts/{post_id}/comments/", response_model=Comment)
async def add_comment_to_post(
    post_id: str,  # The ID of the parent post
    comment: Comment, 
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(token, oauth2_scheme)

    # Create the comment data
    comment_data = {
        "content": comment.content,
        "author": current_user.username,
        "created_at": datetime.utcnow().isoformat(),
        "id": str(ObjectId())  # This is the unique comment ID
    }

    # Update the post with the new comment
    update_result = community_collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"comments": comment_data}}  # Add comment to the post's "comments" array
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or comment already added")
    
    # Create notifications for tagged users in the comment content
    create_notifications(post_id, comment_data['content'], current_user.username, comment_id=comment_data['id'])

    return {**comment_data, "post_id": post_id}

# Get comments for a specific post
@router.get("/community/posts/{post_id}/comments/", response_model=List[Comment])
async def get_comments_for_post(post_id: str, token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)

    try:
        post = community_collection.find_one({"_id": ObjectId(post_id)})
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid post ID format")

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post.get("comments", [])

# Get a specific comment by ID within a post
@router.get("/community/posts/{post_id}/comments/{comment_id}/", response_model=Comment)
async def get_comment_by_id(post_id: str, comment_id: str, token: str = Depends(oauth2_scheme)):
    current_user = await get_current_user(token, oauth2_scheme)

    # Fetch the post by its ID
    post = community_collection.find_one({"_id": ObjectId(post_id)})
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Find the comment by matching the 'id' field (comment_id is a string, so direct string comparison)
    comment = next(
        (comment for comment in post.get("comments", []) if comment['id'] == comment_id), 
        None
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment
