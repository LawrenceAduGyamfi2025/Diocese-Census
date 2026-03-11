import enum
from datetime import datetime
from typing import Optional, List, Any, Dict
from sqlalchemy import (
    create_engine, ForeignKey, String, Integer, Enum, JSON, DateTime, event
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
)
from app.core.config import settings

# 1. Database Setup
engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# 2. Enums and Models
class UserRole(str, enum.Enum):
    superuser = "superuser"
    chancellor = "chancellor"
    priest = "priest"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.priest)
    parish_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    records_submitted: Mapped[List["CensusRecord"]] = relationship(back_populates="author")
    audit_actions: Mapped[List["AuditLog"]] = relationship(back_populates="actor")

class CensusRecord(Base):
    __tablename__ = "census_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    parish_id: Mapped[str] = mapped_column(String(100), index=True)
    total_parishioners: Mapped[int] = mapped_column(default=0)
    baptisms: Mapped[int] = mapped_column(default=0)
    marriages: Mapped[int] = mapped_column(default=0)
    deaths: Mapped[int] = mapped_column(default=0)
    year: Mapped[int] = mapped_column(index=True)
    
    # Audit & Integrity
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)  # Optimistic Locking
    
    author: Mapped["User"] = relationship(back_populates="records_submitted")

    __mapper_args__ = {
        "version_id_col": version
    }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(100))
    record_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20)) # CREATE/UPDATE/DELETE
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    changed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    actor: Mapped["User"] = relationship(back_populates="audit_actions")

# 3. Data Integrity Trigger (Audit Listener)
@event.listens_for(CensusRecord, "before_update")
def audit_census_update(mapper, connection, target: CensusRecord):
    # We use target_state to inspect changes
    from sqlalchemy import inspect
    inspected = inspect(target)
    
    old_data = {}
    new_data = {}
    
    for attr in inspected.attrs:
        history = attr.history
        if history.has_changes():
            old_data[attr.key] = history.deleted[0] if history.deleted else None
            new_data[attr.key] = history.added[0] if history.added else None

    if not old_data and not new_data:
        return

    # Retrieve session to access .info
    session = Session.object_session(target)
    user_id = session.info.get("user_id") if session else None

    audit_entry = AuditLog(
        table_name="census_records",
        record_id=target.id,
        action="UPDATE",
        old_values=old_data,
        new_values=new_data,
        changed_by_id=user_id
    )
    # We use connection.execute to insert directly during the flush
    connection.execute(
        AuditLog.__table__.insert().values(
            table_name=audit_entry.table_name,
            record_id=audit_entry.record_id,
            action=audit_entry.action,
            old_values=audit_entry.old_values,
            new_values=audit_entry.new_values,
            changed_by_id=audit_entry.changed_by_id,
            timestamp=datetime.utcnow()
        )
    )
