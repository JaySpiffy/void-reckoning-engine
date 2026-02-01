
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ImportReporter:
    """
    Generates comprehensive reports for the import process.
    Supports JSON (data), Markdown (human-readable), and Mermaid (visual) formats.
    """
    
    def __init__(self, universe_name: str, output_dir: str):
        self.universe_name = universe_name
        self.output_dir = output_dir
        self.start_time = time.time()
        self.data = {
            "universe_name": universe_name,
            "import_date": datetime.now().isoformat(),
            "engine": "unknown",
            "stages": {},
            "entities": {
                "units": 0, "buildings": 0, "technologies": 0, 
                "factions": 0, "weapons": 0, "abilities": 0
            },
            "validation": {
                "critical": [], "warning": [], "info": []
            },
            "physics_profile": {}
        }
        
    def set_engine(self, engine: str):
        self.data["engine"] = engine
        
    def record_stage_time(self, stage: str, duration: float, meta: Dict = None):
        """Records timing and metadata for a stage."""
        self.data["stages"][stage] = {
            "time": duration,
            "meta": meta or {}
        }
        
    def add_validation_issues(self, issues: List[Any]): # List[ValidationResult]
        """Aggregates validation issues."""
        for issue in issues:
            # issue is ValidationResult object
            self.data["validation"][issue.severity].append({
                "category": issue.category,
                "entity": issue.entity_id,
                "message": issue.message,
                "file": issue.file_path
            })
            
    def set_entity_counts(self, counts: Dict[str, int]):
        """Updates entity counts."""
        self.data["entities"].update(counts)

    def set_physics_profile(self, profile: Dict):
        self.data["physics_profile"] = profile

    def generate_reports(self):
        """Writes all report formats to disk."""
        self.data["total_time_seconds"] = time.time() - self.start_time
        
        # Ensure output dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 1. JSON Report
        json_path = os.path.join(self.output_dir, "import_report.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
            
        # 2. Markdown Report
        md_content = self._generate_markdown()
        md_path = os.path.join(self.output_dir, "import_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return [json_path, md_path]

    def _generate_markdown(self) -> str:
        d = self.data
        val = d["validation"]
        
        md = f"""# Import Report: {d['universe_name']}

**Date:** {d['import_date']}  
**Engine:** {d['engine']}  
**Total Time:** {d['total_time_seconds']:.2f} seconds

## Summary
- ✅ {d['entities']['units']} units imported
- ✅ {d['entities']['buildings']} buildings imported
- ✅ {d['entities']['technologies']} technologies imported
- ✅ {d['entities']['factions']} factions configured
- ⚠️ {len(val['warning'])} validation warnings
- ❌ {len(val['critical'])} critical errors

## Physics Calibration
"""
        if d.get("physics_profile"):
            p = d["physics_profile"]
            md += f"- **Archetype:** {p.get('archetype', 'N/A')}\n"
            md += f"- **MAPE:** {p.get('mape', 0)*100:.1f}% ({p.get('status', 'Unknown')})\n"
        else:
            md += "- *Skipped or Failed*\n"
            
        md += "\n## Validation Issues\n"
        
        if val['critical']:
            md += f"### Critical ({len(val['critical'])})\n"
            for v in val['critical'][:10]:
                md += f"- **{v['entity']}**: {v['message']}\n"
            if len(val['critical']) > 10: md += f"- ...and {len(val['critical'])-10} more\n"
            
        if val['warning']:
            md += f"### Warnings ({len(val['warning'])})\n"
            for v in val['warning'][:10]:
                md += f"- `{v['entity']}`: {v['message']}\n"
                 
        md += "\n## Stage Timings\n| Stage | Time | Details |\n|---|---|---|\n"
        for stage, info in d["stages"].items():
            meta_str = ", ".join([f"{k}:{v}" for k,v in info["meta"].items()])
            md += f"| {stage} | {info['time']:.2f}s | {meta_str} |\n"
            
        return md
