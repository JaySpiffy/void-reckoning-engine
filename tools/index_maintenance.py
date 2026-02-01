import sqlite3
import argparse
import os
import sys

def get_stats(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n=== Index Statistics ===")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM runs")
        print(f"Total Runs indexed: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM events")
        print(f"Total Events: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM factions")
        print(f"Faction Turn Snapshots: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM battles")
        print(f"Total Battles: {cursor.fetchone()[0]}")
        
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"Database Size: {size_mb:.2f} MB")
        print(f"Database Path: {os.path.abspath(db_path)}")
    except sqlite3.OperationalError as e:
        print(f"Error reading statistics: {e}")
    finally:
        conn.close()

def vacuum_db(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    print(f"Optimizing database {db_path} (VACUUM)...")
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        print("Optimization complete.")
    except Exception as e:
        print(f"Error during vacuum: {e}")

def verify_integrity(db_path):
    if not os.path.exists(db_path): return
    print(f"Verifying integrity for {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        print(f"Integrity Check: {result}")
        conn.close()
    except Exception as e:
        print(f"Verification failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Index maintenance utilities")
    parser.add_argument("--db-path", help="Path to index database")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--vacuum", action="store_true", help="Optimize database size")
    parser.add_argument("--verify", action="store_true", help="Verify database integrity")

    args = parser.parse_args()
    
    db_path = args.db_path or os.path.join("reports", "index.db")
    
    if args.verify:
        verify_integrity(db_path)
    if args.stats:
        get_stats(db_path)
    if args.vacuum:
        vacuum_db(db_path)
    
    if not any([args.stats, args.vacuum, args.verify]):
        parser.print_help()

if __name__ == "__main__":
    main()
