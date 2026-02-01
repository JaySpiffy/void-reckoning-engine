import sqlite3
import os

# Configuration
DB_PATH = "reports/campaign_data.db"
RUN_ID = "run_1768696819"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"--- CHECKING RESOURCE TRANSACTIONS for {RUN_ID} ---")
    try:
        cursor.execute("""
            SELECT category, SUM(amount), COUNT(*), MIN(amount), MAX(amount)
            FROM resource_transactions 
            WHERE run_id = ?
            GROUP BY category
        """, (RUN_ID,))
        
        rows = cursor.fetchall()
        for r in rows:
            print(f"Category: {r[0]} | Sum: {r[1]} | Count: {r[2]} | Min: {r[3]} | Max: {r[4]}")
                
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
