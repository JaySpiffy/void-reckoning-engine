from src.reporting.generators.base import BaseReportGenerator
from typing import Dict, Any

class MarkdownReportGenerator(BaseReportGenerator):
    def generate(self, summary: Dict[str, Any], output_path: str):
        self._ensure_dir(output_path)
        f_name = summary["faction"]
        eff_color = "🟢" if summary['economy']['efficiency_pct'] >= 100 else "🔴"
        
        lines = [
            f"# Faction Report: {f_name}",
            f"**Turn**: {summary['turn']}",
            "",
            "## 💰 Economy Summary",
            f"- **Net Requisition**: {summary['deltas']['requisition']:+0.0f} ({summary['economy']['income']} income / {summary['economy']['expense']} expense)",
            f"- **Efficiency**: {eff_color} {summary['economy']['efficiency_pct']}%",
            f"- **Construction Spending**: {summary['economy']['construction_spend']} Req",
            f"- **Constructions Completed**: {summary['construction']['completed']}",
            f"- **Recruitment Spending**: {summary['economy']['recruitment_spend']} Req",
            "",
            "## 🎖️ Military & Territory",
            f"- **Planets**: {summary['territory']['total_controlled']} ({summary['deltas']['planets_count']:+0.0f})",
        ]
        
        if summary['territory']['captured']:
            lines.append(f"  - *Captured*: {', '.join(summary['territory']['captured'])}")
        if summary['territory']['lost']:
            lines.append(f"  - *Lost*: {', '.join(summary['territory']['lost'])}")
            
        lines.extend([
            f"- **Fleets**: {summary['military']['total_fleets']} ({summary['deltas']['fleets_count']:+0.0f})",
            f"- **Military Power**: {summary['military']['military_power_score']} ({summary['deltas']['military_power']:+0.0f})",
            f"- **Battles**: {summary['military']['battles_fought']} ({summary['military']['battles_won']} won)",
            f"- **Units Recruited**: {summary['military']['units_recruited']}",
            f"- **Units Lost**: {summary['military']['units_lost']}",
            f"- **Tech Count**: {summary['technology']['unlocked_count']} ({summary['deltas']['techs_unlocked']:+0.0f})",
            f"- **Diplomacy Actions**: {summary['diplomacy']['actions']}",
            "",
            "## 📜 Event Timeline",
        ])
        
        if not summary['events']:
            lines.append("*No major events recorded this turn.*")
        else:
            for event in summary['events']:
                lines.append(f"- **{event['category'].upper()}**: {event['message']}")
                
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
