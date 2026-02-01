import sqlite3
import os

DB_PATH = "reports/db/index.db"
OLD_UNIVERSE = "unknown"
NEW_UNIVERSE = "eternal_crusade"

def update_universe():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables_to_update = ['runs', 'events', 'factions', 'resource_transactions', 'battle_performance', 'battles']
        
        for table in tables_to_update:
            try:
                print(f"Updating table: {table}")
                cursor.execute(f"UPDATE {table} SET universe = ? WHERE universe = ?", (NEW_UNIVERSE, OLD_UNIVERSE))
                print(f"  Rows updated: {cursor.rowcount}")
            except sqlite3.OperationalError as e:
                print(f"  Skipping table {table}: {e}")
                
        # Also need to update the runs metadata_json if it contains the path "reports/unknown/..."
        # This is a bit trickier, requires string replacement in the JSON blob.
        # SQLite's replace functionality might be limited, but let's try a simple version.
        
        # Select runs to fix paths
        cursor.execute("SELECT run_id, metadata_json FROM runs WHERE universe = ?", (NEW_UNIVERSE,))
        rows = cursor.fetchall()
        for run_id, meta_json in rows:
            if meta_json and "reports/unknown" in meta_json:
                new_json = meta_json.replace("reports/unknown", "reports/eternal_crusade")
                cursor.execute("UPDATE runs SET metadata_json = ? WHERE run_id = ?", (new_json, run_id))
                print(f"  Updated metadata path for run {run_id}")

        conn.commit()
        print("Database update complete.")
        
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_universe()
