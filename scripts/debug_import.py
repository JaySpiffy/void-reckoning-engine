
import sys
import os
try:
    from src.factories.unit_factory import UnitFactory
    print("UnitFactory imported successfully!")
    print(f"File: {UnitFactory.__module__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
