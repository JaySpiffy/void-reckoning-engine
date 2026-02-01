
import sqlite3
import json
import os

def check_combat_events():
    base_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)"
    db_path = os.path.join(base_dir, "reports", "multi_universe_20260127_120032", "eternal_crusade", "index.db")
    
    print(f"Checking database at: {db_path}")
    if not os.path.exists(db_path):
        print("Database path does not exist!")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Detected Tables: {tables}")
        
        if 'events' not in tables:
            print("No 'events' table found.")
            return

        # Query battles
        print("Checking 'battles' table...")
        cursor.execute("SELECT * FROM battles LIMIT 5")
        battles = cursor.fetchall()
        
        if not battles:
            print("No battles found in battles table.")
        else:
            print(f"Found {len(battles)} battles.")
            for b in battles:
                print(f"Battle: {b}")

        # Query events again but without engagement filter to see what types exist
        cursor.execute("SELECT DISTINCT event_type FROM events LIMIT 20")
        print(f"Distinct Event Types: {[r[0] for r in cursor.fetchall()]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    check_combat_events()
