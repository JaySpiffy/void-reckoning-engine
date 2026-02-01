import os

units_to_update = {
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/lucrehulk_csa.md": "corporate_sector_authority, Trade_Federation",
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/munificent.md": "corporate_sector_authority, Trade_Federation, Techno_Union, Commerce_Guild",
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/providence_carrier_destroyer.md": "corporate_sector_authority, Trade_Federation, Commerce_Guild",
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/recusant_light_destroyer.md": "corporate_sector_authority, Trade_Federation, Commerce_Guild",
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/geonosian_cruiser_influence.md": "corporate_sector_authority, Techno_Union",
    "universes/eaw_thrawns_revenge/factions/corporate_sector_authority/Space_Units/keldabe.md": "corporate_sector_authority, Mandalorians"
}

for path, faction_str in units_to_update.items():
    if not os.path.exists(path):
        print(f"Skipping {path} - not found")
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    found_faction = False
    in_parser_data = False
    
    for line in lines:
        if "PARSER_DATA" in line:
            in_parser_data = True
            new_lines.append(line)
            continue
        
        if in_parser_data and line.strip().startswith("faction:"):
            new_lines.append(f"faction: {faction_str}\n")
            found_faction = True
            continue
        
        if in_parser_data and "-->" in line:
            if not found_faction:
                # Add it before the closing tag
                new_lines.append(f"faction: {faction_str}\n")
            in_parser_data = False
            new_lines.append(line)
            continue
        
        new_lines.append(line)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Updated {path}")
