import argparse
import os
import sys

# Add root to sys.path to ensure src is found if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.indexer import ReportIndexer

def find_batches(reports_dir):
    """Discover all batch directories."""
    batches = []
    if not os.path.exists(reports_dir):
        return batches
        
    for d in os.listdir(reports_dir):
        path = os.path.join(reports_dir, d)
        if os.path.isdir(path) and d.startswith("batch_"):
            batches.append(path)
    return batches

def main():
    parser = argparse.ArgumentParser(description="Build simulation index database")
    parser.add_argument("--reports-dir", default="reports", help="Directory containing batches")
    parser.add_argument("--batch", help="Specific batch ID to index")
    parser.add_argument("--db-path", help="Path to SQLite index database")
    parser.add_argument("--rebuild", action="store_true", help="Clear database before indexing")
    parser.add_argument("--incremental", action="store_true", help="Only index new runs (default behavior)")

    args = parser.parse_args()

    db_path = args.db_path or os.path.join(args.reports_dir, "index.db")
    
    if args.rebuild and os.path.exists(db_path):
        print(f"Rebuilding index: Deleting {db_path}")
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Error deleting database: {e}")

    # Ensure reports directory exists
    if not os.path.exists(args.reports_dir):
        print(f"Error: Reports directory {args.reports_dir} not found.")
        return

    indexer = ReportIndexer(db_path)
    
    try:
        if args.batch:
            batch_path = os.path.join(args.reports_dir, args.batch)
            if not os.path.exists(batch_path):
                print(f"Error: Batch {args.batch} not found in {args.reports_dir}")
            else:
                print(f"Indexing batch {args.batch}...")
                indexer.index_batch(batch_path)
        else:
            batches = find_batches(args.reports_dir)
            if not batches:
                print("No batches found to index.")
            else:
                print(f"Found {len(batches)} batches.")
                for i, batch_path in enumerate(batches):
                    print(f"[{i+1}/{len(batches)}] Indexing {os.path.basename(batch_path)}...")
                    indexer.index_batch(batch_path)
    finally:
        indexer.close()
        
    print("Indexing complete.")

if __name__ == "__main__":
    main()
