
import os
import re

def verify_tactical_data(root_dir):
    required_fields = ["weapon_arcs", "armor_front", "armor_side", "armor_rear", "agility", "grid_size", "facing"]
    missing_data = {}
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md") and "ship_" in file:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                missing = []
                # Check for fields in the PARSER_DATA block
                # Simplistic check: just look for the string "field:"
                for field in required_fields:
                    if f"{field}:" not in content:
                        missing.append(field)
                
                if missing:
                    missing_data[file_path] = missing

    if not missing_data:
        print("All ship files have required tactical data!")
        with open("missing_data.txt", "w") as f:
            f.write("None")
    else:
        print(f"Found {len(missing_data)} files with missing data.")
        with open("missing_data.txt", "w") as f:
            for path, missing in missing_data.items():
                f.write(f"{path}\n")

if __name__ == "__main__":
    data_dir = os.path.join(os.getcwd(), "data", "factions")
    verify_tactical_data(data_dir)
