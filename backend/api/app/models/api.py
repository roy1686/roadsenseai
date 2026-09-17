from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# -------------------------------------------------------------
# Auth Schemas
# -------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    full_name: str
    role: Optional[str] = "VIEWER"  # ADMIN, ENGINEER, VIEWER


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# -------------------------------------------------------------
# Survey Schemas
# -------------------------------------------------------------
class SurveyCreateRequest(BaseModel):
    title: Optional[str] = "Survey Corridor Analysis"
    road_name: Optional[str] = "Surveyed Corridor"
    road_category: Optional[str] = "Municipal Arterial"


class SampleSurveyRequest(BaseModel):
    sample_type: Optional[str] = "pothole_video"
    title: Optional[str] = "Rural Road Pothole Corridor (Built-in Demo)"
    road_name: Optional[str] = "Rural Road Corridor (MDR-04)"
    road_category: Optional[str] = "Rural Road / Major District Road"


class SurveyResponse(BaseModel):
    id: str
    survey_code: str
    title: str
    road_name: str
    road_category: str
    status: str
    video_filename: str
    duration_sec: float
    fps: float
    resolution: str
    total_frames: int
    usable_frames: int
    blurry_frames: int
    total_detections: int
    unique_damages: int
    total_estimated_cost: float
    avg_rci: float
    gps_available: bool
    gps_source: str
    model_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobProgressResponse(BaseModel):
    survey_id: str
    status: str
    current_step: str
    progress_pct: int
    logs: List[str]
    error_message: Optional[str] = None


class SurveyStatsResponse(BaseModel):
    survey_id: str
    survey_code: str
    total_frames: int
    usable_frames: int
    total_detections: int
    unique_damages: int
    total_estimated_cost: float
    avg_rci: float
    gps_available: bool
    gps_source: str
    severity_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]


# -------------------------------------------------------------
# Damage Schemas
# -------------------------------------------------------------
class DamageResponse(BaseModel):
    id: str
    survey_id: str
    damage_code: str
    damage_type: str
    severity: str
    priority: int
    confidence: float
    area_sqm: float
    depth_cm: float
    rci: float
    estimated_repair_cost: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_available: bool
    gps_source: str
    frame_image_path: Optional[str] = None
    frame_index: int
    timestamp_sec: float
    verification_status: str
    ai_damage_type: str
    ai_severity: str
    ai_confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class DamageVerifyRequest(BaseModel):
    action: str = Field(..., description="'VERIFY' | 'REJECT' | 'MODIFY'")
    final_severity: Optional[str] = None
    final_damage_type: Optional[str] = None
    notes: Optional[str] = None


class DamageDispatchRequest(BaseModel):
    crew_id: str
    scheduled_date: Optional[str] = None
    notes: Optional[str] = None


# -------------------------------------------------------------
# Crew & Work Order Schemas
# -------------------------------------------------------------
class CrewResponse(BaseModel):
    id: str
    crew_code: str
    crew_name: str
    leader_name: str
    vehicle_type: str
    capacity_tons: float
    status: str
    assigned_tasks_count: int
    max_daily_jobs: int

    class Config:
        from_attributes = True


class WorkOrderResponse(BaseModel):
    id: str
    work_order_code: str
    survey_id: str
    damage_id: str
    assigned_crew_id: Optional[str] = None
    status: str
    priority: int
    estimated_cost: float
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Copilot & Agent Schemas
# -------------------------------------------------------------
class AgentRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    survey_id: Optional[str] = None


class AgentResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    evidence: List[Dict[str, Any]]
    data: Dict[str, Any]
