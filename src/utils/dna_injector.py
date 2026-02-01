
import os
import json
import re
from typing import Dict, Any, Optional

def inject_dna_into_markdown(filepath: str, dna: Dict[str, float]) -> bool:
    """
    Injects a DNA signature into a Markdown file.
    
    It looks for a ## PARSER DATA block and inserts the DNA signature
    immediately after it as a ## DNA Signature block.
    
    If ## DNA Signature already exists, it updates it.
    
    Args:
        filepath: Path to the markdown file.
        dna: The DNA dictionary to inject.
        
    Returns:
        True if successful, False otherwise.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        dna_block = f"## DNA Signature\n```json\n{json.dumps(dna, indent=2)}\n```\n"
        
        # Check if DNA Signature already exists
        if "## DNA Signature" in content:
            # Replace existing block
            pattern = r"## DNA Signature\n```json\n.*?\n```\n"
            if re.search(pattern, content, re.DOTALL):
                new_content = re.sub(pattern, dna_block, content, flags=re.DOTALL)
            else:
                # Appended but maybe malformed? Just append if regex fails but header exists
                # Or better, try to find the header and replace until next header
                # For safety, let's just regex replace if well formed, else append
                 new_content = re.sub(r"## DNA Signature.*?(?=\n#|\Z)", dna_block, content, flags=re.DOTALL)
        else:
            # Insert after PARSER DATA
            if "## PARSER DATA" in content:
                 # Find end of parser data block
                 # Assuming parser data is usually at the end or followed by something
                 # We look for the closing ``` of the parser data
                 pattern = r"(## PARSER DATA\n.*?\n```\n)"
                 match = re.search(pattern, content, re.DOTALL)
                 if match:
                     # Insert after the match
                     end_pos = match.end()
                     new_content = content[:end_pos] + "\n" + dna_block + content[end_pos:]
                 else:
                     # Fallback: Append to end
                     new_content = content + "\n" + dna_block
            else:
                # Fallback: Append to end
                new_content = content + "\n" + dna_block
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"Error injecting DNA into {filepath}: {e}")
        return False

def extract_parser_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the data from a Parser Data block in a markdown file.
    Supports both JSON code blocks and HTML comments.
    """
    if not os.path.exists(filepath):
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Try JSON Code Block (Standard)
        # Search case-insensitively for ## Parser Data
        json_pattern = r"## [Pp]arser [Dd]ata\n```json\n(.*?)\n```"
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # 2. Try HTML Comment Block (Legacy/Compat)
        # Matches: <!-- PARSER_DATA\nkey: value\n...-->
        comment_pattern = r"<!-- PARSER_DATA\n(.*?)\n-->"
        match = re.search(comment_pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            data = {}
            lines = match.group(1).split('\n')
            for line in lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    k = key.strip().lower()
                    v = val.strip()
                    # Try to parse as JSON if it looks like one (list/dict)
                    if v.startswith('[') or v.startswith('{'):
                        try:
                            v = json.loads(v.replace("'", '"'))
                        except:
                            pass
                    # Convert floats/ints if possible
                    try:
                        if '.' in v: v = float(v)
                        else: v = int(v)
                    except:
                        pass
                    data[k] = v
            return data
            
    except Exception as e:
        print(f"Error extracting parser data from {filepath}: {e}")
        
    return None

def extract_dna_from_markdown(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Extracts the JSON content from the ## DNA Signature block in a markdown file.
    """
    if not os.path.exists(filepath):
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        pattern = r"## DNA Signature\n```json\n(.*?)\n```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
            
    except Exception as e:
        # DNA block might not exist yet if skipped or failed
        pass
        
    return None
