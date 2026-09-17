from pathlib import Path
import argparse
import csv
import json
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_INPUT_CSV = (
    PROJECT_ROOT / "data" / "processed" / "tracking_output" / "tracked_detections.csv"
)
DEFAULT_OUTPUT_CSV = (
    PROJECT_ROOT / "data" / "processed" / "m1_output" / "prioritized_detections.csv"
)

CLASS_WEIGHTS = {
    "pothole": 1.0,
    "alligator crack": 0.85,
    "transverse crack": 0.60,
    "longitudinal crack": 0.60,
    "other corruption": 0.50
}

UNIT_REPAIR_RATES = {
    "pothole": 12000.0,
    "alligator crack": 8500.0,
    "transverse crack": 4200.0,
    "longitudinal crack": 4200.0,
    "other corruption": 5000.0
}


def calculate_normalized_severity(
    damage_type: str,
    confidence: float,
    box_area: float = 5000.0,
    frame_area: float = 1280.0 * 720.0,
    persistence_count: int = 1
) -> dict:
    """
    Deterministic normalized severity decision model:
      Score = 0.35 * AreaRatio + 0.35 * ClassWeight + 0.15 * Persistence + 0.15 * Confidence
    All components normalized to [0, 1].
    """
    dtype = damage_type.lower().strip()
    class_w = CLASS_WEIGHTS.get(dtype, 0.50)
    
    # Area ratio normalized against standard 10% pavement frame reference
    ref_area = frame_area * 0.10
    area_ratio = min(1.0, max(0.05, box_area / ref_area if ref_area > 0 else 0.1))
    
    # Persistence normalized up to 4 frames
    persistence_norm = min(1.0, max(0.25, persistence_count / 4.0))
    
    # Confidence in [0, 1]
    conf_norm = min(1.0, max(0.0, float(confidence)))
    
    score = (
        0.35 * area_ratio +
        0.35 * class_w +
        0.15 * persistence_norm +
        0.15 * conf_norm
    )
    score = round(min(1.0, max(0.0, score)), 4)
    
    if score >= 0.65:
        severity = "Critical"
        priority = 1
    elif score >= 0.48:
        severity = "High"
        priority = 2
    elif score >= 0.32:
        severity = "Moderate"
        priority = 3
    else:
        severity = "Low"
        priority = 4

    return {
        "severity": severity,
        "priority": priority,
        "severity_score": round(score * 10.0, 1),
        "components": {
            "area_ratio": round(area_ratio, 3),
            "class_weight": round(class_w, 3),
            "persistence_norm": round(persistence_norm, 3),
            "confidence_norm": round(conf_norm, 3)
        }
    }


def calculate_rci(
    severity_score_10: float,
    defect_concentration: float = 0.5,
    traffic_weight: float = 0.75,
    monsoon_risk_weight: float = 0.60
) -> float:
    """
    Road Criticality Index (0 - 100):
      RCI = 100 * (0.40 * Severity + 0.25 * Concentration + 0.20 * Traffic + 0.15 * Monsoon)
    """
    norm_sev = min(1.0, max(0.0, severity_score_10 / 10.0))
    rci_raw = (
        0.40 * norm_sev +
        0.25 * defect_concentration +
        0.20 * traffic_weight +
        0.15 * monsoon_risk_weight
    )
    return round(min(100.0, max(10.0, rci_raw * 100.0)), 1)


def calculate_dynamic_repair_cost(damage_type: str, severity: str, area_sqm: float = 1.5) -> float:
    dtype = damage_type.lower().strip()
    base_rate = UNIT_REPAIR_RATES.get(dtype, 5000.0)
    multiplier = {
        "critical": 1.5,
        "high": 1.25,
        "moderate": 1.0,
        "low": 0.75
    }.get(severity.lower(), 1.0)
    return round(base_rate * area_sqm * multiplier, 2)


def process_detections_csv(input_csv: Path, output_csv: Path) -> bool:
    if not input_csv.exists():
        print(f"[ERROR] Input file not found: {input_csv}")
        return False

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(input_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Count occurrences per track to compute persistence
    track_counts = defaultdict(int)
    for r in rows:
        tid = r.get("track_id", r.get("damage_class", "0"))
        track_counts[tid] += 1

    results = []
    for idx, r in enumerate(rows):
        x1, y1 = float(r.get("x1", 0)), float(r.get("y1", 0))
        x2, y2 = float(r.get("x2", 100)), float(r.get("y2", 100))
        bw, bh = max(10.0, x2 - x1), max(10.0, y2 - y1)
        b_area = bw * bh
        
        tid = r.get("track_id", r.get("damage_class", "0"))
        p_count = track_counts[tid]
        
        sev_data = calculate_normalized_severity(
            damage_type=r.get("damage_class", r.get("damage_type", "pothole")),
            confidence=float(r.get("confidence", 0.5)),
            box_area=b_area,
            persistence_count=p_count
        )
        
        r["detection_id"] = f"d-{idx+1:05d}"
        r["severity"] = sev_data["severity"]
        r["priority"] = sev_data["priority"]
        r["severity_score"] = sev_data["severity_score"]
        results.append(r)

    if results:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    print(f"[SUCCESS] Severity and priority calculation completed for {len(results)} records.")
    return True


def main():
    parser = argparse.ArgumentParser(description="ROADSense severity & priority processor")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_CSV), help="Input CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_CSV), help="Output prioritized CSV")
    args = parser.parse_args()
    process_detections_csv(Path(args.input).resolve(), Path(args.output).resolve())


if __name__ == "__main__":
    main()
