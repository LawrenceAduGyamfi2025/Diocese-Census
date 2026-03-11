from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import CensusRecord, UserRole, User
from app.schemas.census import CensusCreate, CensusUpdate, CensusResponse
from app.core.security import (
    get_db, get_current_active_user, RoleChecker, 
    allow_chancellor, allow_superuser
)

router = APIRouter(prefix="/census", tags=["Census Management"])

# 1. Custom Role Checkers
allow_priest_or_admin = RoleChecker([UserRole.priest, UserRole.superuser])
allow_priest_only = RoleChecker([UserRole.priest])

# 2. Routes

@router.post("/submit", response_model=CensusResponse, status_code=status.HTTP_201_CREATED)
def submit_census(
    census: CensusCreate,
    current_user: Annotated[User, Depends(allow_priest_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Priests submit their parish data. System automatically logs the author.
    """
    db_census = CensusRecord(
        **census.model_dump(),
        submitted_by_id=current_user.id
    )
    db.add(db_census)
    db.commit()
    db.refresh(db_census)
    return db_census

@router.get("/my-parish", response_model=List[CensusResponse])
def get_my_parish_data(
    current_user: Annotated[User, Depends(allow_priest_only)],
    db: Session = Depends(get_db)
):
    """
    Restricts view to the current priest's parish only.
    """
    return db.query(CensusRecord).filter(
        CensusRecord.parish_id == current_user.parish_name
    ).all()

@router.get("/all", response_model=List[CensusResponse])
def get_all_census_data(
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Chancellors and Admins view all collected diocese data.
    """
    return db.query(CensusRecord).all()

@router.put("/update/{id}", response_model=CensusResponse)
def update_census_record(
    id: int,
    census_update: CensusUpdate,
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Updates record and triggers the 'AuditLog' listener.
    Priests are locked out of editing for data integrity.
    """
    db_record = db.query(CensusRecord).filter(CensusRecord.id == id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Census record not found")

    # Pass the current user ID to the session for the AuditLog listener
    db.info["user_id"] = current_user.id

    update_data = census_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)

    try:
        db.commit()
        db.refresh(db_record)
        return db_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Update failed (possible version conflict): {str(e)}")
