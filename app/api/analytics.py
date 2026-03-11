from typing import List, Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import CensusRecord, AuditLog, User, UserRole
from app.core.security import get_db, allow_chancellor, allow_superuser
from app.utils.exporter import export_to_csv

router = APIRouter(prefix="/analytics", tags=["Diocese Analytics"])

# 1. Audit Trail: The Truth Engine
@router.get("/audit-trail/{record_id}", response_model=List[Dict[str, Any]])
def get_record_audit_trail(
    record_id: int,
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Returns a full chronological history of changes for a specific record.
    Shows who changed what and when.
    """
    logs = db.query(AuditLog).filter(
        AuditLog.record_id == record_id,
        AuditLog.table_name == "census_records"
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return [
        {
            "timestamp": log.timestamp,
            "action": log.action,
            "changed_by": log.actor.email if log.actor else "System",
            "old_values": log.old_values,
            "new_values": log.new_values
        }
        for log in logs
    ]

# 2. Diocese Summary: Aggregated Data
@router.get("/diocese-summary", response_model=Dict[str, int])
def get_diocese_summary(
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Provides a real-time summary of the entire Diocese's census data.
    """
    summary = db.query(
        func.sum(CensusRecord.total_parishioners).label("total"),
        func.sum(CensusRecord.baptisms).label("baptisms"),
        func.sum(CensusRecord.marriages).label("marriages"),
        func.sum(CensusRecord.deaths).label("deaths")
    ).first()
    
    return {
        "total_parishioners": summary.total or 0,
        "total_baptisms": summary.baptisms or 0,
        "total_marriages": summary.marriages or 0,
        "total_deaths": summary.deaths or 0
    }

# 3. Parish Comparison
@router.get("/parish-comparison", response_model=List[Dict[str, Any]])
def get_parish_comparison(
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Side-by-side comparison of latest counts per parish.
    """
    results = db.query(CensusRecord).all()
    return [
        {
            "parish": r.parish_id,
            "year": r.year,
            "total": r.total_parishioners,
            "baptisms": r.baptisms
        }
        for r in results
    ]

# 4. Export Census to CSV
@router.get("/export-csv")
def export_census_data(
    current_user: Annotated[User, Depends(allow_chancellor)],
    db: Session = Depends(get_db)
):
    """
    Generates and downloads a CSV of the entire census for offline reporting.
    """
    records = db.query(CensusRecord).all()
    if not records:
        raise HTTPException(status_code=404, detail="No records available to export")
    
    # Convert to list of dicts for pandas
    data = [
        {
            "ID": r.id,
            "Parish": r.parish_id,
            "Total": r.total_parishioners,
            "Baptisms": r.baptisms,
            "Marriages": r.marriages,
            "Deaths": r.deaths,
            "Year": r.year,
            "SubmittedBy": r.author.email if r.author else "N/A"
        }
        for r in records
    ]
    
    csv_file = export_to_csv(data, filename_prefix="diocese_census")
    
    return FileResponse(
        path=csv_file,
        filename=csv_file.name,
        media_type='text/csv'
    )
