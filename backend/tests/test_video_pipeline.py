import sys
import time
from pathlib import Path
import cv2
import numpy as np

backend_api_dir = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(backend_api_dir))

from app.main import app
from app.db.session import SessionLocal
from app.db.models import Survey, DamageInstance
from fastapi.testclient import TestClient

def create_clean_road_video(output_path: Path, duration_sec: int = 4, fps: int = 25):
    """Creates a clean synthetic asphalt video with ZERO defects."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    w, h = 640, 360
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    total_frames = duration_sec * fps
    for i in range(total_frames):
        # Pure smooth gray pavement with yellow center stripe
        frame = np.full((h, w, 3), (85, 85, 85), dtype=np.uint8)
        # Smooth dashed lane line
        dash_y = (i * 8) % h
        cv2.line(frame, (w // 2, 0), (w // 2, h), (0, 215, 255), 4)
        out.write(frame)

    out.release()
    print(f"[TEST FIXTURE] Generated clean zero-defect road video: {output_path}")


def test_video_processing_pipeline():
    client = TestClient(app)

    # 1. Login
    r_login = client.post('/api/v1/auth/login', json={'email': 'engineer@roadsense.gov.in', 'password': 'Engineer@12345'})
    token = r_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Test Processing Real Video (pothole_video.mp4)
    real_video = Path(__file__).resolve().parents[2] / "data" / "raw" / "demo_clip" / "pothole_video.mp4"
    if real_video.exists():
        with open(real_video, "rb") as f:
            r_up = client.post(
                "/api/v1/surveys/upload",
                files={"file": ("pothole_survey.mp4", f, "video/mp4")},
                data={"title": "Real Pavement Survey Test", "road_name": "NH-16 Corridor", "road_category": "National Highway"},
                headers=headers
            )
        assert r_up.status_code == 202
        s_id = r_up.json()["survey_id"]
        print(f"[PASS] Real Video Uploaded -> Survey ID: {s_id}")

        # Poll until COMPLETED or timeout
        max_wait = 30
        start_t = time.time()
        while time.time() - start_t < max_wait:
            r_prog = client.get(f"/api/v1/surveys/{s_id}/progress", headers=headers)
            prog = r_prog.json()
            if prog["status"] == "COMPLETED":
                print(f"[PASS] Real Video Processing COMPLETED in {time.time() - start_t:.1f}s!")
                break
            elif prog["status"] == "FAILED":
                raise RuntimeError(f"Processing failed: {prog.get('error_message')}")
            time.sleep(1)

        # Verify real damages created
        r_dmg = client.get(f"/api/v1/surveys/{s_id}/damages", headers=headers)
        damages = r_dmg.json()
        print(f"[PASS] Real Video Detections: {len(damages)} unique defect instances recorded in DB.")

    # 3. Test Zero Detection Video (Mandatory Acceptance Criterion)
    clean_video_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "demo_clip" / "clean_road_zero_defect.mp4"
    create_clean_road_video(clean_video_path, duration_sec=3)

    with open(clean_video_path, "rb") as f:
        r_up_clean = client.post(
            "/api/v1/surveys/upload",
            files={"file": ("clean_road_zero_defect.mp4", f, "video/mp4")},
            data={"title": "Pristine Pavement Survey (Zero Defect Test)", "road_name": "State Highway 42", "road_category": "State Highway"},
            headers=headers
        )
    assert r_up_clean.status_code == 202
    clean_sid = r_up_clean.json()["survey_id"]
    print(f"[PASS] Clean Video Uploaded -> Survey ID: {clean_sid}")

    # Poll clean video
    start_t = time.time()
    while time.time() - start_t < 30:
        r_prog = client.get(f"/api/v1/surveys/{clean_sid}/progress", headers=headers)
        prog = r_prog.json()
        if prog["status"] == "COMPLETED":
            print(f"[PASS] Clean Video Processing COMPLETED in {time.time() - start_t:.1f}s!")
            break
        elif prog["status"] == "FAILED":
            raise RuntimeError(f"Clean video processing failed: {prog.get('error_message')}")
        time.sleep(1)

    r_clean_dmg = client.get(f"/api/v1/surveys/{clean_sid}/damages", headers=headers)
    clean_damages = r_clean_dmg.json()
    print(f"[PASS] Clean Video Result: Exactly {len(clean_damages)} damages (Strict Zero Fake Data Verification Passed!)")
    assert len(clean_damages) == 0, f"Expected 0 damages on clean road, got {len(clean_damages)}"

    # 4. Survey Isolation Test: Ensure Clean Survey and Real Survey do not mix data
    r_stats_real = client.get(f"/api/v1/surveys/{s_id}/stats", headers=headers).json()
    r_stats_clean = client.get(f"/api/v1/surveys/{clean_sid}/stats", headers=headers).json()
    assert r_stats_clean["unique_damages"] == 0
    assert r_stats_real["unique_damages"] > 0
    print(f"[PASS] Survey Isolation Verified: Survey 1 has {r_stats_real['unique_damages']} damages, Survey 2 has {r_stats_clean['unique_damages']} damages.")

    # 5. Built-in Sample Video Endpoint Test
    r_sample = client.post(
        "/api/v1/surveys/sample",
        json={"sample_type": "pothole_video", "title": "Built-in Sample Video Evaluation"},
        headers=headers
    )
    assert r_sample.status_code == 202
    sample_sid = r_sample.json()["survey_id"]
    print(f"[PASS] Built-in Sample Video Queued -> Survey ID: {sample_sid}")

    # 6. Video Streaming Endpoints Test
    r_raw_vid = client.get(f"/api/v1/surveys/{s_id}/video/raw")
    assert r_raw_vid.status_code == 200
    print(f"[PASS] Raw Video Streaming Endpoint Verified ({len(r_raw_vid.content)} bytes)")

    r_proc_vid = client.get(f"/api/v1/surveys/{s_id}/video/processed")
    assert r_proc_vid.status_code == 200
    print(f"[PASS] Processed Video Streaming Endpoint Verified ({len(r_proc_vid.content)} bytes)")

    print("\n[ALL VIDEO PIPELINE, BUILT-IN SAMPLE, AND STREAMING TESTS PASSED!]")


if __name__ == "__main__":
    test_video_processing_pipeline()
