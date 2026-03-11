from typing import Annotated, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import CensusRecord, User
from app.core.security import get_db, allow_chancellor
from app.ai.service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Insights"])

@router.get("/census-insight", response_model=Dict[str, str])
async def get_ai_census_insight(
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
     chancellor/superuser only: 
    Generates a natural language summary of all census data using local AI.
    """
    records = db.query(CensusRecord).all()
    if not records:
        return {"insight": "No data available for analysis."}

    # Convert to simple list of dicts for AI service
    data = [
        {
            "parish_id": r.parish_id,
            "total_parishioners": r.total_parishioners,
            "baptisms": r.baptisms,
            "year": r.year
        }
        for r in records
    ]

    summary = await ai_service.generate_census_summary(data)
    return {"insight": summary}
