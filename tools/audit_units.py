import os
import re

DATA_DIR = r"C:\Users\whitt\Desktop\New folder (4)\data\factions"

def audit():
    print("Auditing Unit Tech Requirements...")
    issues = []
    
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".md") and not file.startswith("tech_tree") and not file.startswith("faction_"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extract PARSER_DATA
                match = re.search(r"<!-- PARSER_DATA(.*?)-->", content, re.DOTALL)
                if not match:
                    continue
                    
                data_block = match.group(1)
                stats = {}
                for line in data_block.split('\n'):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        stats[key.strip()] = val.strip()
                
                val = stats.get("tier", "1").split("#")[0].strip()
                try:
                    tier = int(val)
                except:
                    tier = 1
                name = stats.get("name", file)
                req_tech = stats.get("required_tech", "[]")
                
                # Check for empty tech on Tier 3+
                if tier >= 3:
                    is_empty = False
                    if req_tech == "[]" or req_tech == "None" or not req_tech:
                        is_empty = True
                    
                    if is_empty:
                        issues.append(f"[TIER {tier}] {name}: Missing Tech ({path})")

    with open("audit_results_utf8.txt", "w", encoding="utf-8") as f:
        if issues:
            f.write(f"FOUND {len(issues)} ISSUES:\n")
            for i in issues:
                f.write(i + "\n")
        else:
            f.write("All High-Tier Units have Tech Requirements!")

if __name__ == "__main__":
    audit()
