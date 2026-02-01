import sqlite3
import os

DB_PATH = "reports/db/index.db"

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file {DB_PATH} not found!")
        return

    print(f"[OK] Database found: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. List Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"\n[Tables found]: {tables}")
        
        # 2. Check Campaigns
        if 'campaigns' in tables:
            print("\n[Campaigns]:")
            cursor.execute("SELECT * FROM campaigns")
            rows = cursor.fetchall()
            if rows:
                for r in rows: print(r)
            else:
                print("   (No campaigns found)")
        
        # 3. Check Runs
        if 'runs' in tables:
            print("\n[Runs]:")
            # Just select all columns since we don't know schema
            cursor.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                for r in rows: print(r)
            else:
                print("   (No runs found)")
        
        # 4. Check Events Count
        if 'events' in tables:
            cursor.execute("SELECT count(*) FROM events")
            count = cursor.fetchone()[0]
            print(f"\n[Total Events]: {count}")
            
            if count > 0:
                cursor.execute("SELECT run_id, count(*) FROM events GROUP BY run_id")
                print("   Events per Run ID:")
                for r in cursor.fetchall():
                    print(f"   - {r[0]}: {r[1]} events")

    except Exception as e:
        print(f"[ERROR] Error inspecting DB: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    inspect_db()
