
import logging
from src.utils.rust_auditor import RustAuditorWrapper
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def verify_auditor():
    auditor = RustAuditorWrapper()
    if not auditor._auditor:
        logger.error("Rust Auditor not available.")
        return

    # 1. Load Registries
    tech_data = {
        "fusion_reactors": { "name": "fusion_reactors", "tier": 2, "cost": 500 },
        "warp_drive": { "name": "warp_drive", "tier": 3, "cost": 1000 }
    }
    
    if not auditor.load_registry("technology", tech_data):
        logger.error("Failed to load technology registry.")
        return
    logger.info("Technology registry loaded.")

    buildings_data = {
        "shipyard": { "name": "shipyard", "tier": 1, "cost": 200 }
    }
    if not auditor.load_registry("buildings", buildings_data):
        logger.error("Failed to load buildings registry.")
        return
    logger.info("Buildings registry loaded.")

    # 2. Initialize Auditor
    auditor.initialize()
    logger.info("Auditor initialized.")

    # 3. Test Field Existence Rule (Success)
    valid_unit = {
        "name": "Scout",
        "tier": 1,
        "armor": 10,
        "speed": 50,
        "required_tech": ["fusion_reactors"]
    }
    results = auditor.validate_entity("unit_1", "unit", valid_unit, "u1", 1)
    if not results:
        logger.info("[SUCCESS] Valid unit passed validation.")
    else:
        logger.error(f"[FAILURE] Valid unit returned errors: {results}")

    # 4. Test Field Existence Rule (Failure)
    invalid_unit = {
        "name": "Broken Scout",
        # Missing tier, armor, speed
    }
    results = auditor.validate_entity("unit_2", "unit", invalid_unit, "u1", 1)
    if any(r['message'].startswith("Missing required field") for r in results):
        logger.info("[SUCCESS] Invalid unit correctly flagged for missing fields.")
    else:
        logger.error(f"[FAILURE] Invalid unit did NOT flag missing fields: {results}")

    # 5. Test Reference Integrity Rule (Success)
    valid_ref_unit = {
        "name": "Capital Ship",
        "tier": 3,
        "armor": 500,
        "speed": 10,
        "required_tech": ["warp_drive"]
    }
    results = auditor.validate_entity("unit_3", "unit", valid_ref_unit, "u1", 1)
    if not results:
        logger.info("[SUCCESS] Valid reference unit passed validation.")
    else:
        logger.error(f"[FAILURE] Valid reference unit returned errors: {results}")

    # 6. Test Reference Integrity Rule (Failure)
    invalid_ref_unit = {
        "name": "Ghost Ship",
        "tier": 3,
        "armor": 500,
        "speed": 10,
        "required_tech": ["non_existent_tech"]
    }
    results = auditor.validate_entity("unit_4", "unit", invalid_ref_unit, "u1", 1)
    if any("Invalid Tech Reference" in r['message'] for r in results):
        logger.info("[SUCCESS] Invalid reference correctly flagged.")
    else:
        logger.error(f"[FAILURE] Invalid reference did NOT flag error: {results}")

if __name__ == "__main__":
    verify_auditor()
