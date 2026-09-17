import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import DamageInstance as DBDamageInstance, Survey as DBSurvey, Crew as DBCrew, WorkOrder as DBWorkOrder

class DatabaseDeterministicTools:
    """
    Evidence retrieval tools that query the PostgreSQL database directly.
    Provides verified numerical facts to ground the AI Copilot.
    """

    @staticmethod
    def get_survey_statistics(survey_id: Optional[str] = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            query = db.query(DBDamageInstance)
            if survey_id:
                query = query.filter(DBDamageInstance.survey_id == survey_id)
            
            damages = query.all()
            total = len(damages)
            by_type = {}
            by_severity = {}
            total_cost = 0.0
            rci_sum = 0.0

            for d in damages:
                by_type[d.damage_type] = by_type.get(d.damage_type, 0) + 1
                by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
                total_cost += d.estimated_repair_cost
                rci_sum += d.rci

            avg_rci = round(rci_sum / total, 1) if total > 0 else 0.0

            return {
                "total_damages": total,
                "by_type": by_type,
                "by_severity": by_severity,
                "total_estimated_cost": round(total_cost, 2),
                "avg_rci": avg_rci,
                "critical_count": by_severity.get("Critical", by_severity.get("critical", 0)),
                "high_count": by_severity.get("High", by_severity.get("high", 0))
            }
        finally:
            db.close()

    @staticmethod
    def get_damage_by_code(damage_code: str, survey_id: Optional[str] = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            query = db.query(DBDamageInstance).filter(
                (DBDamageInstance.damage_code == damage_code) | (DBDamageInstance.id == damage_code)
            )
            if survey_id:
                query = query.filter(DBDamageInstance.survey_id == survey_id)
            d = query.first()
            if not d:
                return {"error": f"Defect '{damage_code}' not found in active survey."}
            return {
                "damage_id": d.id,
                "damage_code": d.damage_code,
                "damage_type": d.damage_type,
                "severity": d.severity,
                "priority": d.priority,
                "confidence": d.confidence,
                "rci": d.rci,
                "estimated_repair_cost": d.estimated_repair_cost,
                "verification_status": d.verification_status,
                "gps_available": d.gps_available,
                "latitude": d.latitude,
                "longitude": d.longitude
            }
        finally:
            db.close()

    @staticmethod
    def get_critical_damages(survey_id: Optional[str] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(DBDamageInstance).filter(
                (DBDamageInstance.severity.ilike("critical")) | (DBDamageInstance.priority == 1)
            )
            if survey_id:
                query = query.filter(DBDamageInstance.survey_id == survey_id)
            damages = query.all()
            return [
                {
                    "damage_code": d.damage_code,
                    "damage_type": d.damage_type,
                    "severity": d.severity,
                    "priority": d.priority,
                    "rci": d.rci,
                    "estimated_repair_cost": d.estimated_repair_cost
                }
                for d in damages
            ]
        finally:
            db.close()

    @staticmethod
    def get_crew_workloads() -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            crews = db.query(DBCrew).all()
            return [
                {
                    "crew_code": c.crew_code,
                    "crew_name": c.crew_name,
                    "leader_name": c.leader_name,
                    "vehicle": c.vehicle_type,
                    "capacity_tons": c.capacity_tons,
                    "status": c.status,
                    "assigned_tasks": c.assigned_tasks_count,
                    "max_daily_jobs": c.max_daily_jobs
                }
                for c in crews
            ]
        finally:
            db.close()

tools = DatabaseDeterministicTools()
