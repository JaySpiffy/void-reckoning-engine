
import os
import sys
import re

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.utils.dna_generator import generate_dna_from_stats
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_INFORMATION,
    ATOM_AETHER, ATOM_WILL, ATOM_VOLATILITY, ATOM_FREQUENCY,
    ATOM_STABILITY, ATOM_FOCUS
)

ATOM_NAME_MAPPING = {
    "Mass": ATOM_MASS,
    "Energy": ATOM_ENERGY,
    "Cohesion": ATOM_COHESION,
    "Information": ATOM_INFORMATION,
    "Aether": ATOM_AETHER,
    "Will": ATOM_WILL,
    "Volatility": ATOM_VOLATILITY,
    "Frequency": ATOM_FREQUENCY,
    "Stability": ATOM_STABILITY,
    "Focus": ATOM_FOCUS
}

TARGET_DIRS = [
    r"universes/warhammer40k_atomic",
    r"universes/star_wars_atomic",
    r"universes/star_trek_atomic"
]

def format_dna_string(dna):
    """Formats DNA dict into 'Mass: 10, Energy: 20' string."""
    parts = []
    # Reverse mapping for display names
    rev_mapping = {v: k for k, v in ATOM_NAME_MAPPING.items()}
    
    # Sort by value desc
    sorted_items = sorted(dna.items(), key=lambda x: x[1], reverse=True)
    
    for k, v in sorted_items:
        display_name = rev_mapping.get(k, k).replace("atom_", "").capitalize()
        # Clean 'atom_' prefix manually if mapping fails
        if display_name.startswith("Atom_"):
             display_name = display_name[5:]
             
        parts.append(f"{display_name}: {v:.2f}")
        
    return ", ".join(parts)

def retrofit_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stats = {}
    
    # Check for Standard <!-- PARSER_DATA -->
    match_html = re.search(r"<!--\s*PARSER_DATA\s*(.*?)\s*-->", content, re.DOTALL)
    
    # Check for JSON Codeblock (Star Trek Style)
    match_json = re.search(r"## Parser Data\s*```json\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    
    if match_html:
        data_block = match_html.group(1)
        for line in data_block.split('\n'):
            if ":" in line:
                parts = line.split(":", 1)
                stats[parts[0].strip()] = parts[1].strip()
                
    elif match_json:
        try:
            import json
            json_str = match_json.group(1)
            json_data = json.loads(json_str)
            # Normalize to standard keys
            stats["name"] = json_data.get("name", "")
            stats["requisition_cost"] = json_data.get("cost", 0)
            stats["role"] = str(json_data.get("tags", []))
            stats["keywords"] = str(json_data.get("tags", []))
            
            if "stats" in json_data:
                s = json_data["stats"]
                stats["hp"] = s.get("hull", 0)
                stats["armor"] = s.get("armor", 0)
                stats["speed"] = s.get("speed", 0)
        except Exception as e:
            print(f"Skipping {filepath}: Failed to parse JSON: {e}")
            return
            
    else:
        print(f"Skipping {filepath}: No PARSER_DATA found")
        return
            
    # 2. Generate DNA
    try:
        true_dna = generate_dna_from_stats(stats)
        dna_str = format_dna_string(true_dna)
        
        # 3. Replace Existing Signature
        # Regex to find: ## Elemental Signature \n ... \n
        # It might be multiline, so we look for "## Elemental Signature" 
        # followed by text until the next section start "## " or "<!--" or End of File
        
        # We know from `inject_elemental_dna.py` that we inserted it before PARSER_DATA.
        # So we can look for the specific block we inserted or just replace the previous generic line.
        
        # Generic Replacement Strategy:
        # Find "## Elemental Signature"
        # Find the content line(s) below it.
        # Replace content line.
        
        
        header_idx = content.find("## Elemental Signature")
        
        if header_idx != -1:
            # Case A: Header exists (Update existing)
            # Find next section to define bounds
            next_section_start = -1
            
            # Look for common delimiters
            search_start = header_idx + len("## Elemental Signature")
            
            # Next header
            match_header = re.search(r"##\s+[A-Za-z0-9]", content[search_start:])
            # Parser Data start
            match_parser = re.search(r"(<!--|## Parser Data)", content[search_start:])
            
            candidates = []
            if match_header: candidates.append(search_start + match_header.start())
            if match_parser: candidates.append(search_start + match_parser.start())
            
            if candidates:
                 next_section_start = min(candidates)
            else:
                 next_section_start = len(content)
                 
            new_content = content[:header_idx] + f"## Elemental Signature\n{dna_str}\n\n" + content[next_section_start:]
            
        else:
            # Case B: Header Missing (Insert new)
            # Preferred: Before ## Parser Data or <!-- PARSER_DATA
            anchor_idx = -1
            
            match_parser = re.search(r"(<!--\s*PARSER_DATA|## Parser Data)", content)
            if match_parser:
                anchor_idx = match_parser.start()
            
            # Fallback: End of Stats section?
            # Simpler: Just put it at the end if no parser data (but we know parser data exists to reach here)
            
            if anchor_idx != -1:
                new_content = content[:anchor_idx] + f"## Elemental Signature\n{dna_str}\n\n" + content[anchor_idx:]
            else:
                # Append to end
                new_content = content + f"\n\n## Elemental Signature\n{dna_str}\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Retrofit: {os.path.basename(filepath)} -> {dna_str[:50]}...")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    root_dir = os.getcwd()
    count = 0
    for rel_dir in TARGET_DIRS:
        abs_path = os.path.join(root_dir, rel_dir)
        if not os.path.exists(abs_path): continue
            
        for root, dirs, files in os.walk(abs_path):
            for file in files:
                if file.endswith(".md"):
                    retrofit_file(os.path.join(root, file))
                    count += 1
    print(f"Completed retrofitting {count} files.")

if __name__ == "__main__":
    main()
