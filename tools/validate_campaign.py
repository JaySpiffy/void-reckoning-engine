
import sys
import argparse
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.campaign_validator import validate_campaign_file

def main():
    parser = argparse.ArgumentParser(description="Validate Campaign Config JSON")
    parser.add_argument("file", help="Path to campaign_config.json")
    args = parser.parse_args()
    
    success = validate_campaign_file(args.file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
