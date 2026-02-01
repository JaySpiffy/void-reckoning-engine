from src.reporting.generators.base import BaseReportGenerator
from typing import Dict, Any

class HTMLReportGenerator(BaseReportGenerator):
    def generate(self, summary: Dict[str, Any], output_path: str):
        self._ensure_dir(output_path)
        f_name = summary["faction"]
        turn = summary["turn"]
        eff = summary['economy']['efficiency_pct']
        eff_class = "good" if eff >= 100 else "bad"
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{f_name} - Turn {turn}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #e0e0e0; margin: 20px; }}
        .header {{ border-bottom: 2px solid #444; padding-bottom: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .card {{ background: #2a2a2a; padding: 15px; border-radius: 8px; border-left: 4px solid #555; }}
        .card h3 {{ margin-top: 0; color: #aaa; font-size: 0.9em; }}
        .value {{ font-size: 1.4em; font-weight: bold; }}
        .good {{ color: #4caf50; }}
        .bad {{ color: #f44336; }}
        .event-list {{ list-style: none; padding: 0; }}
        .event-item {{ background: #222; padding: 8px; margin-bottom: 5px; border-radius: 4px; border-left: 2px solid #777; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{f_name} <span style="font-size: 0.5em; color: #888;">TURN {turn}</span></h1>
        <div style="background: #333; padding: 5px; border-radius: 4px; display: inline-block; margin-top: 10px;">
            <span style="color: #888; font-size: 0.8em;">UNIVERSE:</span> 
            <span style="color: #4caf50; font-weight: bold;">{summary.get('universe', 'UNKNOWN')}</span>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="card" style="border-left-color: #2196f3;">
            <h3>REQUISITION</h3>
            <div class="value">{summary['deltas']['requisition']:+,.0f}</div>
            <div style="font-size: 0.8em;">{summary['economy']['income']} in / {summary['economy']['expense']} out</div>
        </div>
        <div class="card" style="border-left-color: #4caf50;">
            <h3>EFFICIENCY</h3>
            <div class="value {eff_class}">{eff}%</div>
        </div>
        <div class="card" style="border-left-color: #ff9800;">
            <h3>MILITARY POWER</h3>
            <div class="value">{summary['military']['military_power_score']:,}</div>
            <div style="font-size: 0.8em; color: #888;">{summary['deltas']['military_power']:+d} this turn</div>
        </div>
        <div class="card" style="border-left-color: #9c27b0;">
            <h3>PLANETS</h3>
            <div class="value">{summary['territory']['total_controlled']}</div>
            <div style="font-size: 0.8em; color: #888;">{summary['deltas']['planets_count']:+d} this turn</div>
        </div>
    </div>

    <h2>📜 Recent Events</h2>
    <ul class="event-list">
        {"".join([f'<li class="event-item"><b>{e["category"].upper()}</b>: {e["message"]}</li>' for e in summary['events']]) or "<li>No major events.</li>"}
    </ul>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
