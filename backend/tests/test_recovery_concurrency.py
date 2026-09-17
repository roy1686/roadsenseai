import sys
import time
from pathlib import Path
from datetime import datetime, timezone

backend_api_dir = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(backend_api_dir))

from app.main import app
from app.db.session import SessionLocal, recover_stale_processing_jobs
from app.db.models import Survey, ProcessingJob, User
from fastapi.testclient import TestClient

def test_failure_recovery_and_concurrency():
    client = TestClient(app)

    # 1. Login
    r_login = client.post('/api/v1/auth/login', json={'email': 'admin@roadsense.gov.in', 'password': 'Admin@12345'})
    token = r_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Test Stale Job Recovery on Reboot
    import uuid
    test_code = f"SURVEY-CRASH-{uuid.uuid4().hex[:6]}"
    db = SessionLocal()
    stale_survey = Survey(
        survey_code=test_code,
        title="Simulated Crashed Server Survey",
        video_filename="crash.mp4",
        status="PROCESSING"
    )
    db.add(stale_survey)
    db.flush()

    stale_job = ProcessingJob(
        survey_id=stale_survey.id,
        status="PROCESSING",
        current_step="YOLO AI Processing",
        progress_pct=50
    )
    db.add(stale_job)
    db.commit()
    stale_job_id = stale_job.id
    stale_survey_id = stale_survey.id
    db.close()

    # Trigger recovery function
    recover_stale_processing_jobs()

    db = SessionLocal()
    recovered_job = db.query(ProcessingJob).filter(ProcessingJob.id == stale_job_id).first()
    assert recovered_job.status == "FAILED"
    assert "restart" in recovered_job.error_message.lower()
    print("[PASS] 1. Stale Job Crash Recovery (State transitioned to FAILED)")

    # Clean up test survey
    stale_survey_obj = db.query(Survey).filter(Survey.id == stale_survey_id).first()
    db.delete(recovered_job)
    if stale_survey_obj:
        db.delete(stale_survey_obj)
    db.commit()
    db.close()

    # 3. Test RBAC Direct API Protection
    # Create VIEWER user
    client.post('/api/v1/auth/register', json={'email': 'test_viewer@roadsense.gov.in', 'password': 'Viewer@12345', 'full_name': 'Test Viewer', 'role': 'VIEWER'})
    r_vlogin = client.post('/api/v1/auth/login', json={'email': 'test_viewer@roadsense.gov.in', 'password': 'Viewer@12345'})
    v_token = r_vlogin.json()['access_token']
    v_headers = {'Authorization': f'Bearer {v_token}'}

    # Viewer attempts to call Engineer-only verification endpoint -> Must be 403 FORBIDDEN
    r_forbid = client.patch('/api/v1/damages/any-id/verify', json={'action': 'VERIFY'}, headers=v_headers)
    assert r_forbid.status_code == 403, f"Expected 403 Forbidden for Viewer, got {r_forbid.status_code}"
    print("[PASS] 2. RBAC Direct API Enforcement (Viewer blocked from Engineer endpoints with 403 Forbidden)")

    print("\n[ALL FAILURE RECOVERY & RBAC SECURITY TESTS PASSED!]")

if __name__ == "__main__":
    test_failure_recovery_and_concurrency()
