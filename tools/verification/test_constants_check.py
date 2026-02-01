
try:
    from src.core.constants import BUILDING_DATABASE
    print(f"SUCCESS: BUILDING_DATABASE imported: {type(BUILDING_DATABASE)}")
except ImportError as e:
    print(f"FAILED (ImportError): {e}")
except Exception as e:
    print(f"ERROR: {e}")
