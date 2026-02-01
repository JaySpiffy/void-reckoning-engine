from typing import Dict, Any, List
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .base import BaseReportGenerator

class PDFReportGenerator(BaseReportGenerator):
    """
    Generates professional PDF reports with embedded metrics.
    """
    def generate(self, summary: Dict[str, Any], output_path: str):
        self._ensure_dir(output_path)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        Story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=1))
        
        # Title
        title = f"Campaign Report: {summary.get('universe', 'Unknown Universe')}"
        Story.append(Paragraph(title, styles["Title"]))
        Story.append(Spacer(1, 12))
        
        # Executive Summary
        Story.append(Paragraph("Executive Summary", styles["Heading2"]))
        
        meta = summary.get("metadata", {})
        eco = summary.get("economy", {})
        mil = summary.get("military", {})
        
        data = [
            ["Metric", "Value"],
            ["Turn", str(summary.get("turn", 0))],
            ["Date", meta.get("timestamp", "N/A")],
            ["Total Requisition", f"{eco.get('requisition', 0):,}"],
            ["Military Power", f"{mil.get('military_power', 0):,}"]
        ]
        
        t = Table(data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        Story.append(t)
        Story.append(Spacer(1, 24))
        
        # Economy Section
        Story.append(Paragraph("Economic Performance", styles["Heading2"]))
        eco_text = f"Current Income: {eco.get('income', 0)} | Expenses: {eco.get('expenses', 0)}"
        Story.append(Paragraph(eco_text, styles["Normal"]))
        Story.append(Spacer(1, 12))
        
        # Render Charts if Matplotlib available
        try:
            import matplotlib.pyplot as plt
            import tempfile
            
            # Resource Trend Chart
            # Assuming summary has 'history' or we just mock a simple bar for current distribution
            # For robustness, we'll plot current Income vs Expenses vs Construction
            plt.figure(figsize=(6, 3))
            categories = ['Income', 'Expenses', 'Construction']
            values = [eco.get('income', 0), eco.get('expenses', 0), eco.get('construction_spend', 0)]
            plt.bar(categories, values, color=['green', 'red', 'blue'])
            plt.title('Fiscal Overview')
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_eco:
                plt.savefig(tmp_eco.name, format="png", bbox_inches="tight")
                plt.close()
                Story.append(Image(tmp_eco.name, width=5*inch, height=2.5*inch))
                # Cleanup handled by OS tmp, or explicit deletion?
                # reportlab reads the file during build. We can't delete immediately.
                # We'll rely on tempfile or a wrapper to cleanup after build? 
                # For safety in this concise implementation, we leave it to OS temp cleaning 
                # or store path for later (but 'generate' returns).
                # Actually, reportlab requires file existence at Build time.
                
        except ImportError:
            Story.append(Paragraph("[Matplotlib not installed - Charts unavailable]", styles["Normal"]))
        except Exception as e:
            Story.append(Paragraph(f"[Chart Generation Failed: {e}]", styles["Normal"]))
            
        Story.append(Spacer(1, 12))
        
        # Military Section
        Story.append(Paragraph("Military Status", styles["Heading2"]))
        units = mil.get("units_by_type", {})
        if units:
            unit_data = [["Unit Type", "Count"]]
            for u, c in units.items():
                unit_data.append([u, str(c)])
            
            ut = Table(unit_data, colWidths=[200, 100])
            ut.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black)
            ]))
            Story.append(ut)
            
            Story.append(Spacer(1, 12))
            
            # Military Composition Chart
            try:
                import matplotlib.pyplot as plt
                import tempfile
                
                plt.figure(figsize=(6, 3))
                labels = list(units.keys())
                sizes = list(units.values())
                # Limit to top 5 for readability
                if len(labels) > 5:
                    labels = labels[:5]
                    sizes = sizes[:5]
                    
                plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                plt.title('Fleet Composition')
                
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_mil:
                    plt.savefig(tmp_mil.name, format="png")
                    plt.close()
                    Story.append(Image(tmp_mil.name, width=5*inch, height=2.5*inch))
                    
            except Exception:
                pass

        else:
            Story.append(Paragraph("No active units.", styles["Normal"]))
            
        doc.build(Story)
