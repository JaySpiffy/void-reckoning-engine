import pandas as pd
import os
import json
from datetime import datetime
from io import BytesIO
import logging

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class DataExporter:
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.logger = logging.getLogger("DataExporter")

    def export_to_csv(self, universe: str, run_id: str, factions: list, turn_range: tuple, batch_id: str = None, metrics: list = None) -> BytesIO:
        """Exports combined faction data to CSV."""
        df = self._collect_combined_data(universe, run_id, factions, turn_range, batch_id, metrics)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output

    def export_to_excel(self, universe: str, run_id: str, factions: list, turn_range: tuple, batch_id: str = None, metrics: list = None) -> BytesIO:
        """Exports faction data to Excel with multiple sheets."""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Summary Sheet
            summary_data = []
            for f in factions:
                net_profit = self.data_provider.get_faction_net_profit_history(universe, run_id, f, batch_id, turn_range)
                cer = self.data_provider.get_faction_combat_effectiveness(universe, run_id, f, batch_id, turn_range)
                
                avg_profit = sum(net_profit.get('net_profit', [0])) / max(1, len(net_profit.get('net_profit', [])))
                avg_cer = sum(cer.get('cer', [0])) / max(1, len(cer.get('cer', [])))
                
                summary_data.append({
                    "Faction": f,
                    "Avg Net Profit": round(avg_profit, 2),
                    "Avg CER": round(avg_cer, 2),
                    "Data Points": len(net_profit.get('turns', []))
                })
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            # 2. Detailed Data Sheet
            df = self._collect_combined_data(universe, run_id, factions, turn_range, batch_id, metrics)
            df.to_excel(writer, sheet_name="Detailed Data", index=False)

            # 3. ROI Data Sheet
            roi_data = self.data_provider.get_resource_roi_data(universe, run_id, batch_id, turn_range)
            if roi_data:
                pd.DataFrame(roi_data).to_excel(writer, sheet_name="Resource ROI", index=False)

        output.seek(0)
        return output

    def export_to_pdf(self, universe: str, run_id: str, factions: list, turn_range: tuple, batch_id: str = None) -> BytesIO:
        """Exports a summary dashboard report to PDF."""
        if not REPORTLAB_AVAILABLE:
            # Fallback to a simple text-based PDF or error
            self.logger.warning("ReportLab not available. PDF export might be degraded.")
            return self.export_to_csv(universe, run_id, factions, turn_range, batch_id)

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(f"Campaign Report: {run_id}", styles['Title']))
        elements.append(Paragraph(f"Universe: {universe} | Turn Range: {turn_range[0]} - {turn_range[1]}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Faction Summaries
        elements.append(Paragraph("Faction Performance Summary", styles['Heading2']))
        summary_data = [["Faction", "Avg Profit", "Avg CER", "Turns Active"]]
        for f in factions:
            net_profit = self.data_provider.get_faction_net_profit_history(universe, run_id, f, batch_id, turn_range)
            cer = self.data_provider.get_faction_combat_effectiveness(universe, run_id, f, batch_id, turn_range)
            
            avg_profit = sum(net_profit.get('net_profit', [0])) / max(1, len(net_profit.get('net_profit', [])))
            avg_cer = sum(cer.get('cer', [0])) / max(1, len(cer.get('cer', [])))
            
            summary_data.append([
                f, 
                f"{avg_profit:,.2f}", 
                f"{avg_cer:.2f}",
                str(len(net_profit.get('turns', [])))
            ])

        t = Table(summary_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))

        # ROI Top Items
        roi_data = self.data_provider.get_resource_roi_data(universe, run_id, batch_id, turn_range)
        if roi_data:
            elements.append(Paragraph("Top Resource ROI Conquests", styles['Heading2']))
            sorted_roi = sorted(roi_data, key=lambda x: x['payback_turns'])[:10]
            roi_table_data = [["Planet", "Faction", "Cost", "Payback Turns"]]
            for r in sorted_roi:
                roi_table_data.append([r['planet'], r['faction'], f"{r['cost']:,}", str(r['payback_turns'])])
            
            rt = Table(roi_table_data)
            rt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkcyan),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(rt)

        doc.build(elements)
        output.seek(0)
        return output

    def _collect_combined_data(self, universe: str, run_id: str, factions: list, turn_range: tuple, batch_id: str = None, metrics: list = None) -> pd.DataFrame:
        """Helper to collect and join faction data into a single DataFrame."""
        all_frames = []
        
        # Column mapping from dashboard metric keys to CSV columns
        # If metrics is None, we include everything.
        metric_map = {
            'economy': ['gross_income', 'upkeep', 'net_profit', 'stockpile', 'velocity'],
            'battles': ['cer', 'attrition'],
            'units': ['power'],
            'construction': ['construction_efficiency', 'idle_slots'],
            'research': ['tech_count'],
        }

        for f in factions:
            # 1. Get Economic Data
            net_profit = self.data_provider.get_faction_net_profit_history(universe, run_id, f, batch_id, turn_range)
            econ_df = pd.DataFrame({
                "turn": net_profit.get("turns", []),
                "gross_income": net_profit.get("gross_income", []),
                "upkeep": net_profit.get("upkeep", []),
                "net_profit": net_profit.get("net_profit", [])
            })
            
            # 2. Get Military Data (CER & Attrition)
            cer = self.data_provider.get_faction_combat_effectiveness(universe, run_id, f, batch_id, turn_range)
            attrition = self.data_provider.get_faction_attrition_rate(universe, run_id, f, batch_id, turn_range)
            mil_df = pd.DataFrame({
                "turn": cer.get("turns", []),
                "cer": cer.get("values", []), # Updated from 'cer' to 'values' based on DataProvider impl
            })
            attrition_df = pd.DataFrame({
                "turn": attrition.get("turns", []),
                "attrition": attrition.get("attrition", [])
            })
            mil_df = pd.merge(mil_df, attrition_df, on="turn", how="outer")
            
            # 3. Get Stockpile Data
            velocity = self.data_provider.get_faction_stockpile_velocity(universe, run_id, f, batch_id, turn_range)
            vel_data = velocity.get("factions", {}).get(f, {})
            vel_df = pd.DataFrame({
                "turn": velocity.get("turns", []),
                "stockpile": vel_data.get("stockpile", []),
                "velocity": vel_data.get("velocity", [])
            })
            
            # 4. Get Fleet Power (Units)
            power = self.data_provider.get_faction_fleet_power(universe, run_id, f, batch_id, turn_range)
            power_df = pd.DataFrame({
                "turn": power.get("turns", []),
                "power": power.get("power", [])
            })

            # 5. Get Construction Efficiency
            eff = self.data_provider.get_faction_queue_efficiency(universe, run_id, f, batch_id, turn_range)
            eff_df = pd.DataFrame({
                "turn": eff.get("turns", []),
                "construction_efficiency": eff.get("efficiency", []),
                "idle_slots": eff.get("idle_slots", [])
            })

            # 6. Get Tech Progress (Research)
            tech = self.data_provider.get_faction_tech_tree_progress(universe, run_id, f, batch_id, turn_range)
            # Tech progress returns a dict per tier, we'll just sum them for a 'tech_count' metric
            tech_fac = tech.get("factions", {}).get(f, {})
            tech_count = sum(tech_fac.get("techs_by_tier", {}).values()) if tech_fac else 0
            # Since this isn't a time series in the provider yet, we'll repeat it or mark it
            # In a real scenario, we'd need get_faction_tech_history
            tech_df = pd.DataFrame({"turn": [turn_range[1]], "tech_count": [tech_count]})

            # Combine all available data for this faction
            combined = pd.merge(econ_df, mil_df, on="turn", how="outer")
            combined = pd.merge(combined, vel_df, on="turn", how="outer")
            combined = pd.merge(combined, power_df, on="turn", how="outer")
            combined = pd.merge(combined, eff_df, on="turn", how="outer")
            combined = pd.merge(combined, tech_df, on="turn", how="outer").fillna(0)
            
            # Filter columns based on requested metrics
            if metrics:
                allowed_cols = ['turn']
                for m in metrics:
                    if m in metric_map:
                        allowed_cols.extend(metric_map[m])
                
                # Filter to only existing columns in intersection
                final_cols = [c for c in allowed_cols if c in combined.columns]
                combined = combined[final_cols]

            combined["faction"] = f
            all_frames.append(combined)
            
        if not all_frames:
            return pd.DataFrame(columns=["turn", "faction"])
            
        return pd.concat(all_frames, ignore_index=True)
