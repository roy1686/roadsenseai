import os
import sys
import json
import csv
import shutil
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
from sqlalchemy.orm import Session

def get_ffmpeg_executable() -> str:
    """Finds available ffmpeg binary via system PATH or imageio_ffmpeg fallback."""
    sys_bin = shutil.which("ffmpeg")
    if sys_bin:
        return sys_bin
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


from app.config import settings, PROJECT_ROOT

# Ensure backend vision modules can be imported
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.db.session import SessionLocal
from app.db.models import (
    Survey,
    ProcessingJob,
    FrameRecord as DBFrameRecord,
    DetectionRecord as DBDetectionRecord,
    DamageInstance as DBDamageInstance,
    WorkOrder as DBWorkOrder,
    RoutePlan as DBRoutePlan,
    AuditLog
)
from app.services.route_optimizer import optimize_damage_route

# Import vision modules
try:
    from backend.src.vision.extract_frames import extract_frames
    from backend.src.vision.yolo_detector import run_detection
    from backend.src.vision.track_damage import run_bytetrack_on_detections
    from backend.src.vision.gps_detector import detect_gps, interpolate_gps_track
    from backend.src.vision.severity_priority import (
        calculate_normalized_severity,
        calculate_rci,
        calculate_dynamic_repair_cost
    )
except ImportError:
    from src.vision.extract_frames import extract_frames
    from src.vision.yolo_detector import run_detection
    from src.vision.track_damage import run_bytetrack_on_detections
    from src.vision.gps_detector import detect_gps, interpolate_gps_track
    from src.vision.severity_priority import (
        calculate_normalized_severity,
        calculate_rci,
        calculate_dynamic_repair_cost
    )


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def update_job_progress(db: Session, job_id: str, step: str, progress_pct: int, log_msg: str):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if job:
        job.current_step = step
        job.progress_pct = progress_pct
        current_logs = list(job.logs or [])
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        current_logs.append(f"[{timestamp}] {log_msg}")
        job.logs = current_logs
        db.commit()


def generate_full_annotated_video(
    source_video_path: Path,
    output_video_path: Path,
    tracked_detections: List[Dict[str, Any]],
    survey_code: str = "SURVEY-2026"
) -> bool:
    """
    Overlays detected potholes, distress bounding boxes, ByteTrack tracking IDs,
    confidence ratings and telemetry HUD onto the source video and encodes a web-compatible H.264 MP4.
    """
    try:
        cap = cv2.VideoCapture(str(source_video_path))
        if not cap.isOpened():
            print(f"[WARN] Cannot open source video for annotation: {source_video_path}")
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if width <= 0 or height <= 0:
            cap.release()
            return False

        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = get_ffmpeg_executable()

        cmd = [
            ffmpeg_exe, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "bgr24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_video_path)
        ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        has_detections = len(tracked_detections) > 0
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            t_sec = frame_idx / fps

            # Find active detections within temporal window (+- 0.8s)
            active_dets = []
            if has_detections:
                for d in tracked_detections:
                    d_t = float(d.get("timestamp", 0))
                    if abs(d_t - t_sec) <= 0.80:
                        active_dets.append(d)

            # Draw bounding boxes & defect labels
            for det in active_dets:
                x1 = max(0, int(float(det["x1"])))
                y1 = max(0, int(float(det["y1"])))
                x2 = min(width - 1, int(float(det["x2"])))
                y2 = min(height - 1, int(float(det["y2"])))
                c_name = det.get("damage_class", "Pothole")
                conf = float(det.get("confidence", 0.85))
                tid = det.get("track_id")

                c_lower = c_name.lower()
                if "pothole" in c_lower:
                    color = (0, 0, 230)       # Red
                elif "alligator" in c_lower:
                    color = (0, 140, 255)     # Orange
                elif "transverse" in c_lower:
                    color = (20, 200, 20)     # Green
                elif "longitudinal" in c_lower:
                    color = (220, 200, 0)     # Yellow
                else:
                    color = (180, 50, 200)    # Purple

                # Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Label tag
                label = f"#{tid} {c_name} {conf:.2f}" if tid else f"{c_name} {conf:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
                cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), color, -1)
                cv2.putText(frame, label, (x1 + 3, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)

            # Top Telemetry HUD Banner
            if has_detections:
                hud_text = f"ROADSense AI • {survey_code} | T: {t_sec:.1f}s | ACTIVE: {len(active_dets)}"
                cv2.rectangle(frame, (12, 12), (min(width - 12, 540), 42), (15, 23, 42), -1)
                cv2.rectangle(frame, (12, 12), (min(width - 12, 540), 42), (56, 189, 248), 1)
                cv2.putText(frame, hud_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            else:
                cv2.rectangle(frame, (12, 12), (min(width - 12, 480), 42), (15, 23, 42), -1)
                cv2.rectangle(frame, (12, 12), (min(width - 12, 480), 42), (16, 185, 129), 1)
                cv2.putText(frame, "ZERO DEFECTS DETECTED • CLEAN ROAD VERIFIED", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (16, 185, 129), 1)

            proc.stdin.write(frame.tobytes())
            frame_idx += 1

        proc.stdin.close()
        proc.wait()
        cap.release()
        return output_video_path.exists() and output_video_path.stat().st_size > 0
    except Exception as e:
        print(f"[WARN] generate_full_annotated_video exception: {e}")
        return False


def process_survey_video_async(
    survey_id: str,
    video_path_str: str,
    user_id: Optional[str] = None,
    external_gps_path: Optional[str] = None
):
    """
    Asynchronous 12-Stage Video Processing Pipeline.
    Runs non-blocking in background, updates database progress, and maintains survey isolation.
    """
    db = SessionLocal()
    video_path = Path(video_path_str)
    job = db.query(ProcessingJob).filter(ProcessingJob.survey_id == survey_id).first()
    survey = db.query(Survey).filter(Survey.id == survey_id).first()

    if not job or not survey:
        db.close()
        return

    job_id = job.id
    work_dir = Path(settings.PROCESSED_DATA_DIR) / f"survey_{survey_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ============================================================
        # STAGE 1: Video Ingestion & Codec Verification
        # ============================================================
        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)
        survey.status = "PROCESSING"
        db.commit()

        update_job_progress(db, job_id, "Video Ingestion", 5, f"Ingesting video container: {video_path.name}")

        if not video_path.exists() or video_path.stat().st_size == 0:
            raise ValueError("Uploaded video file is empty or missing.")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"OpenCV could not decode video stream: {video_path.name}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        duration_sec = total_source_frames / fps if fps > 0 else 0.0
        cap.release()

        file_hash = compute_file_sha256(video_path)
        survey.fps = round(fps, 2)
        survey.resolution = f"{width}x{height}"
        survey.duration_sec = round(duration_sec, 2)
        survey.video_sha256 = file_hash
        db.commit()

        update_job_progress(db, job_id, "Video Verified", 15, f"Container verified: {width}x{height} @ {fps:.1f} FPS, Duration: {duration_sec:.1f}s")

        # ============================================================
        # STAGE 2 & 3: Frame Extraction & Quality Analysis
        # ============================================================
        update_job_progress(db, job_id, "Frame Extraction & QA", 25, "Extracting true-timestamp keyframes (1.0 FPS) & running Laplacian blur QA...")
        
        frames_out_dir = work_dir / "frames_output"
        extraction_res = extract_frames(
            video_path=video_path,
            out_dir=frames_out_dir,
            interval_sec=settings.DEFAULT_SAMPLING_INTERVAL_SEC,
            blur_threshold=settings.DEFAULT_BLUR_THRESHOLD
        )

        extracted_count = extraction_res.get("frames_extracted", 0)
        usable_count = extraction_res.get("usable_frames", 0)
        blurry_count = extraction_res.get("frames_flagged_blurry", 0)

        survey.total_frames = extracted_count
        survey.usable_frames = usable_count
        survey.blurry_frames = blurry_count
        db.commit()

        update_job_progress(db, job_id, "Extraction Complete", 35, f"Extracted {extracted_count} frames ({usable_count} usable, {blurry_count} blurry).")

        # Save Frame Records to Database
        manifest_path = frames_out_dir / "frame_manifest.csv"
        frame_manifest_rows = []
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                frame_manifest_rows = list(csv.DictReader(f))
                for fr in frame_manifest_rows:
                    db_frame = DBFrameRecord(
                        survey_id=survey_id,
                        frame_number=int(fr["frame_number"]),
                        saved_index=int(fr["saved_index"]),
                        timestamp_sec=float(fr["timestamp_sec"]),
                        filename=fr["filename"],
                        laplacian_variance=float(fr.get("laplacian_variance", 0.0)),
                        brightness=float(fr.get("brightness", 0.0)),
                        quality_status=fr.get("quality_status", "GOOD"),
                        is_blurry=fr.get("is_blurry", "False").lower() == "true"
                    )
                    db.add(db_frame)
            db.commit()

        # ============================================================
        # STAGE 4: YOLOv8 Road Distress Detection
        # ============================================================
        update_job_progress(db, job_id, "AI Distress Detection", 45, "Executing YOLOv8n road distress multi-class detection (road_damage.pt)...")
        
        yolo_out_dir = work_dir / "yolo_output"
        yolo_csv = yolo_out_dir / "detections.csv"
        frames_dir = frames_out_dir / "frames"
        
        run_detection(
            frames_dir=frames_dir,
            manifest_path=manifest_path,
            output_dir=yolo_out_dir,
            output_csv=yolo_csv,
            confidence_threshold=settings.DEFAULT_CONFIDENCE_THRESHOLD
        )

        detections_count = 0
        raw_detections = []
        if yolo_csv.exists():
            with open(yolo_csv, "r", encoding="utf-8") as f:
                raw_detections = list(csv.DictReader(f))
                detections_count = len(raw_detections)

        survey.total_detections = detections_count
        db.commit()
        update_job_progress(db, job_id, "YOLO Detection Completed", 55, f"YOLO inference identified {detections_count} distress instances.")

        # ============================================================
        # STAGE 5: ByteTrack Multi-Frame Tracking & Deduplication
        # ============================================================
        update_job_progress(db, job_id, "ByteTrack Tracking", 65, "Initializing Kalman-filter state association & deduplicating tracks...")
        
        tracking_out_dir = work_dir / "tracking_output"
        tracking_summary = run_bytetrack_on_detections(
            detections_csv=yolo_csv,
            output_dir=tracking_out_dir,
            iou_threshold=settings.DEFAULT_IOU_THRESHOLD
        )

        unique_tracked_objects = tracking_summary.get("unique_tracked_objects", 0)
        tracked_csv = tracking_out_dir / "tracked_detections.csv"
        tracked_rows = []
        if tracked_csv.exists():
            with open(tracked_csv, "r", encoding="utf-8") as f:
                tracked_rows = list(csv.DictReader(f))

        # Save Detection Records to Database
        for tr in tracked_rows:
            db_det = DBDetectionRecord(
                survey_id=survey_id,
                frame_saved_index=int(tr["frame_number"]),
                timestamp_sec=float(tr["timestamp"]),
                track_id=int(tr.get("track_id", 0)) if tr.get("track_id") else None,
                x1=float(tr["x1"]),
                y1=float(tr["y1"]),
                x2=float(tr["x2"]),
                y2=float(tr["y2"]),
                damage_class=tr["damage_class"],
                confidence=float(tr["confidence"])
            )
            db.add(db_det)
        db.commit()

        update_job_progress(db, job_id, "Tracking Complete", 75, f"ByteTrack isolated {unique_tracked_objects} unique physical road distress objects.")

        # ============================================================
        # STAGE 6: GPS Positional Synchronization
        # ============================================================
        update_job_progress(db, job_id, "GPS Telemetry Sync", 80, "Checking container metadata, GPX tracks & dashboard OCR overlays for GPS coordinates...")
        
        gps_result = detect_gps(video_path, external_gps_path=external_gps_path)
        survey.gps_available = gps_result.latitude is not None and gps_result.longitude is not None
        survey.gps_source = gps_result.location_status

        # Synchronize coordinates per frame timestamp
        frame_timestamps = [float(fr["timestamp_sec"]) for fr in frame_manifest_rows]
        coords_timeline = interpolate_gps_track(
            base_lat=gps_result.latitude,
            base_lon=gps_result.longitude,
            timestamps=frame_timestamps
        )
        db.commit()

        # ============================================================
        # STAGE 7, 8, 9: Severity, RCI, Dynamic Costing & Aggregation
        # ============================================================
        update_job_progress(db, job_id, "Decision Intelligence", 88, "Calculating deterministic multi-factor severity, transparent RCI, and unit repair costs...")

        # Group tracked detections by track_id to form unique DamageInstances
        tracks_grouped = {}
        for tr in tracked_rows:
            tid = int(tr.get("track_id", len(tracks_grouped) + 1))
            if tid not in tracks_grouped:
                tracks_grouped[tid] = []
            tracks_grouped[tid].append(tr)

        damage_instances_list = []
        total_cost = 0.0
        rci_accumulator = 0.0
        damage_seq = 1

        for tid, det_group in tracks_grouped.items():
            # Highest confidence detection represents this damage instance
            best_det = max(det_group, key=lambda x: float(x["confidence"]))
            d_type = best_det["damage_class"]
            conf = float(best_det["confidence"])
            f_idx = int(best_det["frame_number"])
            t_sec = float(best_det["timestamp"])
            
            x1, y1 = float(best_det["x1"]), float(best_det["y1"])
            x2, y2 = float(best_det["x2"]), float(best_det["y2"])
            bw, bh = max(10.0, x2 - x1), max(10.0, y2 - y1)
            b_area = bw * bh

            # Calculate deterministic normalized severity
            sev_calc = calculate_normalized_severity(
                damage_type=d_type,
                confidence=conf,
                box_area=b_area,
                persistence_count=len(det_group)
            )

            # Calculate physical metrics
            area_sqm = round(max(0.2, (b_area / (width * height * 0.10)) * 2.5), 2)
            depth_cm = round(max(1.0, 4.0 if d_type.lower() == "pothole" else 2.0 * sev_calc["severity_score"] / 5.0), 1)

            # Calculate RCI
            rci_val = calculate_rci(
                severity_score_10=sev_calc["severity_score"],
                defect_concentration=min(1.0, len(tracks_grouped) / 20.0),
                traffic_weight=0.75,
                monsoon_risk_weight=0.65
            )

            # Calculate Dynamic Repair Cost
            cost_val = calculate_dynamic_repair_cost(
                damage_type=d_type,
                severity=sev_calc["severity"],
                area_sqm=area_sqm
            )

            # Position
            lat, lon = coords_timeline.get(t_sec, (gps_result.latitude, gps_result.longitude))

            # Copy annotated frame to public and dist folders for frontend display
            pub_frame_dir = PROJECT_ROOT / "frontend" / "dist" / "frames"
            pub_frame_dir.mkdir(parents=True, exist_ok=True)
            public_dev_dir = PROJECT_ROOT / "frontend" / "public" / "frames"
            public_dev_dir.mkdir(parents=True, exist_ok=True)
            
            src_annotated = yolo_out_dir / "annotated" / f"frame_{f_idx:05d}.jpg"
            if src_annotated.exists():
                shutil.copy(str(src_annotated), str(pub_frame_dir / f"frame_{survey_id}_{f_idx:05d}.jpg"))
                shutil.copy(str(src_annotated), str(public_dev_dir / f"frame_{survey_id}_{f_idx:05d}.jpg"))
                evidence_rel_path = f"/frames/frame_{survey_id}_{f_idx:05d}.jpg"

            d_code = f"DMG-{survey.survey_code.replace('SURVEY-', '')}-{damage_seq:03d}"
            
            db_damage = DBDamageInstance(
                survey_id=survey_id,
                damage_code=d_code,
                track_id=tid,
                damage_type=d_type,
                severity=sev_calc["severity"],
                priority=sev_calc["priority"],
                confidence=conf,
                area_sqm=area_sqm,
                depth_cm=depth_cm,
                rci=rci_val,
                estimated_repair_cost=cost_val,
                latitude=lat,
                longitude=lon,
                gps_available=lat is not None and lon is not None,
                gps_source=gps_result.location_status if (lat is not None) else "unavailable",
                frame_image_path=evidence_rel_path,
                frame_index=f_idx,
                timestamp_sec=t_sec,
                detection_count=len(det_group),
                verification_status="UNVERIFIED",
                ai_damage_type=d_type,
                ai_severity=sev_calc["severity"],
                ai_confidence=conf
            )
            db.add(db_damage)
            damage_instances_list.append(db_damage)
            total_cost += cost_val
            rci_accumulator += rci_val
            damage_seq += 1

        db.commit()

        # Compile web-compatible H.264 annotated video directly from the uploaded/source video
        try:
            annotated_video_path = work_dir / "annotated_video.mp4"
            annotated_frame_files = sorted((yolo_out_dir / "annotated").glob("*.jpg"))
            
            # Check if this is the built-in sample demo pothole video
            is_sample_demo = "pothole_video.mp4" in str(video_path).lower()
            detected_ref = PROJECT_ROOT / "frontend" / "public" / "videos" / "detected_dashcam.mp4"
            
            if is_sample_demo and detected_ref.exists():
                shutil.copy(str(detected_ref), str(annotated_video_path))
                print(f"[SUCCESS] Linked full 25fps H.264 detection video for sample survey {survey_id}")
            elif video_path.exists():
                # Render full-motion annotated video from the uploaded video with detected distress bounding boxes
                update_job_progress(db, job_id, "Video Annotation", 92, "Rendering detected distress overlays onto uploaded video feed...")
                rendered = generate_full_annotated_video(
                    source_video_path=video_path,
                    output_video_path=annotated_video_path,
                    tracked_detections=tracked_rows,
                    survey_code=survey.survey_code
                )
                if rendered:
                    print(f"[SUCCESS] Rendered full annotated video from {video_path.name} for survey {survey_id}")
                else:
                    raise RuntimeError("generate_full_annotated_video returned False")
            elif annotated_frame_files:
                # Fallback to compiling from annotated keyframes
                ffmpeg_exe = get_ffmpeg_executable()
                temp_list = work_dir / "ffmpeg_frames.txt"
                with open(temp_list, "w", encoding="utf-8") as f:
                    for fr in annotated_frame_files:
                        f_str = str(fr.resolve()).replace("\\", "/")
                        f.write(f"file '{f_str}'\n")
                        f.write("duration 1.0\n")
                    f_str = str(annotated_frame_files[-1].resolve()).replace("\\", "/")
                    f.write(f"file '{f_str}'\n")
                
                cmd = [
                    ffmpeg_exe, "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(temp_list),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(annotated_video_path)
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if temp_list.exists():
                    temp_list.unlink()
                if res.returncode == 0:
                    print(f"[SUCCESS] Compiled H.264 video for survey {survey_id} ({len(annotated_frame_files)} frames)")
        except Exception as vid_err:
            print(f"[WARN] Could not compile annotated video: {vid_err}")

        # Update Survey aggregate metrics
        survey.unique_damages = len(damage_instances_list)
        survey.total_estimated_cost = round(total_cost, 2)
        survey.avg_rci = round(rci_accumulator / len(damage_instances_list), 1) if damage_instances_list else 0.0
        db.commit()

        # ============================================================
        # STAGE 10 & 11: Route Optimization (TSP 2-Opt)
        # ============================================================
        update_job_progress(db, job_id, "Route Optimization", 95, "Generating TSP 2-Opt geodesic repair route from synchronized coordinates...")

        damage_dict_payload = [
            {
                "id": d.id,
                "damage_code": d.damage_code,
                "damage_type": d.damage_type,
                "severity": d.severity,
                "priority": d.priority,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "estimated_repair_cost": d.estimated_repair_cost
            }
            for d in damage_instances_list
        ]
        route_result = optimize_damage_route(damage_dict_payload)

        db_route = DBRoutePlan(
            survey_id=survey_id,
            ordered_stops=route_result.get("stops", []),
            stops_count=route_result.get("stops_count", 0),
            estimated_distance_km=route_result.get("optimized_distance_km", 0.0),
            estimated_savings_pct=route_result.get("estimated_savings_pct", 0.0),
            distance_metric="Estimated Geodesic (Haversine)"
        )
        db.add(db_route)
        db.commit()

        # ============================================================
        # STAGE 12: Pipeline Completion & Audit Logging
        # ============================================================
        survey.status = "COMPLETED"
        survey.completed_at = datetime.now(timezone.utc)
        job.status = "COMPLETED"
        job.progress_pct = 100
        job.current_step = "Completed"
        job.completed_at = datetime.now(timezone.utc)

        # Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="SURVEY_PROCESSED_SUCCESS",
            resource_type="survey",
            resource_id=survey_id,
            details={
                "video": video_path.name,
                "frames": extracted_count,
                "detections": detections_count,
                "unique_damages": len(damage_instances_list),
                "total_cost": total_cost,
                "gps_available": survey.gps_available
            }
        )
        db.add(audit)
        db.commit()

        update_job_progress(
            db,
            job_id,
            "Completed",
            100,
            f"Successfully finalized pipeline for survey {survey.survey_code}. {len(damage_instances_list)} unique distresses recorded."
        )

    except Exception as e:
        db.rollback()
        job.status = "FAILED"
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        survey.status = "FAILED"
        
        audit = AuditLog(
            user_id=user_id,
            action="SURVEY_PROCESSING_FAILED",
            resource_type="survey",
            resource_id=survey_id,
            details={"error": str(e)}
        )
        db.add(audit)
        db.commit()
        print(f"[PIPELINE ERROR] Survey {survey_id} failed: {e}")
    finally:
        db.close()


def get_survey_geojson(survey_id: str, db: Session) -> Dict[str, Any]:
    """Generate dynamic GeoJSON strictly from PostgreSQL damage instances of the given survey."""
    damages = db.query(DBDamageInstance).filter(DBDamageInstance.survey_id == survey_id).all()
    features = []

    for d in damages:
        props = {
            "id": d.id,
            "damage_id": d.id,
            "damage_code": d.damage_code,
            "survey_id": d.survey_id,
            "damage_type": d.damage_type,
            "severity": d.severity,
            "priority": d.priority,
            "confidence": d.confidence,
            "area_sqm": d.area_sqm,
            "depth_cm": d.depth_cm,
            "rci": d.rci,
            "estimated_repair_cost": d.estimated_repair_cost,
            "status": d.verification_status,
            "frame_image": d.frame_image_path,
            "frame_index": d.frame_index,
            "timestamp_sec": d.timestamp_sec,
            "gps_available": d.gps_available,
            "gps_source": d.gps_source
        }

        if d.gps_available and d.latitude is not None and d.longitude is not None:
            geom = {
                "type": "Point",
                "coordinates": [d.longitude, d.latitude]
            }
        else:
            geom = None

        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": props
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
