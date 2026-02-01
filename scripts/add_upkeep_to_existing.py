import os
import json

def add_upkeep_to_existing():
    units_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    if not os.path.exists(units_dir):
        print(f"Error: Directory {units_dir} not found.")
        return

    for filename in os.listdir(units_dir):
        if filename.endswith(".json") and not filename.endswith("_dna.json") and "registry" not in filename:
            path = os.path.join(units_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                modified = False
                if isinstance(data, list):
                    for unit in data:
                        if isinstance(unit, dict) and "cost" in unit and "upkeep" not in unit:
                            unit["upkeep"] = unit["cost"] // 10
                            modified = True
                elif isinstance(data, dict):
                    if "cost" in data and "upkeep" not in data:
                        data["upkeep"] = data["cost"] // 10
                        modified = True
                    else:
                        for key, unit in data.items():
                            if isinstance(unit, dict) and "cost" in unit and "upkeep" not in unit:
                                unit["upkeep"] = unit["cost"] // 10
                                modified = True

                if modified:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    print(f"Updated upkeep in {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    add_upkeep_to_existing()
