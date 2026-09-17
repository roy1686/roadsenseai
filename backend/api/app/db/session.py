from typing import Generator
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.models import Base, User, Crew, Survey, DamageInstance, WorkOrder, ProcessingJob, RoutePlan

# Support Railway / Cloud PostgreSQL URL format (postgres:// -> postgresql://)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling and check_same_thread=False for SQLite
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def recover_stale_processing_jobs():
    """Sweep database on boot and fail any jobs left in PROCESSING state."""
    db = SessionLocal()
    try:
        stale_jobs = db.query(ProcessingJob).filter(ProcessingJob.status == "PROCESSING").all()
        for job in stale_jobs:
            job.status = "FAILED"
            job.error_message = "Server restart interrupted active processing. Please retry."
            job.completed_at = datetime.now(timezone.utc)
            
            # Also update parent survey if it was PROCESSING
            if job.survey and job.survey.status == "PROCESSING":
                job.survey.status = "FAILED"
        
        if stale_jobs:
            db.commit()
            print(f"[RECOVERY] Recovered {len(stale_jobs)} stale processing jobs.")
    except Exception as e:
        db.rollback()
        print(f"[RECOVERY ERROR] Failed to recover stale jobs: {e}")
    finally:
        db.close()


def init_db():
    """Create all tables and seed default baseline roles & crews if missing."""
    Base.metadata.create_all(bind=engine)
    recover_stale_processing_jobs()
    
    db = SessionLocal()
    try:
        # Import password hashing dynamically to avoid circular dependencies
        from app.auth.security import get_password_hash

        # 1. Seed Default Users
        default_users = [
            {"email": "admin@roadsense.gov.in", "pass": "Admin@12345", "name": "System Administrator", "role": "ADMIN"},
            {"email": "engineer@roadsense.gov.in", "pass": "Engineer@12345", "name": "Lead Highway Engineer", "role": "ENGINEER"},
            {"email": "viewer@roadsense.gov.in", "pass": "Viewer@12345", "name": "Municipal Inspector", "role": "VIEWER"},
        ]

        for u in default_users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["pass"]),
                    full_name=u["name"],
                    role=u["role"],
                    is_active=True
                )
                db.add(user)

        # 2. Seed Standard Municipal Repair Crews
        default_crews = [
            {"code": "CREW-ALPHA", "name": "Odisha PWD Rapid Patch Crew 01", "lead": "Er. S. Mohapatra", "vehicle": "PatchMaster Truck #4", "capacity": 15.0, "status": "AVAILABLE", "max": 8},
            {"code": "CREW-BETA", "name": "BMC Smart City Quick Repair Unit", "lead": "R. K. Nayak", "vehicle": "JetPatcher Cold-Mix #2", "capacity": 8.0, "status": "AVAILABLE", "max": 6},
            {"code": "CREW-GAMMA", "name": "NHAI Highway Emergency Asphalt Unit", "lead": "Capt. V. Sharma", "vehicle": "InfraPave Heavy Patcher #1", "capacity": 25.0, "status": "AVAILABLE", "max": 10},
        ]

        for c in default_crews:
            existing = db.query(Crew).filter(Crew.crew_code == c["code"]).first()
            if not existing:
                crew = Crew(
                    crew_code=c["code"],
                    crew_name=c["name"],
                    leader_name=c["lead"],
                    vehicle_type=c["vehicle"],
                    capacity_tons=c["capacity"],
                    status=c["status"],
                    max_daily_jobs=c["max"]
                )
                db.add(crew)

        # 3. Seed Initial Demo Survey if no surveys exist
        existing_survey = db.query(Survey).first()
        if not existing_survey:
            demo_survey_id = "survey-demo-seed-0001"
            admin_user = db.query(User).filter(User.role == "ADMIN").first()
            
            demo_survey = Survey(
                id=demo_survey_id,
                survey_code="SURVEY-DEMO-SEED-01",
                title="Rural Road Corridor Baseline Survey (Demo)",
                road_name="Rural Road Corridor (MDR-04)",
                road_category="Rural Road / Major District Road",
                created_by=admin_user.id if admin_user else None,
                status="COMPLETED",
                video_filename="pothole_video.mp4",
                duration_sec=28.0,
                fps=25.0,
                resolution="1280x720",
                total_frames=28,
                usable_frames=27,
                blurry_frames=1,
                total_detections=33,
                unique_damages=7,
                total_estimated_cost=127200.0,
                avg_rci=77.2,
                gps_available=True,
                gps_source="embedded",
                model_name="YOLOv8n Road Damage (RDD2022)",
                model_version="v1.0.0",
                completed_at=datetime.now(timezone.utc)
            )
            db.add(demo_survey)
            db.flush()

            demo_damages_data = [
                {"code": "DMG-DEMO-101", "type": "Pothole", "sev": "Critical", "prio": 1, "conf": 0.96, "area": 1.45, "depth": 8.5, "rci": 94.2, "cost": 26100.0, "lat": 20.3012, "lon": 85.8345, "frame": 2, "t": 2.0},
                {"code": "DMG-DEMO-102", "type": "alligator crack", "sev": "High", "prio": 2, "conf": 0.92, "area": 4.80, "depth": 3.2, "rci": 82.5, "cost": 51000.0, "lat": 20.2934, "lon": 85.8456, "frame": 4, "t": 4.0},
                {"code": "DMG-DEMO-103", "type": "longitudinal crack", "sev": "Moderate", "prio": 3, "conf": 0.89, "area": 2.10, "depth": 2.0, "rci": 61.4, "cost": 8820.0, "lat": 20.2789, "lon": 85.7912, "frame": 7, "t": 7.0},
                {"code": "DMG-DEMO-104", "type": "other corruption", "sev": "High", "prio": 2, "conf": 0.94, "area": 3.20, "depth": 4.0, "rci": 81.0, "cost": 20000.0, "lat": 20.3125, "lon": 85.8641, "frame": 10, "t": 10.0},
                {"code": "DMG-DEMO-105", "type": "Pothole", "sev": "Critical", "prio": 1, "conf": 0.98, "area": 1.90, "depth": 11.2, "rci": 96.5, "cost": 34200.0, "lat": 20.2185, "lon": 85.7352, "frame": 14, "t": 14.0},
                {"code": "DMG-DEMO-106", "type": "transverse crack", "sev": "Low", "prio": 4, "conf": 0.86, "area": 1.10, "depth": 1.2, "rci": 41.0, "cost": 3465.0, "lat": 20.3541, "lon": 85.8198, "frame": 18, "t": 18.0},
                {"code": "DMG-DEMO-107", "type": "alligator crack", "sev": "Moderate", "prio": 3, "conf": 0.91, "area": 2.40, "depth": 2.5, "rci": 68.3, "cost": 20400.0, "lat": 19.8214, "lon": 85.9124, "frame": 22, "t": 22.0},
            ]

            for d in demo_damages_data:
                dmg = DamageInstance(
                    survey_id=demo_survey_id,
                    damage_code=d["code"],
                    track_id=int(d["code"].split("-")[-1]),
                    damage_type=d["type"],
                    severity=d["sev"],
                    priority=d["prio"],
                    confidence=d["conf"],
                    area_sqm=d["area"],
                    depth_cm=d["depth"],
                    rci=d["rci"],
                    estimated_repair_cost=d["cost"],
                    latitude=d["lat"],
                    longitude=d["lon"],
                    gps_available=True,
                    gps_source="embedded",
                    frame_image_path=f"/frames/frame_{d['frame']:05d}.jpg",
                    frame_index=d["frame"],
                    timestamp_sec=d["t"],
                    verification_status="UNVERIFIED",
                    ai_damage_type=d["type"],
                    ai_severity=d["sev"],
                    ai_confidence=d["conf"]
                )
                db.add(dmg)

            # Route plan
            from app.services.route_optimizer import optimize_damage_route
            route_res = optimize_damage_route(demo_damages_data)
            route = RoutePlan(
                survey_id=demo_survey_id,
                ordered_stops=route_res.get("stops", []),
                stops_count=route_res.get("stops_count", 0),
                estimated_distance_km=route_res.get("optimized_distance_km", 0.0),
                estimated_savings_pct=route_res.get("estimated_savings_pct", 0.0),
                distance_metric="Estimated Geodesic (Haversine)"
            )
            db.add(route)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[DB INIT ERROR] Failed to seed initial baseline data: {e}")
    finally:
        db.close()
