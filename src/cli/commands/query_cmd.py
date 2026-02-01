import argparse
from src.cli.base_command import BaseCommand

class QueryCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "query"

    @property
    def help(self) -> str:
        return "Query simulation reports"

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--batch", help="Batch ID to query")
        parser.add_argument("--run", help="Specific run ID(s), comma-separated")
        parser.add_argument("--faction", help="Filter by faction")
        parser.add_argument("--category", choices=["economy", "combat", "diplomacy", "movement", "construction", "system"])
        parser.add_argument("--turns", help="Turn range (e.g., 50-60)")
        parser.add_argument("--search", help="Full-text search query")
        parser.add_argument("--timeline", action="store_true", help="Export timeline CSV")
        parser.add_argument("--faction-stats", help="Faction name for statistics")
        parser.add_argument("--output", help="Output file path")
        parser.add_argument("--format", choices=["json", "csv", "table"], default="table")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--db-path", help="Path to SQLite index database")

    def execute(self, args: argparse.Namespace) -> None:
        from tools.report_query import run_query
        run_query(args)
