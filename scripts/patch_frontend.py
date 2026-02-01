
import os

JS_PATH = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\frontend\dist\assets\index-8aIGqv5J.js"

FACTION_COLORS = {
    'Solar_Hegemony': '#F59E0B',
    'Void_Corsairs': '#8B5CF6',
    'Zealot_Legions': '#EF4444',
    'Ascended_Order': '#06B6D4',
    'Hive_Swarm': '#84CC16',
    'Iron_Vanguard': '#64748B',  
    'Rift_Daemons': '#B91C1C',
    'Scavenger_Clans': '#F97316',
    'Ancient_Guardians': '#10B981',
    'Cyber_Synod': '#3B82F6'
}

SUFFIXES = [
    '', 
    '_PROFIT', '_STOCKPILE', '_VELOCITY', '_EFFICIENCY', '_IDLE', '_CER', '_ATTRITION',
    '_profit', '_stockpile', '_velocity', '_efficiency', '_idle', '_cer', '_attrition'
]

def generate_color_map():
    entries = []
    # Add Generic
    entries.append('Player:"#3b82f6"')
    
    # Add Factions and variations
    for faction, color in FACTION_COLORS.items():
        for suffix in SUFFIXES:
            key = f"{faction}{suffix}"
            entries.append(f'"{key}":"{color}"')
            
    # Add legacy Generic
    entries.append('AI_1:"#ef4444"')
    entries.append('AI_2:"#f59e0b"')
    entries.append('AI_3:"#22c55e"')
    entries.append('AI_4:"#8b5cf6"')
    entries.append('Neutral:"#94a3b8"')
    
    return "{" + ",".join(entries) + "}"

def patch_file():
    if not os.path.exists(JS_PATH):
        print("JS file not found")
        return

    with open(JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Target: Player:"#3b82f6",AI_1:"#ef4444" ... Neutral:"#94a3b8"}
    # Because valid JSON keys in source were unquoted? No, content output: Player:"#3b82f6"
    
    # We look for the start and end of the object.
    start_marker = 'Player:"#3b82f6"'
    end_marker = 'Neutral:"#94a3b8"}'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Start marker not found")
        return
        
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print("End marker not found")
        return
        
    # Include the closing brace
    end_idx += len(end_marker)

    original_segment = content[start_idx-1:end_idx] # -1 to include opening brace if present?
    # Inspecting previous output: Player:"... is preceded by {?
    # Output was `Player:"...` 
    # Let's assume the brace is before Player
    
    # Let's construct the new segment
    new_map_str = generate_color_map()
    # verify format: {key:val,...}
    
    # We replace from start_idx (Player...) minus 1 (assuming {) to end_idx
    # But wait, if keys are not quoted in source?
    # The output previously: Player:"#3b82f6",AI_1...
    # Player is NOT quoted. But my generated map QUOTES keys.
    # Minified JS objects often don't quote keys if valid identifiers.
    # I should try to match the style or rely on JS accepting quoted keys.
    # JS accepts quoted keys: {"Player":"..."} is valid.
    
    # But wait, finding the range to replace is critical.
    # I will look for `{Player:"#3b82f6"`
    
    real_start_idx = content.find('{Player:"#3b82f6"')
    if real_start_idx == -1:
         # Try without brace
         real_start_idx = content.find('Player:"#3b82f6"')
         if real_start_idx == -1: 
             print("Could not find start sequence")
             return
         # check if char before is {
         if content[real_start_idx-1] == '{':
             real_start_idx -= 1
         else:
             print("Warning: Object start not clearly identified")
    
    # Check end
    real_end_idx = content.find('Neutral:"#94a3b8"}') + len('Neutral:"#94a3b8"}')
    
    print(f"Replacing range {real_start_idx} to {real_end_idx}")
    
    new_content = content[:real_start_idx] + new_map_str + content[real_end_idx:]
    
    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Patch applied successfully.")

if __name__ == "__main__":
    patch_file()
