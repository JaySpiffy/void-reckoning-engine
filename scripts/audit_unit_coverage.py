
import json
import os
import sys

# Define expected classes for reference
EXPECTED_CLASSES = {
    "space": {
        1: ["fighter", "bomber", "interceptor"],
        2: ["corvette", "frigate", "destroyer"],
        3: ["light_cruiser", "heavy_cruiser", "battlecruiser", "battleship"],
        4: ["carrier", "dreadnought"],
        5: ["titan", "planet_killer", "world_devastator", "stellar_accelerator"],
        6: ["mothership"]
    },
    "ground": {
        1: ["light_infantry", "assault_infantry", "skirmisher"],
        2: ["light_vehicle", "apc", "anti_tank"],
        3: ["battle_tank", "heavy_vehicle", "superheavy_tank"],
        4: ["command_vehicle"],
        5: ["titan_walker", "siege_engine"],
        6: ["mobile_fortress"]
    }
}

def audit_coverage():
    base_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade"
    registry_path = os.path.join(base_dir, "factions", "faction_registry.json")
    
    with open(registry_path, "r", encoding='utf-8') as f:
        registry = json.load(f)
        
    report = ["# Eternal Crusade Unit Coverage Audit\n"]
    
    for faction_key, data in registry.items():
        report.append(f"## {faction_key}\n")
        
        # Coverage Matrix
        coverage = {"space": {}, "ground": {}} # tier -> set(classes)
        
        unit_files = data.get("unit_files", [])
        for rel_path in unit_files:
            full_path = os.path.join(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade", rel_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding='utf-8') as uf:
                        units = json.load(uf)
                        for u in units:
                            domain = u.get("domain", "space") # Default to space if missing? Actually check logic.
                            u_class = u.get("unit_class")
                            tier = u.get("tier", 1)
                            
                            # Infer domain/tier if missing based on class map (heuristic)
                            if not u_class: continue
                            
                            # Categorize
                            if domain not in coverage: coverage[domain] = {}
                            if tier not in coverage[domain]: coverage[domain][tier] = set()
                            coverage[domain][tier].add(u_class)
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")

        # Render Table
        report.append("| Domain | Tier | Expected Classes | Found Classes | Status |")
        report.append("|---|---|---|---|---|")
        
        all_ok = True
        
        for domain in ["space", "ground"]:
            for tier in range(1, 7):
                if tier not in EXPECTED_CLASSES[domain]: continue
                
                expected = set(EXPECTED_CLASSES[domain][tier])
                found = coverage.get(domain, {}).get(tier, set())
                
                missing = expected - found
                status = "✅ OK" if not missing else f"❌ Missing: {', '.join(missing)}"
                if missing: all_ok = False
                
                # Format strings
                exp_str = ", ".join(sorted(list(expected)))
                found_str = ", ".join(sorted(list(found))) if found else "(None)"
                
                report.append(f"| {domain.title()} | {tier} | {exp_str} | {found_str} | {status} |")
        
        report.append("\n")
        
    # Write Report
    out_path = os.path.join(base_dir, "UNITS_COVERAGE.md")
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"Report generated at {out_path}")

if __name__ == "__main__":
    audit_coverage()
