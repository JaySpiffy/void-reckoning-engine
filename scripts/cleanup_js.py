
import os

filepath = r'c:\Users\whitt\OneDrive\Desktop\New folder (4)\src\reporting\static\dashboard.js'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Goal: Keep up to line 4108 (approx) and skip until 4638
# Wait, let's precisely identify the cut-off.
# Line 4108 is end of loadIndustrialData.
# Line 4109 is loadInitialData.
# Line 4149 is DOMContentLoaded.

# I'll keep everything until line 4211.
# And I'll keep everything from 4638 onwards.

new_lines = lines[:4211] + lines[4637:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Cleaned dashboard.js. New length: {len(new_lines)} lines.")
