from typing import Optional, List

from app.api.security import create_token, verify_token
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

import app.storage as storage
from app.schema import User

router = APIRouter()

class UserID(str):
    """Type annotation for user ID."""

class UserRegisterRequest(BaseModel):
    """Payload for registering a new user."""
    username: str = Field(..., description="The username of the user.")
    password_hash: str = Field(..., description="The hashed password of the user.")
    email: str = Field(..., description="The email of the user.")
    full_name: str = Field(..., description="The full name of the user.")
    address: str = Field(..., description="The address of the user.")

class UserLoginRequest(BaseModel):
    """Payload for logging in a user."""
    username: str = Field(..., description="The username of the user.")
    password_hash: str = Field(..., description="The hashed password of the user.")

class UserResponse(BaseModel):
    """Response model for registering a new user."""
    token: str
    message: str


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_register_request: UserRegisterRequest) -> UserResponse:
    """Register a new user."""
    user = await storage.register_user(**user_register_request.dict())
    if user:
        # Generate token
        token = create_token(user.username)
        return {'token': token, "message": "Register successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@router.post("/login", response_model=Optional[UserResponse])
async def login_user(user_login_request: UserLoginRequest) -> Optional[UserResponse]:
    """Login a user."""
    user = await storage.login_user(**user_login_request.dict())
    if user:
        # Generate token
        token = create_token(user.username)
        return {"token": token, "message": 'Login successful'}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@router.post("/logout")
async def logout_user():
    # You may add additional logic here if needed, such as invalidating sessions, etc.
    return {"message": "Logout successful"}

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(user_id: UserID) -> User:
    """Get a user by ID."""
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[User], status_code=200)
async def list_active_users():
    """List all active users."""
    users = await storage.list_active_users()
    if users:
        return users
    else:
        raise HTTPException(status_code=404, detail="No active users found")


@router.put("/{user_id}", response_model=User)
async def update_user_by_id(user_id: UserID, user_update_request: UserRegisterRequest) -> User:
    """Update a user by ID."""
    user = await storage.update_user(user_id, **user_update_request.dict())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user_by_id(user_id: UserID):
    """Delete a user by ID."""
    deleted = await storage.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
