
import time
import json
import random
from src.utils.rust_auditor import RustAuditorWrapper

def benchmark_auditor():
    print("=== Rust Auditor Benchmark ===")
    
    auditor = RustAuditorWrapper()
    if not auditor.initialize():
        print("Failed to initialize auditor.")
        return

    # 1. Setup Registries
    print("Loading registries...")
    tech_data = {f"tech_{i}": {"name": f"Tech {i}", "tier": 1, "cost": 100} for i in range(100)}
    buildings_data = {f"bldg_{i}": {"name": f"Building {i}", "tier": 1, "cost": 100} for i in range(100)}
    
    t0 = time.time()
    auditor.load_registry("technology", tech_data)
    auditor.load_registry("buildings", buildings_data)
    print(f"Registry Load Time: {time.time() - t0:.4f}s")

    # 2. Generate Data
    NUM_ENTITIES = 100000
    print(f"Generating {NUM_ENTITIES} entities...")
    
    entities = []
    for i in range(NUM_ENTITIES):
        # Mix of valid and invalid
        is_valid = random.random() > 0.1 # 90% valid
        
        if is_valid:
            entities.append({
                "id": f"unit_{i}",
                "type": "unit",
                "data": {
                    "name": f"Unit {i}",
                    "tier": 1,
                    "armor": 100,
                    "speed": 10,
                    "required_tech": ["tech_1"]
                }
            })
        else:
            # Missing fields or invalid ref
            entities.append({
                "id": f"unit_{i}",
                "type": "unit",
                "data": {
                    "name": f"Broken Unit {i}",
                    # Missing fields
                    "required_tech": ["non_existent"]
                }
            })

    # 3. Benchmark Validation
    print("Starting validation...")
    start_time = time.time()
    
    violations = 0
    # Batch processing simulation (iterating one by one as the wrapper is currently 1-by-1)
    # The wrapper exposes validate_entity. 
    # If we had a batch API it would be faster, but let's test the overhead of the call too.
    
    for ent in entities:
        res = auditor.validate_entity(ent["id"], ent["type"], ent["data"], "univ_bench", 100)
        if res:
            violations += 1
            
    total_time = time.time() - start_time
    tps = NUM_ENTITIES / total_time
    
    print(f"\nResults:")
    print(f"  Processed: {NUM_ENTITIES}")
    print(f"  Violations Found: {violations}")
    print(f"  Total Time: {total_time:.4f}s")
    print(f"  Throughput: {tps:.2f} entities/sec")
    
    # Python Baseline Comparison (Approximation)
    # A pure python validator usually runs at ~5-10k entities/sec with strict schema checks
    print(f"\nEstimated Python Baseline: ~5,000 - 10,000/sec")
    print(f"Speedup Factor: ~{tps/7500:.1f}x")

if __name__ == "__main__":
    benchmark_auditor()
