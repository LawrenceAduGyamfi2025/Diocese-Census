from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import (
    verify_password, create_access_token, get_db, 
    get_current_active_user, User
)

router = APIRouter(tags=["Authentication"])

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "parish": current_user.parish_name,
        "is_active": current_user.is_active
    }
