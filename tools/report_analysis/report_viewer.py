import sqlite3
import os
import json
import sys

class ReportViewer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_batches(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT batch_id FROM runs ORDER BY batch_id DESC")
        batches = [row['batch_id'] for row in cursor.fetchall()]
        conn.close()
        return batches

    def list_runs(self, batch_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT run_id, winner, turns_taken FROM runs WHERE batch_id = ? ORDER BY run_id ASC", (batch_id,))
        runs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return runs

    def list_turns(self, batch_id: str, run_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT turn FROM events WHERE batch_id = ? AND run_id = ? AND turn IS NOT NULL ORDER BY turn ASC", (batch_id, run_id))
        turns = [row['turn'] for row in cursor.fetchall()]
        conn.close()
        return turns

    def view_turn_summary(self, batch_id: str, run_id: str, turn: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Faction summaries for this turn
        cursor.execute("SELECT faction, requisition, planets_controlled FROM factions WHERE batch_id = ? AND run_id = ? AND turn = ?", (batch_id, run_id, turn))
        f_stats = [dict(row) for row in cursor.fetchall()]
        
        # Battles for this turn
        cursor.execute("SELECT location, winner, duration_rounds FROM battles WHERE batch_id = ? AND run_id = ? AND turn = ?", (batch_id, run_id, turn))
        battles = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return f_stats, battles

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_loop(db_path):
    viewer = ReportViewer(db_path)
    state = {"view": "batches", "batch": None, "run": None, "turn": None}
    
    while True:
        clear_screen()
        print(f"--- SIMULATION REPORT VIEWER ({db_path}) ---")
        
        if state["view"] == "batches":
            batches = viewer.list_batches()
            print("\nAvailable Batches:")
            for i, b in enumerate(batches):
                print(f"{i+1}. {b}")
            print("\nOptions: [id] to select, [q] to quit")
            
            cmd = input("> ").strip().lower()
            if cmd == 'q': break
            if cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(batches):
                    state["batch"] = batches[idx]
                    state["view"] = "runs"
                    
        elif state["view"] == "runs":
            print(f"\nBatch: {state['batch']}")
            runs = viewer.list_runs(state["batch"])
            print("\nRuns in Batch:")
            header = "ID".ljust(15) + " | " + "WINNER".ljust(15) + " | " + "TURNS"
            print(header)
            print("-" * len(header))
            for i, r in enumerate(runs):
                print(f"{i+1}. {r['run_id'].ljust(12)} | {str(r['winner']).ljust(15)} | {r['turns_taken']}")
            
            print("\nOptions: [id] to select, [b] for back, [q] to quit")
            cmd = input("> ").strip().lower()
            if cmd == 'q': break
            if cmd == 'b': state["view"] = "batches"
            if cmd.isdigit():
                idx = int(cmd) - 1
                if 0 <= idx < len(runs):
                    state["run"] = runs[idx]['run_id']
                    state["view"] = "turns"

        elif state["view"] == "turns":
            print(f"\nBatch: {state['batch']} | Run: {state['run']}")
            turns = viewer.list_turns(state["batch"], state["run"])
            if not turns:
                print("No turn data found for this run (possibly old format or text-only).")
                print("\nOptions: [b] for back, [q] to quit")
            else:
                print(f"\nIndexed Turns ({len(turns)} total):")
                # Show first 10 and last 10 if many
                if len(turns) > 20:
                    for t in turns[:10]: print(f"{t}", end=", ")
                    print("...", end=", ")
                    for t in turns[-10:]: print(f"{t}", end=", ")
                else:
                    for t in turns: print(f"{t}", end=", ")
                print("\n\nEnter turn number to view details.")
                
                print("\nOptions: [turn#] to select, [b] for back, [q] to quit")
            
            cmd = input("> ").strip().lower()
            if cmd == 'q': break
            if cmd == 'b': state["view"] = "runs"
            if cmd.isdigit():
                t_num = int(cmd)
                if t_num in turns:
                    state["turn"] = t_num
                    state["view"] = "turn_detail"

        elif state["view"] == "turn_detail":
            print(f"\nBatch: {state['batch']} | Run: {state['run']} | Turn: {state['turn']}")
            f_stats, battles = viewer.view_turn_summary(state["batch"], state["run"], state["turn"])
            
            print("\n--- Faction Snapshots ---")
            if f_stats:
                header = "FACTION".ljust(15) + " | " + "REQ".ljust(10) + " | " + "PLANETS"
                print(header)
                for f in f_stats:
                    print(f"{f['faction'].ljust(15)} | {str(f['requisition']).ljust(10)} | {f['planets_controlled']}")
            else:
                print("No faction snapshots for this turn.")
                
            print("\n--- Battles ---")
            if battles:
                header = "LOCATION".ljust(20) + " | " + "WINNER".ljust(15) + " | " + "ROUNDS"
                print(header)
                for b in battles:
                    print(f"{str(b['location']).ljust(20)} | {str(b['winner']).ljust(15)} | {b['duration_rounds']}")
            else:
                print("No battles recorded this turn.")
                
            print("\nOptions: [b] for back, [q] to quit")
            cmd = input("> ").strip().lower()
            if cmd == 'q': break
            if cmd == 'b': state["view"] = "turns"

if __name__ == "__main__":
    db_default = os.path.join("reports", "index.db")
    if not os.path.exists(db_default):
        db_default = os.path.join("reports", "reports", "index.db")
        
    path = sys.argv[1] if len(sys.argv) > 1 else db_default
    try:
        main_loop(path)
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"Error: {e}")
