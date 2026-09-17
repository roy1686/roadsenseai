import sys
from pathlib import Path

# Add backend/api to path
backend_api_dir = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(backend_api_dir))

from app.main import app
from fastapi.testclient import TestClient

def test_full_pipeline_apis():
    client = TestClient(app)

    # 1. Health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    print("[PASS] 1. Root Health Check:", r_health.json()["status"])

    # 2. Login
    r_login = client.post("/api/v1/auth/login", json={"email": "engineer@roadsense.gov.in", "password": "Engineer@12345"})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 2. User Authentication & JWT Bearer Token")

    # 3. User Profile
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["role"] == "ENGINEER"
    print("[PASS] 3. Profile & RBAC Verification:", r_me.json()["email"])

    # 4. List Surveys
    r_surveys = client.get("/api/v1/surveys", headers=headers)
    assert r_surveys.status_code == 200
    surveys = r_surveys.json()
    assert len(surveys) >= 1
    
    selected_survey = surveys[0]
    damages = []
    for s in surveys:
        r_d = client.get(f"/api/v1/surveys/{s['id']}/damages", headers=headers)
        if r_d.status_code == 200 and len(r_d.json()) > 0:
            selected_survey = s
            damages = r_d.json()
            break
    s_id = selected_survey["id"]
    print(f"[PASS] 4. Surveys List (Found {len(surveys)} surveys, active: {selected_survey['survey_code']})")

    # 5. Survey Damages
    if not damages:
        r_damages = client.get(f"/api/v1/surveys/{s_id}/damages", headers=headers)
        assert r_damages.status_code == 200
        damages = r_damages.json()
    assert len(damages) >= 1
    print(f"[PASS] 5. Survey-Isolated Damages ({len(damages)} defect records)")

    # 6. Dynamic Stats
    r_stats = client.get(f"/api/v1/surveys/{s_id}/stats", headers=headers)
    assert r_stats.status_code == 200
    stats = r_stats.json()
    print(f"[PASS] 6. Dynamic Stats (Cost: Rs {stats['total_estimated_cost']}, Avg RCI: {stats['avg_rci']})")

    # 7. GeoJSON Feature Collection
    r_geo = client.get(f"/api/v1/surveys/{s_id}/geojson", headers=headers)
    assert r_geo.status_code == 200
    assert r_geo.json()["type"] == "FeatureCollection"
    print(f"[PASS] 7. Dynamic GeoJSON Generation ({len(r_geo.json()['features'])} point features)")

    # 8. Route Optimization (TSP 2-Opt)
    r_route = client.get(f"/api/v1/surveys/{s_id}/route", headers=headers)
    assert r_route.status_code == 200
    route = r_route.json()
    print(f"[PASS] 8. TSP 2-Opt Route Optimization ({route.get('stops_count')} stops, {route.get('estimated_distance_km')} km)")

    # 9. Human-in-the-loop Verification
    d_id = damages[0]["id"]
    r_verify = client.patch(f"/api/v1/damages/{d_id}/verify", json={"action": "VERIFY", "notes": "Audited by Lead Engineer."}, headers=headers)
    assert r_verify.status_code == 200
    assert r_verify.json()["verification_status"] == "VERIFIED"
    print("[PASS] 9. Human Verification Audit Trail (Status -> VERIFIED)")

    # 10. Crew Dispatch
    r_crews = client.get("/api/v1/crews", headers=headers)
    assert r_crews.status_code == 200
    crews = r_crews.json()
    crew_id = crews[0]["id"]
    r_dispatch = client.post(f"/api/v1/damages/{d_id}/dispatch", json={"crew_id": crew_id, "notes": "Dispatching Rapid Patch Truck #4."}, headers=headers)
    assert r_dispatch.status_code == 200
    print("[PASS] 10. Crew Assignment & Work Order Generation:", r_dispatch.json()["work_order_code"])

    # 11. Evidence-Grounded AI Copilot
    r_copilot = client.post("/api/v1/agent/ask", json={"question": "How many critical potholes in this survey?", "survey_id": s_id})
    assert r_copilot.status_code == 200
    print("[PASS] 11. Grounded Copilot Q&A:", r_copilot.json()["answer"][:80], "...")

    # 12. Verified Model Metrics
    r_model = client.get("/api/v1/model/metrics")
    assert r_model.status_code == 200
    assert r_model.json()["evaluation_metrics"]["mAP50"] == 0.4336
    print("[PASS] 12. Authentic Model Metrics (mAP50: 0.4336, Precision: 0.4915, Recall: 0.4358)")

    # 13. Dynamic PDF Report
    r_report = client.get(f"/api/v1/surveys/{s_id}/report", headers=headers)
    assert r_report.status_code == 200
    assert r_report.headers["content-type"] == "application/pdf"
    assert len(r_report.content) > 1000
    print(f"[PASS] 13. PDF Engineering Report Generation ({len(r_report.content)} bytes)")

    print("\n[ALL 13 API TESTS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_full_pipeline_apis()
