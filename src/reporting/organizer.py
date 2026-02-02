import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

REPORT_VERSION = "2.0"

class ReportOrganizer:
    """
    Manages the creation and organization of report directories and files.
    Structure: reports/runs/run_ID/{battles, economy, diplomacy, movements, telemetry, turns}
    """
    def __init__(self, base_reports_dir: str, batch_id: str, run_id: str, universe_name: str = "unknown", logger: Optional[Any] = None):
        self.base_dir = base_reports_dir
        self.run_id = run_id
        # Batch ID and Universe Name are deprecated for structure but kept for metadata
        self.batch_id = batch_id
        self.universe_name = universe_name
        self.logger = logger
        
        # New Flat Structure: reports/runs/run_ID
        self.runs_dir = os.path.join(self.base_dir, "runs")
        self.run_path = os.path.join(self.runs_dir, self.run_id)
        
        # Top-Level Categories (formerly inside turns)
        self.categories = ["battles", "economy", "diplomacy", "movements", "factions", "designs"]
        self.timeline_path = os.path.join(self.run_path, "timeline.md")
        self.integrity_errors = []
        
    def initialize_run(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Creates run directory and category subdirectories.
        Writes consolidated run manifest.
        """
        if not os.path.exists(self.run_path):
            os.makedirs(self.run_path, exist_ok=True)
            
        # Create Category Directories at Run Level (Phase 1 Goal)
        for cat in self.categories:
            cat_path = os.path.join(self.run_path, cat)
            os.makedirs(cat_path, exist_ok=True)
            
        # Create Telemetry Directory
        telemetry_path = os.path.join(self.run_path, "telemetry")
        os.makedirs(telemetry_path, exist_ok=True)
        
        # Create Turns Directory
        turns_path = os.path.join(self.run_path, "turns")
        os.makedirs(turns_path, exist_ok=True)
            
        # Write Run Manifest (Consolidated)
        run_manifest = os.path.join(self.run_path, "run.json")
        self.write_manifest(run_manifest, {
            "run_id": self.run_id,
            "universe": self.universe_name,
            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metadata": metadata or {},
            "status": "running"
        })

        # Initialize Master Timeline
        with open(self.timeline_path, "w", encoding="utf-8") as f:
            f.write(f"# Master Simulation History: {self.run_id}\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| Turn | Event Category | Description |\n")
            f.write("| :--- | :--- | :--- |\n")

    def prepare_turn_folder(self, turn: int, factions: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Creates turn summary directory and writes summary.json.
        
        Args:
            turn: Turn number.
            factions: List of faction names (legacy/unused).
            data: Dictionary containing turn statistics (economy, factions, etc.).
        """
        turn_id = f"turn_{turn:03d}"
        turn_path = os.path.join(self.run_path, "turns", turn_id)
        
        if not os.path.exists(turn_path):
            os.makedirs(turn_path, exist_ok=True)
                
        # Turn Manifest / Summary
        summary_data = {
            "turn": turn,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "stats": data or {}
        }
        
        self.write_manifest(os.path.join(turn_path, "summary.json"), summary_data)
            
        return turn_path

    def get_turn_path(self, turn: int, category: str, faction: Optional[str] = None) -> str:
        """
        Deprecation Warning: Categories are now at Run level.
        Returns the path to the Category directory (e.g., runs/run_ID/battles).
        """
        # Mapping old logic to new structure
        if category in self.categories:
             cat_path = os.path.join(self.run_path, category)
             return cat_path
             
             # Note: Factions are now flattened too. 
             # reports/runs/run_ID/factions/FactionName.json
             # If caller expects a directory, we return the factions root.
             
        # Fallback for unexpected categories
        return os.path.join(self.run_path, category)

    def write_manifest(self, path: str, data: Dict[str, Any]):
        """
        Writes a manifest.json file with standard metadata.
        """
        # Inject standard metadata
        data["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data["report_version"] = REPORT_VERSION
        
        if "universe" not in data:
            data["universe"] = self.universe_name

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error writing manifest at {path}: {e}")
            else:
                print(f"Error writing manifest at {path}: {e}")

    def finalize_manifest(self, path: str, data_schema: Optional[Dict[str, List[str]]] = None):
        """
        Adds file statistics (count, size, contents) to an existing manifest.
        """
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            folder_path = os.path.dirname(path)
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f != "manifest.json"]
            
            total_size = sum(os.path.getsize(os.path.join(folder_path, f)) for f in files)
            
            data["file_count"] = len(files)
            data["total_size_bytes"] = total_size
            data["contains"] = files
            if data_schema:
                data["data_schema"] = data_schema

            # Rewrite with new info
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finalizing manifest at {path}: {e}")

    def log_to_master_timeline(self, turn: int, category: str, description: str):
        """
        Appends a major event to the master history file.
        """
        try:
            with open(self.timeline_path, "a", encoding="utf-8") as f:
                f.write(f"| {turn} | **[{category.upper()}]** | {description} |\n")
        except Exception as e:
            print(f"Error writing to timeline: {e}")

    def validate_turn_reports(self, turn: int) -> tuple[bool, list[str]]:
        """
        Validates that all expected reports for a turn exist in the flat structure.
        Returns (is_valid, errors).
        """
        turn_id = f"turn_{turn:03d}"
        # Correct path to turns directory
        turn_path = os.path.join(self.run_path, "turns", turn_id)
        errors = []

        # 1. Check Turn Summary
        if not os.path.exists(turn_path):
            msg = f"Turn folder missing: turns/{turn_id}"
            errors.append(msg)
            self.integrity_errors.append(msg)
            return False, errors
            
        summary_path = os.path.join(turn_path, "summary.json")
        if not os.path.exists(summary_path):
             errors.append(f"Missing summary.json in turns/{turn_id}")

        # 2. Check Flat Categories (Factions, etc.)
        # Factions: Check if each faction has a report for this turn
        factions_dir = os.path.join(self.run_path, "factions")
        if os.path.exists(factions_dir):
            # We need to know which factions exist to validate completely, but we can check if directory is empty
            # For now, let's assume if the dir exists, we check for at least some files if turn > 0
            pass 
            # Ideally we would check `Faction_turn_{turn:03d}.json` for each faction, 
            # but we don't have the faction list here easily without passing it in.
            # We'll skip strict faction-by-faction validation here to avoid dependency injection issues,
            # or rely on the caller to handle that.
            
        # 3. Check Manifests (Global) - Optional, mainly for debugging
        
        if errors:
            self.integrity_errors.extend(errors)
            return False, errors

        return True, []

    def finalize_run(self, summary: Dict[str, Any]):
        """
        Updates run manifest with completion summary.
        """
        run_manifest = os.path.join(self.run_path, "manifest.json")
        if os.path.exists(run_manifest):
            try:
                with open(run_manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["finished_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                data["summary"] = summary
                
                # Add Alert Summary
                # Add Integrity Report
                data["integrity"] = {
                    "is_valid": len(self.integrity_errors) == 0,
                    "error_count": len(self.integrity_errors),
                    "errors": self.integrity_errors[:50] # Cap at 50 for size
                }
                
                with open(run_manifest, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error finalizing run manifest: {e}")

    def generate_csv_reports(self, telemetry_file: str) -> None:
        """
        [REPORTING] Generates CSV reports for Economy and Diplomacy from telemetry.
        Populates the previously empty 'economy' and 'diplomacy' folders.
        """
        if not os.path.exists(telemetry_file): return
        
        print(f"[REPORT] Generating CSV reports from {telemetry_file}...")
        
        econ_rows = []
        diplo_rows = []
        
        try:
            with open(telemetry_file, 'r') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        ev = json.loads(line)
                        cat = ev.get("category")
                        
                        if cat == "economy":
                            # Flat structure for CSV
                            row = {
                                "turn": ev.get("turn"),
                                "timestamp": ev.get("timestamp"),
                                "faction": ev.get("faction"),
                                "event_type": ev.get("event_type"),
                                "data": json.dumps(ev.get("data", {})) 
                            }
                            econ_rows.append(row)
                            
                        elif cat == "diplomacy":
                            row = {
                                "turn": ev.get("turn"),
                                "timestamp": ev.get("timestamp"),
                                "faction": ev.get("faction"),
                                "event_type": ev.get("event_type"),
                                "data": json.dumps(ev.get("data", {}))
                            }
                            diplo_rows.append(row)
                            
                    except json.JSONDecodeError:
                        continue
                        
            # Write Economy CSV
            if econ_rows:
                import csv
                econ_path = os.path.join(self.run_path, "economy", "economy_report.csv")
                with open(econ_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["turn", "timestamp", "faction", "event_type", "data"])
                    writer.writeheader()
                    writer.writerows(econ_rows)
                print(f"[REPORT] Created {econ_path}")

            # Write Diplomacy CSV
            if diplo_rows:
                import csv
                diplo_path = os.path.join(self.run_path, "diplomacy", "diplomacy_report.csv")
                with open(diplo_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["turn", "timestamp", "faction", "event_type", "data"])
                    writer.writeheader()
                    writer.writerows(diplo_rows)
                print(f"[REPORT] Created {diplo_path}")
                
        except Exception as e:
            print(f"[REPORT] Failed to generate CSVs: {e}")
