import argparse
import os
import sys
from src.cli.base_command import BaseCommand

class ExportCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "export"

    @property
    def help(self) -> str:
        return "Export reports and analytics"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        subparsers = parser.add_subparsers(dest="export_type", help="Export type")
        
        # Export Reports
        exp_report = subparsers.add_parser("report", help="Export specific run report")
        exp_report.add_argument("--universe", required=True)
        exp_report.add_argument("--run-id", required=True)
        exp_report.add_argument("--formats", nargs="+", default=["pdf", "excel"], help="Output formats")
        exp_report.add_argument("--output-dir", required=True)
        
        # Export Analytics
        exp_analytics = subparsers.add_parser("analytics", help="Export campaign analytics")
        exp_analytics.add_argument("--universe", required=True)
        exp_analytics.add_argument("--output-dir", required=True)
        exp_analytics.add_argument("--formats", nargs="+", default=["pdf", "excel"], help="Output formats")
        exp_analytics.add_argument("--webhook", help="Webhook URL for completion notification")

    def execute(self, args: argparse.Namespace) -> None:
        from src.reporting.indexing import ReportIndexer
        from src.reporting.analytics_engine import AnalyticsEngine
        from src.reporting.faction_reporter import FactionReporter
        import glob
        
        # Mock Engine for Reporter linkage logic
        class MockEngine:
             def __init__(self, unis, rid):
                 self.universe_data = type('obj', (object,), {'name': unis})
                 self.run_id = rid
                 self.logger = None
                 self.factions = {} 
        
        if args.export_type == "analytics":
            # Resolving DB Path for Export
            db_path = None
            run_id = getattr(args, 'run_id', None)
            
            if run_id:
                # Try to find run folder
                pattern = f"reports/{args.universe}/batch_*/{run_id}/campaign_data.db"
                matches = glob.glob(pattern)
                if matches:
                    db_path = matches[0]
            
            if not db_path:
                 # Fallback/Discovery
                 try:
                     from src.reporting.dashboard_v2.api.utils.discovery import discover_latest_run
                     _, found_id, found_path = discover_latest_run(args.universe)
                     if found_path:
                         db_path = os.path.join(found_path, "campaign_data.db")
                         print(f"Auto-selected latest run: {found_id}")
                 except ImportError:
                     pass
            
            if not db_path or not os.path.exists(db_path):
                print(f"Error: Could not locate campaign_data.db for universe '{args.universe}' and run '{run_id or 'latest'}'")
                return

            print(f"Using Database: {db_path}")
            indexer = ReportIndexer(db_path)
            
            # Reconstruct linkage
            reporter = FactionReporter(MockEngine(args.universe, getattr(args, 'run_id', 'batch')))
            reporter.analytics_engine = AnalyticsEngine(indexer)
            
            print(f"Exporting analytics for {args.universe} to {args.output_dir}...")
            reporter.export_analytics_report(args.output_dir, formats=args.formats, webhook_url=args.webhook)
            print("Done.")
            
        elif args.export_type == "report":
            print("Exporting individual run report not fully implemented via CLI yet.")
            pass
