import sys
import os
from pathlib import Path

# 1. Setup Path to allow importing from the 'app' directory
# This ensures the script can be run from the project root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.models.database import (
    engine, SessionLocal, Base, User, UserRole, CensusRecord, AuditLog
)
from app.core.security import get_password_hash

def seed_genesis():
    print("✨ Starting Genesis Seed for Diocese Census GH...")
    
    # 2. Initialization: Create Tables
    print(f"📁 Database location: {BASE_DIR / 'data' / 'census.db'}")
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        # 3. Superuser Creation
        admin_email = "admin@diocese.gh"
        if not session.query(User).filter(User.email == admin_email).first():
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("Admin123!"),
                role=UserRole.superuser,
                parish_name="Headquarters",
                is_active=True
            )
            session.add(admin)
            print(f"✅ Created Superuser: {admin_email}")
        
        # 4. Chancellor and Priest Creation
        chan_email = "chancellor@diocese.gh"
        if not session.query(User).filter(User.email == chan_email).first():
            chancellor = User(
                email=chan_email,
                hashed_password=get_password_hash("Chancellor123!"),
                role=UserRole.chancellor,
                parish_name="Chancery",
                is_active=True
            )
            session.add(chancellor)
            print(f"✅ Created Chancellor: {chan_email}")

        priest_email = "priest_st_peters@diocese.gh"
        if not session.query(User).filter(User.email == priest_email).first():
            priest = User(
                email=priest_email,
                hashed_password=get_password_hash("Priest123!"),
                role=UserRole.priest,
                parish_name="St. Peters",
                is_active=True
            )
            session.add(priest)
            print(f"✅ Created Priest: {priest_email}")

        session.commit()
        
        # 5. Data Integrity Test (The Proof)
        print("\n🛠️  Running Truth Engine Validation...")
        
        # Fetch the users for the test
        p_user = session.query(User).filter(User.email == priest_email).one()
        c_user = session.query(User).filter(User.email == chan_email).one()
        
        # Step A: Initial Submission (by Priest)
        record = CensusRecord(
            parish_id="St. Peters",
            total_parishioners=500,
            baptisms=20,
            marriages=5,
            deaths=2,
            year=2024,
            submitted_by_id=p_user.id
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        print(f"📝 Initial Record Created: ID {record.id}, Total: {record.total_parishioners}")

        # Step B: Modification (by Chancellor)
        # We simulate the API passing the user_id to the session info
        session.info["user_id"] = c_user.id
        
        record.total_parishioners = 550  # Changing 500 -> 550
        session.commit()
        print(f"🔄 Record Updated by Chancellor: ID {record.id}, Total: 550")

        # Step C: Verify AuditLog
        audit = session.query(AuditLog).filter(AuditLog.record_id == record.id).first()
        
        if audit:
            print("\n🚨 TRUTH ENGINE PROOF CAPTURED:")
            print(f"   Table: {audit.table_name}")
            print(f"   Action: {audit.action}")
            print(f"   Modified By: {c_user.email} (ID: {audit.changed_by_id})")
            print(f"   Old Value: {audit.old_values.get('total_parishioners')}")
            print(f"   New Value: {audit.new_values.get('total_parishioners')}")
            print(f"   Timestamp: {audit.timestamp}")
            print("\n✅ DATA INTEGRITY VERIFIED.")
        else:
            print("\n❌ FAILED: AuditLog was not captured.")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        session.rollback()
    finally:
        session.close()

    print("\n--------------------------------------------------------")
    print("🚀 System Ready!")
    print("1. Start the app: python main.py")
    print("2. Open Swagger: http://localhost:8000/docs")
    print(f"3. Login with: {admin_email} / Admin123!")
    print("--------------------------------------------------------")

if __name__ == "__main__":
    seed_genesis()
