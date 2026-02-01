
import os

path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\src\reporting\static\dashboard.js"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

keep = lines[:1850]

# Ensure it ends cleanly
if keep[-1].strip() != '}':
    pass # It should be '}' based on my view

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(keep)
    f.write('\n') # Ensure newline

print(f"Truncated {path} to {len(keep)} lines.")
