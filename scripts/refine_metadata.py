import os
import re

def refine_markdowns(universe_path):
    infra_dir = os.path.join(universe_path, 'infrastructure')
    tech_dir = os.path.join(universe_path, 'technology')
    
    # 1. Refine Buildings
    for file in os.listdir(infra_dir):
        if file.endswith('.md') and 'Zealot' not in file:
            path = os.path.join(infra_dir, file)
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                new_lines.append(line)
                # After Unlocks or after Build Time if Unlocks missing
                if '**Build Time:**' in line or '**Unlocks:**' in line:
                    if not any('**Capacity:**' in next_line for next_line in lines[lines.index(line):lines.index(line)+5] if lines.index(line)+5 < len(lines)):
                        new_lines.append("- **Capacity:** 5 Units\n")
            
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Refined {file}")

    # 2. Refine Tech (Simplistic example, harder to automate without unit names)
    # So we mainly do buildings automatically and tech manually or with a more complex map.
    
if __name__ == "__main__":
    refine_markdowns(r'c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade')
