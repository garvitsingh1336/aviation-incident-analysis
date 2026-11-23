"""Build 1000 real aviation incident reports from authentic NASA ASRS / NTSB reports."""
import json
import csv
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
INPUT_JSONL = DATA_DIR / "sample_asrs_8mb.jsonl"
OUTPUT_CSV = DATA_DIR / "reports.csv"
BACKUP_CSV = DATA_DIR / "reports_synthetic_backup.csv"
TARGET_COUNT = 1000

def parse_date(date_str: str) -> str:
    """Coerce YYYYMM to YYYY-MM-15 or return as is."""
    if not date_str:
        return "2018-06-01"
    s = str(date_str).strip()
    if len(s) == 6 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-15"
    if len(s) >= 8 and s[:8].isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s

def clean_str(val: str, default: str = "") -> str:
    if val is None:
        return default
    cleaned = re.sub(r'\s+', ' ', str(val)).strip()
    return cleaned if cleaned else default

def determine_severity(anomaly: str, result: str) -> tuple[str, str]:
    """Map anomaly/result to severity and injury_level."""
    text = f"{anomaly} {result}".lower()
    if "accident" in text or "damage" in text or "injury" in text or "crash" in text:
        return "Accident", "Minor"
    if "critical" in text or "emergency" in text or "deviation" in text or "loss of control" in text:
        return "Serious Incident", "None"
    return "Incident", "None"

def build_real_dataset():
    if OUTPUT_CSV.exists() and not BACKUP_CSV.exists():
        OUTPUT_CSV.rename(BACKUP_CSV)
        print(f"Backed up original reports to: {BACKUP_CSV.name}")

    records = []
    skipped = 0

    with open(INPUT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            acn = clean_str(row.get("acn_num_ACN"))
            date_raw = clean_str(row.get("Time_Date"))
            event_text = clean_str(row.get("Report 1.2_Synopsis"))
            narrative = clean_str(row.get("Report 1_Narrative"))
            aircraft_type = clean_str(row.get("Aircraft 1.2_Make Model Name"), default="Commercial Aircraft")
            operator = clean_str(row.get("Aircraft 1.1_Aircraft Operator"), default="Air Carrier")
            flight_phase = clean_str(row.get("Aircraft 1.9_Flight Phase"), default="Cruise").lower()
            contributing_factors = clean_str(row.get("Assessments_Contributing Factors / Situations"))
            human_factors = clean_str(row.get("Person 1.7_Human Factors"))
            anomaly = clean_str(row.get("Events_Anomaly"))
            result = clean_str(row.get("Events.5_Result"))

            # Airport & location
            locale = clean_str(row.get("Place_Locale Reference"))
            state = clean_str(row.get("Place.1_State Reference"))
            airport = locale if locale else "Unknown"
            location = f"{locale}, {state}".strip(", ") if locale or state else "United States"

            # Must have a narrative
            if not narrative or len(narrative) < 60:
                skipped += 1
                continue

            if not acn:
                acn = f"ASRS-{1000000 + len(records)}"

            # If synopsis is missing, use first 200 chars of narrative
            if not event_text or len(event_text) < 20:
                event_text = narrative[:250] + "..."

            # Combine true contributing factors
            factor_list = []
            if contributing_factors:
                for f_item in contributing_factors.split(";"):
                    f_item = f_item.strip()
                    if f_item and f_item not in factor_list:
                        factor_list.append(f_item)
            if human_factors:
                for h_item in human_factors.split(";"):
                    h_item = h_item.strip()
                    if h_item and h_item not in factor_list:
                        factor_list.append(h_item)
            true_factors = "; ".join(factor_list)

            severity, injury_level = determine_severity(anomaly, result)

            records.append({
                "report_id": f"ACN-{acn}",
                "date": parse_date(date_raw),
                "narrative": narrative,
                "event_text": event_text,
                "aircraft_type": aircraft_type,
                "airport": airport,
                "location": location,
                "operator": operator,
                "phase_of_flight": flight_phase,
                "severity": severity,
                "injury_level": injury_level,
                "true_factors": true_factors
            })

            if len(records) >= TARGET_COUNT:
                break

    print(f"Extracted {len(records)} authentic reports (skipped {skipped} low-text items).")

    fieldnames = [
        "report_id", "date", "narrative", "event_text", "aircraft_type",
        "airport", "location", "operator", "phase_of_flight",
        "severity", "injury_level", "true_factors"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[SUCCESS] Saved {len(records)} real incident reports to: {OUTPUT_CSV}")

if __name__ == "__main__":
    build_real_dataset()
