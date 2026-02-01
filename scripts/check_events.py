
import sqlite3
import json

def check_combat_events():
    db_path = 'reports/eternal_crusade/index.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for any combat or engagement events
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor.execute(query)
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        # Try a more generic search for tables that contain 'event' or 'combat'
        for (table_name,) in tables:
            print(f"Sampling {table_name}...")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            print(f"Sample from {table_name}: {cursor.fetchone()}")
        
        if not rows:
            print("No combat events found in database.")
            return

        print(f"Found {len(rows)} combat events.")
        for row in rows[:5]: # Show first 5
            category, event_type, data_json = row
            data = json.loads(data_json)
            # Look for rounds or damage in the data
            rounds = data.get('rounds') or data.get('total_rounds')
            damage = data.get('total_damage') or data.get('damage_dealt')
            print(f"Event: {event_type} | Rounds: {rounds} | Damage: {damage}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_combat_events()
