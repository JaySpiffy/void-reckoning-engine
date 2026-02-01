from src.services.recruitment_service import RecruitmentService
import sys
import os

print(f"RecruitmentService loaded from: {RecruitmentService.__module__}")
# Print the file path of the module
module = sys.modules['src.services.recruitment_service']
print(f"File: {module.__file__}")

# Read the file and check for my debug string
with open(module.__file__, 'r') as f:
    content = f.read()
    if "[DEBUG] Trace Blueprint Lookup" in content:
        print("DEBUG CODE FOUND in file.")
    else:
        print("DEBUG CODE NOT FOUND in file.")
