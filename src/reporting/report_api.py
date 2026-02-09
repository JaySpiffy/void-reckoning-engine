import os
import json
import time
import psutil
from datetime import datetime
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file, stream_with_context, Response
from .report_queue import ReportJobQueue
from .dashboard_data_provider import DashboardDataProvider
from .exporter import DataExporter
from .indexer import ReportIndexer

report_api_bp = Blueprint('report_api', __name__)
alerts_api_bp = Blueprint('alerts_api', __name__)

def get_indexer():
    # Attempt to get from global state if running via live_dashboard
    try:
        from src.reporting.live_dashboard import state
        if state.initialized:
            return state.indexer
    except:
        pass
    return ReportIndexer("reports/db/index.db")

@report_api_bp.route('/reports/list', methods=['GET'])
def list_reports():
    from src.reporting.indexing import ReportIndexer
    universe = request.args.get('universe')
    limit = int(request.args.get('limit', 100))
    
    try:
        # Assuming Indexer singleton or creation on fly
        indexer = ReportIndexer("reports/db/index.db") 
        # Note: ReportIndexer might need to be persistent or cached
        
        # Querying indexer directly via sqlite connection for now as placeholder for method
        cursor = indexer.conn.cursor()
        query = "SELECT run_id, universe, winner, turns_taken, timestamp FROM runs"
        params = []
        if universe:
            query += " WHERE universe = ?"
            params.append(universe)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        reports = [
            {
                "run_id": r[0], 
                "universe": r[1],
                "winner": r[2], 
                "turns": r[3],
                "date": r[4]
            } for r in rows
        ]
        return jsonify({"count": len(reports), "reports": reports})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/download', methods=['GET'])
def download_report():
    path = request.args.get('path')
    if not path:
        return jsonify({"error": "Path required"}), 400
        
    # Security: Ensure path is within reports directory
    abs_path = os.path.abspath(path)
    reports_root = os.path.abspath("reports")
    
    if not abs_path.startswith(reports_root):
        return jsonify({"error": "Access denied: Path traversal attempt"}), 403
        
    if not os.path.exists(abs_path):
        return jsonify({"error": "File not found"}), 404
        
    # Determine mimetype
    ext = os.path.splitext(abs_path)[1].lower()
    mimetype = "application/octet-stream"
    if ext == ".pdf": mimetype = "application/pdf"
    elif ext == ".xlsx": mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif ext == ".json": mimetype = "application/json"
    
    return send_file(abs_path, as_attachment=True, mimetype=mimetype)

@report_api_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    from src.reporting.generators import GENERATORS
    
    data = request.json
    universe = data.get('universe')
    run_id = data.get('run_id')
    formats = data.get('formats', ['json'])
    webhook = data.get('webhook_url')
    
    if not universe or not run_id:
        return jsonify({"error": "Missing universe or run_id"}), 400
        
    # Validate formats
    valid_formats = list(GENERATORS.keys()) + ['json']
    invalid = [f for f in formats if f not in valid_formats]
    if invalid:
        return jsonify({"error": f"Invalid formats: {invalid}. Supported: {valid_formats}"}), 400
        
    queue = ReportJobQueue.get_instance()
    # queue.start_worker() is handled inside add_job per recent fix
    job_id = queue.add_job(universe, run_id, formats, webhook)
    
    return jsonify({"job_id": job_id, "status": "queued"})

@report_api_bp.route('/reports/status/<job_id>', methods=['GET'])
def check_status(job_id):
    queue = ReportJobQueue.get_instance()
    status = queue.get_status(job_id)
    if not status:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(status)

@report_api_bp.route('/reports/analytics', methods=['GET'])
def get_analytics():
    from src.reporting.indexing import ReportIndexer
    universe = request.args.get('universe')
    
    if not universe:
        return jsonify({"error": "Universe context required"}), 400
        
    try:
        indexer = ReportIndexer("reports/db/index.db")
        # Reuse logic similar to CrossUniverseReporter or dedicated AnalyticsEngine
        # For API response speed, we do a quick aggregate query
        cursor = indexer.conn.cursor()
        cursor.execute("SELECT COUNT(*), AVG(turns_taken) FROM runs WHERE universe = ?", (universe,))
        basic = cursor.fetchone()
        
        return jsonify({
            "universe": universe,
            "total_runs": basic[0],
            "average_turns": round(basic[1] or 0, 1)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/runs/gold_standard', methods=['GET', 'POST', 'DELETE'])
def handle_gold_standard():
    from src.reporting.indexing import ReportIndexer
    
    universe = request.args.get('universe')
    if not universe and request.method == 'POST':
        universe = (request.json or {}).get('universe')
    
    if not universe:
        return jsonify({"error": "Universe required"}), 400
        
    try:
        indexer = ReportIndexer("reports/db/index.db")
        
        if request.method == 'GET':
            run = indexer.get_gold_standard_run(universe)
            return jsonify({"universe": universe, "gold_standard": run})
            
        elif request.method == 'POST':
            data = request.json or {}
            run_id = data.get('run_id')
            batch_id = data.get('batch_id')
            if not run_id or not batch_id:
                return jsonify({"error": "run_id and batch_id required"}), 400
                
            success = indexer.set_gold_standard_run(universe, run_id, batch_id)
            if success:
                return jsonify({"success": True, "message": "Gold standard set"})
            else:
                return jsonify({"success": False, "message": "Failed to set gold standard"}), 500
                
        elif request.method == 'DELETE':
            success = indexer.clear_gold_standard(universe)
            return jsonify({"success": success, "message": "Gold standard cleared"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/compare/runs', methods=['GET'])
def compare_runs_endpoint():
    from src.reporting.indexing import ReportIndexer
    universe = request.args.get('universe')
    current_run_id = request.args.get('current_run_id')
    current_batch_id = request.args.get('current_batch_id')
    baseline_run_id = request.args.get('baseline_run_id')
    baseline_batch_id = request.args.get('baseline_batch_id')
    
    if not all([universe, current_run_id, current_batch_id, baseline_run_id, baseline_batch_id]):
        return jsonify({"error": "Missing required parameters"}), 400
        
    try:
        indexer = ReportIndexer("reports/db/index.db")
        result = indexer.compare_runs(universe, current_run_id, current_batch_id, baseline_run_id, baseline_batch_id)
        if "error" in result:
             return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/compare/analysis', methods=['GET'])
def analyze_replay_divergence():
    from src.reporting.indexing import ReportIndexer
    from src.observability.replay_analyzer import ReplayAnalyzer
    
    universe = request.args.get('universe')
    run_a = request.args.get('run_a')
    run_b = request.args.get('run_b')
    
    if not all([universe, run_a, run_b]):
        return jsonify({"error": "Missing parameters (universe, run_a, run_b)"}), 400
        
    try:
        indexer = ReportIndexer("reports/db/index.db")
        analyzer = ReplayAnalyzer(indexer)
        report = analyzer.compare_runs(universe, run_a, run_b)
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/compare/runs/gold_standard', methods=['GET'])
def compare_gold_standard():
    from src.reporting.indexing import ReportIndexer
    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    
    if not all([universe, run_id, batch_id]):
        return jsonify({"error": "Missing parameters"}), 400
        
    try:
        indexer = ReportIndexer("reports/db/index.db")
        gold = indexer.get_gold_standard_run(universe)
        
        if not gold:
            return jsonify({"error": "No gold standard set for this universe"}), 404
            
        result = indexer.compare_runs(universe, run_id, batch_id, gold['run_id'], gold['batch_id'])
        if "error" in result:
             return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Alert API Endpoints (Step 6) ---

@alerts_api_bp.route('/active', methods=['GET'])
def get_active_alerts():
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    alerts = am.get_active_alerts()
    return jsonify([a.to_dict() for a in alerts])

@alerts_api_bp.route('/history', methods=['GET'])
def get_alert_history():
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    
    severity = request.args.get('severity')
    faction = request.args.get('faction')
    alert_type = request.args.get('type')
    limit = int(request.args.get('limit', 50))
    
    alerts = am.history.alerts
    
    filtered = []
    for a in alerts:
        if severity and a.severity.value != severity: continue
        if faction and a.context.get('faction') != faction: continue
        if alert_type and a.rule_name != alert_type: continue
        filtered.append(a)
    
    filtered.sort(key=lambda x: x.timestamp, reverse=True)
    return jsonify([a.to_dict() for a in filtered[:limit]])

@alerts_api_bp.route('/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    for a in am.history.alerts:
        if a.id == alert_id:
            a.acknowledged = True
            return jsonify({"success": True})
    return jsonify({"error": "Alert not found"}), 404

@alerts_api_bp.route('/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    for a in am.history.alerts:
        if a.id == alert_id:
            a.resolved = True
            return jsonify({"success": True})
    return jsonify({"error": "Alert not found"}), 404

@alerts_api_bp.route('/top', methods=['GET'])
def get_top_alerts():
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    alerts = am.get_active_alerts()
    
    severity_map = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    alerts.sort(key=lambda x: (severity_map.get(x.severity.value, 4), x.timestamp), reverse=False)
    
    return jsonify([a.to_dict() for a in alerts[:5]])

@alerts_api_bp.route('/summary', methods=['GET'])
def get_alert_summary_api():
    from src.reporting.alert_manager import AlertManager
    am = AlertManager()
    active = am.get_active_alerts()
    history = am.history.alerts
    
    by_severity = {}
    for a in history:
        s = a.severity.value
        by_severity[s] = by_severity.get(s, 0) + 1
        
    return jsonify({
        "total": len(history),
        "active": len(active),
        "by_severity": by_severity
    })

# --- Export API Endpoints (Comment 1) ---

def _get_exporter():
    # Helper to get indexer and exporter
    db_path = "reports/db/index.db" # Default path
    indexer = ReportIndexer(db_path)
    provider = DashboardDataProvider(indexer)
    return DataExporter(provider)

@report_api_bp.route('/reports/export/metrics', methods=['POST'])
def export_metrics_api():
    try:
        data = request.json or {}
        universe = data.get('universe')
        run_id = data.get('run_id')
        batch_id = data.get('batch_id')
        factions = data.get('factions', [])
        turn_range_raw = data.get('turn_range', {})
        turn_range = (turn_range_raw.get('min', 0), turn_range_raw.get('max', 9999))
        metrics = data.get('metrics', [])
        format = data.get('format', 'csv')

        if not all([universe, run_id, factions]):
            return jsonify({"error": "Missing required parameters (universe, run_id, factions)"}), 400

        exporter = _get_exporter()
        
        if format == 'csv':
            output = exporter.export_to_csv(universe, run_id, factions, turn_range, batch_id, metrics)
            filename = f"export_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            mimetype = "text/csv"
        elif format == 'excel':
            output = exporter.export_to_excel(universe, run_id, factions, turn_range, batch_id, metrics)
            filename = f"export_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            return jsonify({"error": "Unsupported format for this endpoint. Use /pdf for PDF."}), 400

        return send_file(output, mimetype=mimetype, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/reports/export/metrics/pdf', methods=['POST'])
def export_metrics_pdf_api():
    try:
        data = request.json or {}
        universe = data.get('universe')
        run_id = data.get('run_id')
        batch_id = data.get('batch_id')
        factions = data.get('factions', [])
        turn_range_raw = data.get('turn_range', {})
        turn_range = (turn_range_raw.get('min', 0), turn_range_raw.get('max', 9999))
        # PDF might not use simple metric filtering yet, but we accept it
        
        if not all([universe, run_id, factions]):
            return jsonify({"error": "Missing required parameters"}), 400

        exporter = _get_exporter()
        output = exporter.export_to_pdf(universe, run_id, factions, turn_range, batch_id)
        
        filename = f"report_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # --- Industrial API Endpoints (New) ---

@report_api_bp.route('/industrial/queue_efficiency', methods=['GET'])
def get_queue_efficiency_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)
    
    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    faction = request.args.get('faction')
    
    if not all([universe, run_id, faction]):
        return jsonify({"turns": [], "values": [], "efficiency": 1.0})
        
    return jsonify(provider.get_queue_efficiency(universe, run_id, faction, batch_id))

@report_api_bp.route('/industrial/timeline', methods=['GET'])
def get_industrial_timeline_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)
    
    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    limit = int(request.args.get('limit', 20))
    
    if not all([universe, run_id]):
        return jsonify([])
        
    return jsonify(provider.get_construction_timeline(universe, run_id, batch_id, limit))

# --- Research API Endpoints (New) ---

@report_api_bp.route('/research/tech_tree_progress', methods=['GET'])
def get_tech_progress_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)
    
    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    faction = request.args.get('faction')
    
    if not all([universe, run_id, faction]):
        return jsonify({"turns": [], "values": []})
        
    return jsonify(provider.get_tech_tree_progress(universe, run_id, faction, batch_id))

@report_api_bp.route('/military/fleet_history', methods=['GET'])
def get_fleet_history_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)

    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    
    # Allow multi-faction query
    factions_param = request.args.get('faction')
    factions = factions_param.split(',') if factions_param else []
    
    downsample = request.args.get('downsample', type=int)

    if not all([universe, run_id]):
        return jsonify({"factions": {}})

    results = {}
    for f in factions:
        if not f: continue
        results[f] = provider.get_faction_fleet_count_history(universe, run_id, f, batch_id, downsample)

    return jsonify({"factions": results})

@report_api_bp.route('/history/territory', methods=['GET'])
def get_territory_history_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)

    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    
    factions_param = request.args.get('faction')
    factions = factions_param.split(',') if factions_param else []
    downsample = request.args.get('downsample', type=int)

    if not all([universe, run_id]):
        return jsonify({"factions": {}})

    results = {}
    for f in factions:
        if not f: continue
        results[f] = provider.get_faction_territory_history(universe, run_id, f, batch_id, downsample)

    return jsonify({"factions": results})

@report_api_bp.route('/history/battle_stats', methods=['GET'])
def get_battle_stats_history_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)

    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    batch_id = request.args.get('batch_id')
    
    factions_param = request.args.get('faction')
    factions = factions_param.split(',') if factions_param else []
    downsample = request.args.get('downsample', type=int)

    if not all([universe, run_id]):
        return jsonify({"factions": {}})

    results = {}
    for f in factions:
        if not f: continue
        results[f] = provider.get_faction_battle_stats_history(universe, run_id, f, batch_id, downsample)

    return jsonify({"factions": results})

@report_api_bp.route('/reports/trace', methods=['GET'])
def get_event_trace_api():
    from src.reporting.dashboard_data_provider import DashboardDataProvider
    indexer = get_indexer()
    provider = DashboardDataProvider(indexer)

    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    trace_id = request.args.get('trace_id')

    if not all([universe, run_id, trace_id]):
        return jsonify({"chain": []})

    chain = provider.get_event_trace(universe, run_id, trace_id)
    return jsonify({"chain": chain})


# --- Paginated & Performance API Endpoints (Step 8) ---

@report_api_bp.route('/metrics/paginated', methods=['GET'])
def get_paginated_metrics():
    indexer = get_indexer()
    table = request.args.get('table', 'telemetry')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 100, type=int)
    
    faction = request.args.get('faction')
    universe = request.args.get('universe')
    run_id = request.args.get('run_id')
    
    try:
        if table == 'alerts':
            # Handle in-memory alerts pagination
            from src.reporting.alert_manager import AlertManager
            am = AlertManager()
            # Filter by optional params if needed (simple implementation for now)
            # Assuming AlertManager holds global state or can retrieve persisting alerts
            
            all_alerts = am.history.alerts
            # Filter
            filtered = [a for a in all_alerts if (not faction or a.context.get('faction') == faction)]
            # Sort likely by timestamp desc
            filtered.sort(key=lambda x: x.timestamp, reverse=True)
            
            total_count = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            items = filtered[start:end]
            
            return jsonify({
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "items": [a.to_dict() for a in items]
            })

        elif table in ['telemetry', 'events']:
            data = indexer.query_telemetry(
                run_id=run_id, 
                universe=universe, 
                faction=faction,
                page=page, 
                page_size=page_size
            )
        elif table == 'resource_transactions':
            data = indexer.query_resource_transactions(
                faction=faction,
                universe=universe,
                page=page,
                page_size=page_size
            )
        elif table == 'battle_performance':
            data = indexer.query_battle_performance(
                faction=faction,
                universe=universe,
                page=page,
                page_size=page_size
            )
        else:
            return jsonify({"error": f"Unsupported table: {table}"}), 400

        # Adapt indexer output to frontend items key if necessary
        return jsonify({
            "page": data.get("page", page),
            "page_size": data.get("page_size", page_size),
            "total": data.get("total_count", 0),
            "total_pages": data.get("total_pages", 0),
            "items": data.get("data", [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@report_api_bp.route('/performance/stats', methods=['GET'])
def get_performance_stats():
    indexer = get_indexer()
    stats = {
        "memory": indexer.get_memory_usage(),
        "cache": indexer.cache.get_cache_stats() if hasattr(indexer, 'cache') else {},
        "profiling_enabled": getattr(indexer, 'enable_profiling', False)
    }
    return jsonify(stats)

@report_api_bp.route('/performance/profiling/enable', methods=['POST'])
def enable_profiling():
    indexer = get_indexer()
    indexer.enable_profiling = True
    return jsonify({"status": "enabled"})

@report_api_bp.route('/performance/profiling/disable', methods=['POST'])
def disable_profiling():
    indexer = get_indexer()
    indexer.enable_profiling = False
    return jsonify({"status": "disabled"})

@report_api_bp.route('/performance/slow_queries', methods=['GET'])
def get_slow_queries():
    try:
        with open("reports/db/query_profile.log", "r") as f:
            lines = f.readlines()[-50:] # Last 50 queries
            return jsonify({"queries": lines})
    except:
        return jsonify({"queries": []})

@report_api_bp.route('/export/stream', methods=['GET'])
def stream_export():
    indexer = get_indexer()
    run_id = request.args.get('run_id')
    universe = request.args.get('universe')
    
    def generate():
        query = "SELECT * FROM telemetry WHERE run_id = ? AND universe = ?"
        cursor = indexer.conn.cursor()
        cursor.execute(query, (run_id, universe))
        cols = [column[0] for column in cursor.description]
        yield json.dumps(cols) + "\n"
        
        while True:
            row = cursor.fetchone()
            if not row: break
            yield json.dumps(row) + "\n"
            
    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')
