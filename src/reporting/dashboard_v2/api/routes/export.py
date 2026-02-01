from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import json
from datetime import datetime
from typing import List, Dict, Any

# Assuming DataExporter exists and can be adapted
from src.reporting.exporter import DataExporter
from src.reporting.dashboard_v2.api.dependencies import get_dashboard_service

router = APIRouter(prefix="/reports/export", tags=["export"])

class ExportRequest(BaseModel):
    universe: str
    run_id: str
    batch_id: str
    factions: List[str]
    turn_range: Dict[str, int]
    metrics: List[str]
    format: str

@router.post("/metrics")
async def export_metrics(
    request: ExportRequest,
    service = Depends(get_dashboard_service)
):
    """
    Handle CSV and Excel exports of simulation metrics.
    """
    try:
        data_provider = service.data_provider
        exporter = DataExporter(data_provider)
        
        # Convert turn_range dict to tuple
        turn_tuple = (request.turn_range.get('min', 0), request.turn_range.get('max', 0))
        
        output: io.BytesIO
        media_type: str
        filename_ext: str

        if request.format == 'excel':
            output = exporter.export_to_excel(
                universe=request.universe,
                run_id=request.run_id,
                factions=request.factions,
                turn_range=turn_tuple,
                batch_id=request.batch_id,
                metrics=request.metrics
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename_ext = "xlsx"
        else:
            # Default to CSV
            output = exporter.export_to_csv(
                universe=request.universe,
                run_id=request.run_id,
                factions=request.factions,
                turn_range=turn_tuple,
                batch_id=request.batch_id,
                metrics=request.metrics
            )
            media_type = "text/csv"
            filename_ext = "csv"
        
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=export_{request.run_id}.{filename_ext}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")

@router.post("/metrics/pdf")
async def export_metrics_pdf(
    request: ExportRequest,
    service = Depends(get_dashboard_service)
):
    """
    Handle PDF generation for simulation metrics.
    """
    try:
        data_provider = service.data_provider
        exporter = DataExporter(data_provider)
        
        turn_tuple = (request.turn_range.get('min', 0), request.turn_range.get('max', 0))
        
        output = exporter.export_to_pdf(
            universe=request.universe,
            run_id=request.run_id,
            factions=request.factions,
            turn_range=turn_tuple,
            batch_id=request.batch_id
        )
        
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=export_{request.run_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
