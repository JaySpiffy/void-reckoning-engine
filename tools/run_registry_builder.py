import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # tools -> root
sys.path.append(project_root)

try:
    from src.utils.registry_builder import build_all_registries
except ImportError:
    # Try adding one more level up if running from root
    sys.path.append(os.path.dirname(project_root))
    from src.utils.registry_builder import build_all_registries

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_registry_builder.py <universe_name>")
        sys.exit(1)
        
    universe_name = sys.argv[1]
    print(f"Building registries for {universe_name}...")
    build_all_registries(universe_name)
    print("Done.")
