
import sqlite3
import json
import sys
import os

DB_PATH = "reports/db/index.db"

def check_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- Data Availability Diagnosis ---\n")

    # 1. Check Events Table for 'income_collected'
    print("1. Checking 'income_collected' events:")
    try:
        cursor.execute("SELECT count(*) FROM events WHERE category='economy' AND event_type='income_collected'")
        count = cursor.fetchone()[0]
        print(f"   Total Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT data_json FROM events WHERE category='economy' AND event_type='income_collected' LIMIT 1")
            data = cursor.fetchone()[0]
            print(f"   Sample Data: {data}")
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Check Events Table for 'snapshot'
    print("\n2. Checking 'snapshot' events:")
    try:
        cursor.execute("SELECT count(*) FROM events WHERE category='economy' AND event_type='snapshot'")
        count = cursor.fetchone()[0]
        print(f"   Total Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT data_json FROM events WHERE category='economy' AND event_type='snapshot' LIMIT 1")
            data = cursor.fetchone()[0]
            print(f"   Sample Data: {data}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Check Resource Transactions Table
    print("\n3. Checking 'resource_transactions' table:")
    try:
        cursor.execute("SELECT count(*) FROM resource_transactions")
        count = cursor.fetchone()[0]
        print(f"   Total Count: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM resource_transactions LIMIT 1")
            row = cursor.fetchone()
            print(f"   Sample Row: {row}")
    except Exception as e:
        print(f"   Error: {e}")

    conn.close()

if __name__ == "__main__":
    check_data()
