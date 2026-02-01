import sqlite3
import os

DB_PATH = "reports/db/index.db"
# Swapped for revert
OLD_UNIVERSE = "eternal_crusade" 
NEW_UNIVERSE = "unknown"

def revert_universe():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables_to_update = ['runs', 'events', 'factions', 'resource_transactions', 'battle_performance', 'battles']
        
        for table in tables_to_update:
            try:
                cursor.execute(f"UPDATE {table} SET universe = ? WHERE universe = ?", (NEW_UNIVERSE, OLD_UNIVERSE))
                print(f"  Reverted table {table}: {cursor.rowcount} rows")
            except sqlite3.OperationalError:
                pass
                
        # Revert paths in metadata
        cursor.execute("SELECT run_id, metadata_json FROM runs WHERE universe = ?", (NEW_UNIVERSE,))
        rows = cursor.fetchall()
        for run_id, meta_json in rows:
            if meta_json and "reports/eternal_crusade" in meta_json:
                new_json = meta_json.replace("reports/eternal_crusade", "reports/unknown")
                cursor.execute("UPDATE runs SET metadata_json = ? WHERE run_id = ?", (new_json, run_id))
                print(f"  Reverted metadata path for run {run_id}")

        conn.commit()
        print("Database revert complete.")
        
    except Exception as e:
        print(f"Error reverting database: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    revert_universe()
