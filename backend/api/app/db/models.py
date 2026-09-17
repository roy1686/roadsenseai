import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="VIEWER")  # ADMIN, ENGINEER, VIEWER, CREW
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    surveys = relationship("Survey", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    road_name = Column(String(255), nullable=False, default="Surveyed Corridor")
    road_category = Column(String(100), nullable=False, default="Municipal Arterial")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # State: QUEUED, PROCESSING, COMPLETED, FAILED
    status = Column(String(50), nullable=False, default="QUEUED", index=True)
    
    # Video metadata
    video_filename = Column(String(255), nullable=False)
    video_sha256 = Column(String(64), nullable=True, index=True)
    video_path = Column(String(512), nullable=True)
    duration_sec = Column(Float, default=0.0)
    fps = Column(Float, default=0.0)
    resolution = Column(String(50), default="1280x720")
    
    # Summary metrics
    total_frames = Column(Integer, default=0)
    usable_frames = Column(Integer, default=0)
    blurry_frames = Column(Integer, default=0)
    total_detections = Column(Integer, default=0)
    unique_damages = Column(Integer, default=0)
    total_estimated_cost = Column(Float, default=0.0)
    avg_rci = Column(Float, default=0.0)
    gps_available = Column(Boolean, default=False)
    gps_source = Column(String(100), default="unavailable")
    
    # Model provenance
    model_name = Column(String(100), default="YOLOv8n Road Damage (RDD2022)")
    model_version = Column(String(50), default="v1.0.0")
    confidence_threshold = Column(Float, default=0.20)
    iou_threshold = Column(Float, default=0.45)
    sampling_interval_sec = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="surveys")
    jobs = relationship("ProcessingJob", back_populates="survey", cascade="all, delete-orphan")
    frames = relationship("FrameRecord", back_populates="survey", cascade="all, delete-orphan")
    detections = relationship("DetectionRecord", back_populates="survey", cascade="all, delete-orphan")
    damages = relationship("DamageInstance", back_populates="survey", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="survey", cascade="all, delete-orphan")
    route_plans = relationship("RoutePlan", back_populates="survey", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="QUEUED", index=True)  # QUEUED, PROCESSING, COMPLETED, FAILED
    current_step = Column(String(100), default="Initialized")
    progress_pct = Column(Integer, default=0)
    logs = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="jobs")


class FrameRecord(Base):
    __tablename__ = "frame_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    frame_number = Column(Integer, nullable=False)
    saved_index = Column(Integer, nullable=False)
    timestamp_sec = Column(Float, nullable=False)
    filename = Column(String(255), nullable=False)
    laplacian_variance = Column(Float, default=0.0)
    brightness = Column(Float, default=0.0)
    quality_status = Column(String(50), default="GOOD")  # GOOD, BLURRY, DARK, OVEREXPOSED
    is_blurry = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="frames")
    detections = relationship("DetectionRecord", back_populates="frame", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_frame_survey_index", "survey_id", "saved_index"),
    )


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    frame_id = Column(String(36), ForeignKey("frame_records.id"), nullable=True, index=True)
    frame_saved_index = Column(Integer, nullable=False)
    timestamp_sec = Column(Float, nullable=False)
    track_id = Column(Integer, nullable=True, index=True)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    damage_class = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="detections")
    frame = relationship("FrameRecord", back_populates="detections")


class DamageInstance(Base):
    __tablename__ = "damage_instances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    damage_code = Column(String(64), nullable=False, index=True)
    track_id = Column(Integer, nullable=True, index=True)
    
    # Current active values (either AI prediction or human-verified)
    damage_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)  # CRITICAL, HIGH, MODERATE, LOW
    priority = Column(Integer, nullable=False, default=4, index=True)  # 1, 2, 3, 4
    confidence = Column(Float, nullable=False)
    
    # Physics & Costing
    area_sqm = Column(Float, default=1.0)
    depth_cm = Column(Float, default=3.0)
    rci = Column(Float, default=50.0)
    estimated_repair_cost = Column(Float, default=0.0)
    
    # Geo reference
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_available = Column(Boolean, default=False)
    gps_source = Column(String(100), default="unavailable")
    
    # Visual Evidence
    frame_image_path = Column(String(512), nullable=True)
    frame_index = Column(Integer, default=0)
    timestamp_sec = Column(Float, default=0.0)
    detection_count = Column(Integer, default=1)
    
    # Human-In-The-Loop Audit Trails
    verification_status = Column(String(50), default="UNVERIFIED", index=True)  # UNVERIFIED, VERIFIED, REJECTED, MODIFIED
    ai_damage_type = Column(String(100), nullable=False)
    ai_severity = Column(String(50), nullable=False)
    ai_confidence = Column(Float, nullable=False)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="damages")
    work_orders = relationship("WorkOrder", back_populates="damage", cascade="all, delete-orphan")


class Crew(Base):
    __tablename__ = "crews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    crew_code = Column(String(64), unique=True, nullable=False, index=True)
    crew_name = Column(String(255), nullable=False)
    leader_name = Column(String(255), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    capacity_tons = Column(Float, default=10.0)
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, BUSY, OFF_DUTY
    assigned_tasks_count = Column(Integer, default=0)
    max_daily_jobs = Column(Integer, default=8)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    work_orders = relationship("WorkOrder", back_populates="assigned_crew")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    damage_id = Column(String(36), ForeignKey("damage_instances.id"), nullable=False, index=True)
    work_order_code = Column(String(64), unique=True, nullable=False, index=True)
    assigned_crew_id = Column(String(36), ForeignKey("crews.id"), nullable=True, index=True)
    
    # State lifecycle: DETECTED -> VERIFIED -> ASSIGNED -> IN_REPAIR -> REPAIRED -> CLOSED
    status = Column(String(50), default="DETECTED", nullable=False, index=True)
    priority = Column(Integer, default=4)
    estimated_cost = Column(Float, default=0.0)
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="work_orders")
    damage = relationship("DamageInstance", back_populates="work_orders")
    assigned_crew = relationship("Crew", back_populates="work_orders")


class RoutePlan(Base):
    __tablename__ = "route_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    survey_id = Column(String(36), ForeignKey("surveys.id"), nullable=False, index=True)
    crew_id = Column(String(36), ForeignKey("crews.id"), nullable=True)
    ordered_stops = Column(JSON, nullable=False)
    stops_count = Column(Integer, default=0)
    estimated_distance_km = Column(Float, default=0.0)
    estimated_savings_pct = Column(Float, default=0.0)
    distance_metric = Column(String(100), default="Estimated Geodesic (Haversine)")
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    survey = relationship("Survey", back_populates="route_plans")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=get_utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
