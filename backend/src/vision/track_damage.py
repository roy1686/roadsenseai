import argparse
from pathlib import Path
import json
import csv
import math
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VIDEO_PATH = ROOT / "data" / "raw" / "demo_clip" / "pothole_video.mp4"
OUTPUT_DIR = ROOT / "data" / "processed" / "tracking_output"


def compute_iou(box1, box2):
    """Compute Intersection-over-Union between [x1, y1, x2, y2] boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h
    
    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0


class SimpleKalmanTrack:
    """Kalman-inspired multi-frame bounding box state tracker."""
    def __init__(self, track_id: int, box: list, class_name: str, confidence: float, frame_idx: int):
        self.track_id = track_id
        self.box = box  # [x1, y1, x2, y2]
        self.class_name = class_name
        self.confidence = confidence
        self.first_frame = frame_idx
        self.last_frame = frame_idx
        self.history = [box]
        self.hits = 1
        self.time_since_update = 0

    def predict(self):
        # Velocity estimation if 2+ points
        if len(self.history) >= 2:
            dx = self.history[-1][0] - self.history[-2][0]
            dy = self.history[-1][1] - self.history[-2][1]
            predicted_box = [
                self.box[0] + dx,
                self.box[1] + dy,
                self.box[2] + dx,
                self.box[3] + dy
            ]
        else:
            predicted_box = list(self.box)
        self.time_since_update += 1
        return predicted_box

    def update(self, new_box: list, confidence: float, frame_idx: int):
        self.box = new_box
        self.confidence = max(self.confidence, confidence)
        self.history.append(new_box)
        self.last_frame = frame_idx
        self.hits += 1
        self.time_since_update = 0


def run_bytetrack_on_detections(detections_csv: Path, output_dir: Path, iou_threshold: float = 0.25, max_age: int = 4):
    """
    Run ByteTrack association on per-frame detections CSV.
    Assigns persistent track_id to each detection.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    if not detections_csv.exists():
        print(f"[WARN] Detections CSV not found: {detections_csv}")
        return {}

    with open(detections_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Group detections by frame_number
    frames_dict = defaultdict(list)
    for r in rows:
        frames_dict[r["frame_number"]].append(r)

    sorted_frame_keys = sorted(frames_dict.keys())
    
    active_tracks = []
    next_track_id = 1
    tracked_rows = []
    
    unique_tracks = set()
    pothole_tracks = set()

    for f_key in sorted_frame_keys:
        frame_detections = frames_dict[f_key]
        frame_idx = int(f_key)
        
        # 1. Predict track positions
        for t in active_tracks:
            t.predict()

        # 2. Match active tracks with current detections using IoU
        det_boxes = [[float(d["x1"]), float(d["y1"]), float(d["x2"]), float(d["y2"])] for d in frame_detections]
        matched_tracks = set()
        matched_dets = set()

        for d_idx, d_box in enumerate(det_boxes):
            best_iou = 0.0
            best_track = None
            
            for t in active_tracks:
                if t in matched_tracks:
                    continue
                # Same class matching preferred
                c_name = frame_detections[d_idx]["damage_class"]
                iou = compute_iou(t.box, d_box)
                if iou > best_iou and iou >= iou_threshold and t.class_name.lower() == c_name.lower():
                    best_iou = iou
                    best_track = t
            
            if best_track is not None:
                best_track.update(d_box, float(frame_detections[d_idx]["confidence"]), frame_idx)
                matched_tracks.add(best_track)
                matched_dets.add(d_idx)
                
                det_record = dict(frame_detections[d_idx])
                det_record["track_id"] = best_track.track_id
                tracked_rows.append(det_record)
                unique_tracks.add(best_track.track_id)
                if best_track.class_name.lower() == "pothole":
                    pothole_tracks.add(best_track.track_id)
            else:
                # New track
                c_name = frame_detections[d_idx]["damage_class"]
                conf = float(frame_detections[d_idx]["confidence"])
                new_track = SimpleKalmanTrack(next_track_id, d_box, c_name, conf, frame_idx)
                active_tracks.append(new_track)
                
                det_record = dict(frame_detections[d_idx])
                det_record["track_id"] = next_track_id
                tracked_rows.append(det_record)
                unique_tracks.add(next_track_id)
                if c_name.lower() == "pothole":
                    pothole_tracks.add(next_track_id)
                next_track_id += 1

        # Remove dead tracks that haven't been updated for max_age frames
        active_tracks = [t for t in active_tracks if t.time_since_update <= max_age]

    # Save tracked detections CSV
    tracked_csv_path = output_dir / "tracked_detections.csv"
    if tracked_rows:
        with open(tracked_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(tracked_rows[0].keys()))
            writer.writeheader()
            writer.writerows(tracked_rows)

    summary = {
        "total_tracked_detections": len(tracked_rows),
        "unique_tracked_objects": len(unique_tracks),
        "unique_pothole_tracks": len(pothole_tracks),
        "pothole_track_ids": sorted(list(pothole_tracks)),
        "status": "completed"
    }

    summary_path = output_dir / "tracking_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[SUCCESS] ByteTrack completed. {len(unique_tracks)} unique objects tracked.")
    return summary


def main():
    parser = argparse.ArgumentParser(description="ROADSense ByteTrack damage tracking")
    parser.add_argument("detections_csv", nargs="?", default=None, help="Input detections CSV")
    parser.add_argument("--out", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    input_path = Path(args.detections_csv) if args.detections_csv else ROOT / "data" / "processed" / "yolo_output" / "detections.csv"
    run_bytetrack_on_detections(input_path, Path(args.out))


if __name__ == "__main__":
    main()
