import re
import hashlib
import time
import sqlite3
import json
import csv
import argparse
import sys
import os
from typing import List, Dict, Any, Optional

# --- Phase 1: Query Parser & Logic ---

class QueryParser:
    """Maps natural language queries to SQL and parameters."""
    
    INTENTS = {
        'BATTLE_QUERY': r'\b(battle|combat|fight|engagement|war)\b',
        'FACTION_STATS': r'\b(statistics|stats|performance|summary|report)\b',
        'TIMELINE': r'\b(timeline|history|sequence|chronology)\b',
        'COMPARISON': r'\b(compare|versus|vs|diff)\b',
        'RESOURCE_FLOW': r'\b(resource|economy|income|production|req|promethium)\b'
    }

    def parse(self, nl_query: str) -> Dict[str, Any]:
        """Parse natural language query into structured filters."""
        filters = {}
        nl_query = nl_query.lower()

        # Intent Detection
        intent = "GENERIC"
        for key, pattern in self.INTENTS.items():
            if re.search(pattern, nl_query):
                intent = key
                break
        filters['intent'] = intent

        # Event Type / Table Selection
        if intent == 'BATTLE_QUERY':
            filters['table'] = 'battles'
        elif intent in ('FACTION_STATS', 'RESOURCE_FLOW'):
            filters['table'] = 'factions'
        else:
            filters['table'] = 'events'

        # Faction Extraction
        # Simple heuristic: look for capitalized words in original query or specific knowledge
        # For now, relying on explicit "faction X" pattern or assume user provides valid names
        # Improved: "faction <name>" or "player <name>"
        faction_match = re.search(r'(?:faction|player)\s+([a-zA-Z0-9_]+)', nl_query)
        if faction_match:
            filters['faction'] = faction_match.group(1)

        # Outcome Extraction
        if 'won' in nl_query or 'winner' in nl_query:
            # "won by X" or "X won" - simplified to just detecting intent to filter by winner
            # If faction is extracted, assume they are the winner
            if 'faction' in filters:
                filters['winner'] = filters['faction']
        elif 'lost' in nl_query or 'loser' in nl_query:
             if 'faction' in filters:
                 filters['loser'] = filters['faction']

        # Time/Turn Extraction
        turn_range = re.search(r'(?:turn|turns)\s+(\d+)(?:\s*(?:-|to)\s*(\d+))?', nl_query)
        if turn_range:
            start = turn_range.group(1)
            end = turn_range.group(2)
            if end:
                filters['turns'] = f"{start}-{end}"
            else:
                filters['turns'] = start
                
        # Last N turns
        last_n = re.search(r'last\s+(\d+)\s+turns', nl_query)
        if last_n:
             # This requires knowing max turn, handled in SQL or by caller. 
             # For CLI tool, simpler to map to "sort desc limit N".
             filters['limit'] = int(last_n.group(1))
             filters['sort'] = 'desc'

        # Resources keywords
        if 'resource' in nl_query or 'economy' in nl_query:
            filters['category'] = 'economy'

        return filters

def build_advanced_query(args, nl_filters=None):
    """Construct SQL with composite filters."""
    # Base Table
    table = "events"
    if nl_filters and 'table' in nl_filters:
        table = nl_filters['table']
    elif hasattr(args, 'winner') and args.winner:
        table = "battles"
        
    query = f"SELECT * FROM {table}"
    params = []
    where_clauses = []

    # Merge CLI args and NL filters (CLI takes precedence)
    filters = nl_filters or {}
    
    # Generic mappings
    faction = args.faction or filters.get('faction')
    batch = args.batch
    run = args.run
    turns = args.turns or filters.get('turns')
    search = args.search
    category = args.category or filters.get('category')
    
    # Advanced mappings
    winner = getattr(args, 'winner', None) or filters.get('winner')
    loser = getattr(args, 'loser', None) or filters.get('loser')
    min_damage = getattr(args, 'min_damage', None)
    
    # Clause Construction
    if batch:
        where_clauses.append("batch_id = ?")
        params.append(batch)
    
    if run:
        runs = run.split(",")
        clause = "run_id IN (" + ",".join(["?"] * len(runs)) + ")"
        where_clauses.append(clause)
        params.extend(runs)
        
    if faction:
        if table == 'battles':
            where_clauses.append("(factions_involved LIKE ? OR winner = ?)")
            params.extend([f"%{faction}%", faction])
        else:
            where_clauses.append("faction = ?")
            params.append(faction)

    if winner and table == 'battles':
        where_clauses.append("winner = ?")
        params.append(winner)
        
    if loser and table == 'battles':
        # Loser is involved but not winner
        where_clauses.append("(factions_involved LIKE ? AND winner != ?)")
        params.extend([f"%{loser}%", loser])
            
    if category and table == 'events':
        where_clauses.append("category = ?")
        params.append(category)

    if turns:
        if "-" in str(turns):
            s, e = str(turns).split("-")
            where_clauses.append("turn BETWEEN ? AND ?")
            params.extend([int(s), int(e)])
        else:
            where_clauses.append("turn = ?")
            params.append(int(turns))
            
    if min_damage and table == 'battles':
        where_clauses.append("total_damage >= ?")
        params.append(float(min_damage))

    if hasattr(args, 'event_type') and args.event_type and table == 'events':
        where_clauses.append("event_type = ?")
        params.append(args.event_type)
        
    if hasattr(args, 'location') and args.location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{args.location}%")

    if search and table == 'events':
         # Assuming naive LIKE fallback for simplicity here unless FTS passed down
         where_clauses.append("(keywords LIKE ? OR data_json LIKE ?)")
         params.extend([f"%{search}%", f"%{search}%"])

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        
    # Sorting
    if filters.get('sort') == 'desc':
        query += " ORDER BY turn DESC"
    
    limit = args.limit or filters.get('limit') or 100
    query += f" LIMIT {limit} OFFSET {args.offset}"
    
    return query, params

# --- Caching Support ---

def get_cache_path(query, params):
    cache_dir = ".query_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    
    key_str = f"{query}|{params}"
    key = hashlib.md5(key_str.encode()).hexdigest()
    return os.path.join(cache_dir, f"{key}.json")

def load_cache(cache_path, ttl=3600):
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if time.time() - cached['timestamp'] < ttl:
                return cached['results']
        except:
            pass
    return None

def save_cache(cache_path, query, params, results):
    data = {
        'timestamp': time.time(),
        'query': query,
        'params': params,
        'rows': len(results),
        'results': results
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- Updated Output Formatter ---

def format_results(results, format="table", output_path=None):
    """Enhanced formatting."""
    if not results:
        print("No results found.")
        return

    out = sys.stdout
    should_close = False
    if output_path:
        out = open(output_path, "w", encoding="utf-8", newline="")
        should_close = True

    try:
        keys = results[0].keys()
        
        if format == "json":
            json.dump(results, out, indent=2)
        elif format == "csv":
            writer = csv.DictWriter(out, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        elif format == "markdown":
            # GitHub table
            display_keys = [k for k in keys if k not in ["data_json", "keywords", "id"]]
            header = "| " + " | ".join(display_keys) + " |"
            sep = "| " + " | ".join(["---"] * len(display_keys)) + " |"
            print(header, file=out)
            print(sep, file=out)
            for row in results:
                print("| " + " | ".join([str(row.get(k,"")) for k in display_keys]) + " |", file=out)
        elif format == "html":
            out.write("<html><body><table border='1'><thead><tr>")
            display_keys = [k for k in keys if k not in ["data_json", "keywords", "id"]]
            for k in display_keys: out.write(f"<th>{k}</th>")
            out.write("</tr></thead><tbody>")
            for row in results:
                out.write("<tr>")
                for k in display_keys: out.write(f"<td>{row.get(k,'')}</td>")
                out.write("</tr>")
            out.write("</tbody></table></body></html>")
            
        else:  # table (CLI)
            # Filter out and truncate for table view
            display_keys = [k for k in keys if k not in ["data_json", "keywords", "id"]]
            
            # Header
            header = " | ".join([k.upper().ljust(15) for k in display_keys])
            print(header, file=out)
            print("-" * len(header), file=out)
            
            for row in results:
                vals = [str(row.get(k, "")).ljust(15)[:15] for k in display_keys]
                print(" | ".join(vals), file=out)
                
        # Summary footer
        if format == "table" and out == sys.stdout:
            print(f"\nTotal Rows: {len(results)}")
            
    finally:
        if should_close:
            out.close()
            print(f"Results saved to {output_path}")

# --- Legacy Helper Functions (Preserved/Updated) ---

def execute_query(db_path, query, params):
    """Run query and fetch results."""
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return []
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"SQL Error: {e}")
        return []
    finally:
        conn.close()

def export_timeline(db_path, batch_id, output_path):
    query = "SELECT turn, run_id, timestamp, category, event_type, faction, location, entity_name, data_json FROM events WHERE batch_id = ? ORDER BY turn ASC, timestamp ASC"
    results = execute_query(db_path, query, [batch_id])
    format_results(results, "csv", output_path)

def faction_statistics(db_path, faction, batch_id, turns=None, format="table", output_path=None):
    query = """
        SELECT 
            faction,
            ROUND(AVG(requisition), 2) as avg_req_delta,
            ROUND(AVG(promethium), 2) as avg_prom_delta,
            MAX(planets_controlled) as max_planets,
            SUM(units_recruited) as total_units_recruited,
            SUM(units_lost) as total_units_lost,
            SUM(battles_fought) as total_battles,
            SUM(battles_won) as total_wins,
            ROUND(SUM(damage_dealt), 2) as total_damage
        FROM factions
        WHERE faction = ? AND batch_id = ?
    """
    params = [faction, batch_id]
    
    if turns:
        if "-" in turns:
            try:
                start, end = turns.split("-")
                query += " AND turn BETWEEN ? AND ?"
                params.extend([int(start), int(end)])
            except ValueError: pass
        else:
            try:
                query += " AND turn = ?"
                params.append(int(turns))
            except ValueError: pass
            
    query += " GROUP BY faction"
    
    results = execute_query(db_path, query, params)
    format_results(results, format, output_path)

def run_query(args):
    db_path = getattr(args, "db_path", os.path.join("reports", "index.db"))
    
    if args.clear_cache:
        import shutil
        if os.path.exists(".query_cache"):
            shutil.rmtree(".query_cache")
            print("Cache cleared.")
        return

    if args.timeline:
        if not args.batch:
            print("Error: --batch is required for --timeline")
            return
        output = args.output or f"timeline_{args.batch}.csv"
        export_timeline(db_path, args.batch, output)
    elif args.faction_stats:
        if not args.batch:
            print("Error: --batch is required for --faction-stats")
            return
        faction_statistics(db_path, args.faction_stats, args.batch, args.turns, args.format, args.output)
    else:
        # Check cache
        nl_filters = None
        if args.query_nl:
            parser = QueryParser()
            nl_filters = parser.parse(args.query_nl)
            
        initial_query, initial_params = build_advanced_query(args, nl_filters)
        
        cache_path = get_cache_path(initial_query, initial_params)
        if args.use_cache:
            start_t = time.time()
            cached = load_cache(cache_path)
            if cached is not None:
                print(f"Loaded from cache ({time.time()-start_t:.3f}s)")
                format_results(cached, args.format, args.output)
                return

        results = execute_query(db_path, initial_query, initial_params)
        
        if args.use_cache and results:
            save_cache(cache_path, initial_query, initial_params, results)
        
        format_results(results, args.format, args.output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query simulation reports")
    # Basic
    parser.add_argument("--db-path", help="Path to SQLite index database")
    parser.add_argument("--batch", help="Batch ID to query")
    parser.add_argument("--run", help="Specific run ID(s), comma-separated")
    parser.add_argument("--faction", help="Filter by faction")
    parser.add_argument("--category", choices=["economy", "combat", "diplomacy", "movement", "construction", "system"])
    parser.add_argument("--turns", help="Turn range (e.g., 50-60)")
    parser.add_argument("--search", help="Full-text search query")
    
    # Advanced / NL
    parser.add_argument("--query-nl", help="Natural language query string")
    parser.add_argument("--event-type", help="Filter by exact event type")
    parser.add_argument("--location", help="Filter by location (LIKE matched)")
    parser.add_argument("--winner", help="Filter battles by winner")
    parser.add_argument("--loser", help="Filter battles by loser")
    parser.add_argument("--min-damage", type=float, help="Minimum total damage")
    
    # Modes
    parser.add_argument("--timeline", action="store_true", help="Export timeline CSV")
    parser.add_argument("--faction-stats", help="Faction name for statistics")
    
    # Output
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=["json", "csv", "table", "markdown", "html"], default="table")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0)
    
    # Cache
    parser.add_argument("--use-cache", action="store_true", help="Enable query result caching")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the query cache")
    
    args = parser.parse_args()
    
    # Default DB path if not provided
    if not args.db_path:
        args.db_path = os.path.join("reports", "index.db")
        
    run_query(args)
