import os

def cleanup():
    units_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\void_reckoning\units"
    keep_files = ["procedural_roster.json", "procedural_land_roster.json", "hand_crafted_roster.json"]
    
    deleted_count = 0
    for file in os.listdir(units_dir):
        if file.endswith(".json") and file not in keep_files:
            filepath = os.path.join(units_dir, file)
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {file}: {e}")
                
    print(f"Deleted {deleted_count} legacy files.")

if __name__ == "__main__":
    cleanup()
