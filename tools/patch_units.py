import os

AUDIT_FILE = "audit_results_utf8.txt"

TECH_MAP = {
    "Chaos": {
        3: ["Dark Pacts"],
        4: ["Warp Fusion"],
        5: ["Daemon Ascension"]
    },
    "Imperium": {
        "Land": {
            3: ["Castellum Stronghold"],
            4: ["Fortress Monastery"],
            5: ["Reclusiam"]
        },
        "Space": {
            3: ["Orbital Dock"],
            4: ["Deep Space Foundry"],
            5: ["Deep Space Foundry"]
        }
    },
    "Necrons": {
        3: ["Living Metal Refinement"],
        4: ["Living Metal Refinement"],
        5: ["Awakening Protocols"]
    },
    "Orks": {
        3: ["Slaver Pits"],
        4: ["Shiny Gubbinz"],
        5: ["Infinite Waaagh!"]
    },
    "Tau_Empire": {
        3: ["Air Caste Doctrines"],
        4: ["Fusion Collider Theory"],
        5: ["Fifth Sphere Expansion"]
    },
    "Tyranids": {
        3: ["Metabolic Overdrive"],
        4: ["Regeneration Cysts"],
        5: ["Hive Mind Omniscience"]
    },
    "Aeldari": {
        3: ["Wraithbone Singing"],
        4: ["Webway Gate"],
        5: ["Spirit Stones"]
    }
}

def get_tech(faction, tier, unit_type):
    # Handle Sub-Factions
    if "Chaos" in faction:
        return TECH_MAP["Chaos"].get(tier, ["Dark Pacts"])
    
    # Generic Faction Map
    f_map = TECH_MAP.get(faction)
    if not f_map:
        return ["Unknown Tech"]
        
    # Handle Type Split (Imperium)
    if "Land" in f_map:
        type_map = f_map.get(unit_type, f_map["Land"])
        return type_map.get(tier, ["Unknown Tech"])
    
    # Simple Map
    return f_map.get(tier, ["Unknown Tech"])

def patch():
    print("Patching Unit Tech Requirements...")
    
    # Read Audit List
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    patched_count = 0
    
    for line in lines:
        if "Missing Tech" not in line: continue
        
        # Parse Line: [TIER 5] Name: Missing Tech (Path)
        try:
            if ": Missing Tech (" not in line: continue
            
            parts = line.split(": Missing Tech (")
            path = parts[1].strip().rstrip(")")
            
            # Extract Tier
            tier_str = line.split("]")[0].split(" ")[1]
            tier = int(tier_str)
            
            if not os.path.exists(path):
                print(f"Skipping {path} (Not Found)")
                continue
                
            # Identify Faction and Type from Path
            # Path: ...\data\factions\Chaos_Khorne\Space_Units\ship_name.md
            path_parts = path.replace("\\", "/").split("/")
            
            faction = "Unknown"
            unit_type = "Land"
            
            if "factions" in path_parts:
                idx = path_parts.index("factions")
                if idx + 1 < len(path_parts):
                    faction = path_parts[idx+1]
                if "Space_Units" in path_parts:
                    unit_type = "Space"
            
            # Determine Tech
            techs = get_tech(faction, tier, unit_type)
            
            # Apply Patch
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if "required_tech:" in content:
                # Replace existing empty line
                new_line = f'required_tech: ["{techs[0]}"]'
                # Use regex to replace specifically the field
                import re
                new_content = re.sub(r"required_tech:\s*\[?\]?", new_line, content)
                
                # If regex didn't change anything (because it wasn't empty empty?), force it
                # Check directly
                if "required_tech: []" in content:
                     new_content = content.replace("required_tech: []", new_line)
                elif "required_tech: None" in content:
                     new_content = content.replace("required_tech: None", new_line)
                
                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    patched_count += 1
                    # print(f"Patched {faction} {Math.tier} -> {techs}")
            
        except Exception as e:
            print(f"Error patching line: {line.strip()} -> {e}")

    print(f"Successfully Patched {patched_count} files.")

if __name__ == "__main__":
    patch()
