
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from tools.universal_importer import main as universal_main

def main():
    """
    Entry point for the Universal Game Importer.
    Delegates to the main function in universal_importer.py.
    """
    universal_main()

if __name__ == "__main__":
    main()
