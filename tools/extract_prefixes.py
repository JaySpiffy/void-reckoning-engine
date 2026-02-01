import re

def get_prefixes(file_path):
    prefixes = set()
    pattern = re.compile(r'^\s*"([^:]+):')
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                prefixes.add(match.group(1))
    return sorted(list(prefixes))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for p in get_prefixes(sys.argv[1]):
            print(p)
