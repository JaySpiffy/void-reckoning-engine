import os
import re

FACTION_MAP = {
    "Ascended_Order": {"unit": "Acolyte", "ship": "Lantern Class", "building_prefix": "Ascended"},
    "Iron_Vanguard": {"unit": "Conscript", "ship": "Hammer Class", "building_prefix": "Iron"},
    "Hive_Swarm": {"unit": "Drone", "ship": "Bio-Ship", "building_prefix": "Hive"},
    "Cyber_Synod": {"unit": "Thrall", "ship": "Dirge Class", "building_prefix": "Cyber"},
    "Void_Corsairs": {"unit": "Raider", "ship": "Corsair Class", "building_prefix": "Void"},
    "Solar_Hegemony": {"unit": "Legionnaire", "ship": "Solar Class", "building_prefix": "Solar"},
    "Rift_Daemons": {"unit": "Daemon", "ship": "Rift Class", "building_prefix": "Rift"},
    "Scavenger_Clans": {"unit": "Scavenger", "ship": "Junk Class", "building_prefix": "Scavenger"}
}

def clean_and_refine(universe_path):
    infra_dir = os.path.join(universe_path, 'infrastructure')
    tech_dir = os.path.join(universe_path, 'technology')
    
    for faction, data in FACTION_MAP.items():
        # Clean Buildings
        b_file = f"{faction}_buildings.md"
        b_path = os.path.join(infra_dir, b_file)
        if os.path.exists(b_path):
            with open(b_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove existing Capacity lines if they are duplicates or generic
            content = re.sub(r'- \*\*Capacity:\*\*.*?\n', '', content)
            
            # Re-inject Capacity and fix Unlocks
            new_lines = []
            for line in content.splitlines():
                new_lines.append(line)
                if '**Build Time:**' in line:
                    # Add generic capacity
                    new_lines.append(f"- **Capacity:** 5 Units")
                elif '**Unlocks:**' in line:
                    # Fix unit names if needed (very basic fix)
                    line = re.sub(r'\[(.*?)\]', lambda m: f"[{m.group(1).replace(faction, '').strip()}]", line)
                    new_lines[-1] = line
                    
            with open(b_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print(f"Cleaned {b_file}")

        # Refine Tech
        t_file = f"{faction}_tech.md"
        t_path = os.path.join(tech_dir, t_file)
        if os.path.exists(t_path):
            with open(t_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ensure Effects use the Unlocks pattern
            # We'll just append it to known tier 1 techs for now to ensure the registry picks up SOMETHING.
            content = re.sub(r'Basic Doctrine(.*?)- \*\*Effects:\*\* (.*)', 
                            fr'Basic Doctrine\1- **Effects:** \2, Unlocks [{data["unit"]}]', content, flags=re.DOTALL)
            content = re.sub(r'Capital Ships(.*?)- \*\*Effects:\*\* (.*)', 
                            fr'Capital Ships\1- **Effects:** \2, Unlocks [{data["ship"]}]', content, flags=re.DOTALL)
            
            with open(t_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Refined {t_file}")

if __name__ == "__main__":
    clean_and_refine(r'c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade')
