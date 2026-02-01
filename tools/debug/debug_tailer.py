import sys
import os
import json
import psutil

# Mock LogTailer implementation
class LogTailer:
    def __init__(self, file_path):
        self.file_path = file_path
        self._file = None
        
    def open(self, seek_end=True):
        if not os.path.exists(self.file_path):
            print(f"File not found: {self.file_path}")
            return False
        self._file = open(self.file_path, 'r', encoding='utf-8')
        if seek_end:
            self._file.seek(0, 2)
        return True
        
    def read_lines(self):
        if not self._file: return
        while True:
            curr = self._file.tell()
            line = self._file.readline()
            if not line:
                self._file.seek(curr)
                break
            if line.endswith('\n'):
                yield line
            else:
                self._file.seek(curr)
                break

# Target Content
target_file = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\eternal_crusade\batch_20260117_080248\run_1768636968\campaign.json"

print(f"Checking file: {target_file}")
if not os.path.exists(target_file):
    print("CRITICAL: File does not exist via python os.path!")
    sys.exit(1)

size = os.path.getsize(target_file)
print(f"File Size: {size} bytes")

tailer = LogTailer(target_file)
if tailer.open(seek_end=False):
    print("Tailer opened successfully (Start).")
    count = 0
    turns = set()
    for line in tailer.read_lines():
        count += 1
        try:
            evt = json.loads(line)
            if 'turn' in evt:
                turns.add(evt['turn'])
        except Exception as e:
            print(f"JSON Error on line {count}: {e}")
    
    print(f"Read {count} lines.")
    print(f"Turns found: {sorted(list(turns))}")
    
    if count == 0:
        print("CRITICAL: Read 0 lines! Checking why...")
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read(100)
            print(f"First 100 chars raw: {repr(content)}")
else:
    print("Failed to open tailer.")
