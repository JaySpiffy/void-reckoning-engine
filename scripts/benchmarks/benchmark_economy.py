import sys
import os
import time
import random
import cProfile
import pstats
from io import StringIO

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.utils.rust_economy import RustEconomyWrapper

def benchmark_economy():
    print("="*60)
    print("RUST ECONOMY ENGINE BENCHMARK (10k+ Entities)")
    print("="*60)

    # 1. Setup
    economy = RustEconomyWrapper()
    economy.set_rules(
        orbit_discount=0.5,
        garrison_discount=0.25,
        navy_penalty_ratio=4,
        navy_penalty_rate=0.05
    )
    
    FACTION_COUNT = 50
    NODES_PER_FACTION = 200 # Total 10,000 Nodes
    TRADE_ROUTES = 5000
    
    factions = [f"Faction_{i}" for i in range(FACTION_COUNT)]
    node_types = ["Planet", "Station", "Station", "Station"] # Weighted towards Stations
    
    print(f"Generating {FACTION_COUNT * NODES_PER_FACTION} economic nodes...")
    
    start_gen = time.time()
    for f in factions:
        for i in range(NODES_PER_FACTION):
            node_id = f"{f}_Node_{i}"
            n_type = random.choice(node_types)
            
            # Randomized Income/Upkeep
            income = {
                "credits": random.randint(0, 100),
                "minerals": random.randint(0, 50),
                "energy": random.randint(0, 50), 
                "research": random.randint(0, 10)
            }
            
            upkeep = {
                "credits": random.randint(0, 20),
                "energy": random.randint(0, 10)
            }
            
            mods = []
            if random.random() > 0.8:
                mods.append({"name": "EfficientManagement", "multiplier": 1.1})
                
            economy.add_node(node_id, f, n_type, income, upkeep, efficiency=1.0, modifiers=mods)
            
    gen_time = time.time() - start_gen
    print(f"Generation Complete: {gen_time:.4f}s")
    
    # 2. Add Trade Routes (Simulated)
    print(f"Generating {TRADE_ROUTES} trade routes...")
    for _ in range(TRADE_ROUTES):
        f = random.choice(factions)
        n1 = f"{f}_Node_{random.randint(0, NODES_PER_FACTION-1)}"
        n2 = f"{f}_Node_{random.randint(0, NODES_PER_FACTION-1)}"
        if n1 != n2:
            economy.add_trade_route(n1, n2, {
                "credits": random.randint(5, 50),
                "minerals": 0,
                "energy": 0,
                "research": 0
            })
            
    # 3. Benchmark Calculation
    print("\nStarting Performance Test...")
    
    # Profile the calculation
    pr = cProfile.Profile()
    pr.enable()
    
    start_calc = time.time()
    
    # Run the big calculation (process_all)
    # Note: We aren't testing calculate_trade(pathfinder) here as that requires the pathfinding graph setup
    # We are testing the core economic aggregation and modifier logic.
    reports = economy.get_all_reports()
    
    end_calc = time.time()
    pr.disable()
    
    duration = end_calc - start_calc
    
    print(f"Calculation Time: {duration:.4f}s")
    print(f"Entities Processed: {len(reports)} Factions, {FACTION_COUNT * NODES_PER_FACTION} Nodes")
    print("-" * 60)
    
    # 4. Verify Results (Sanity Check)
    total_gdp = sum(r["total_income"]["credits"] for r in reports.values())
    print(f"Total Galactic GDP (Credits): {total_gdp:,.2f}")
    
    # 5. Output Stats
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    print("\nTop 10 Functions by Execution Time:")
    print(s.getvalue())

    # Success Criteria
    if duration < 0.5: # 500ms budget for economy phase
        print("RESULT: PASS - Rust Engine is blazing fast!")
    elif duration < 1.0:
        print("RESULT: PASS - Acceptable performance.")
    else:
        print("RESULT: FAIL - Too slow for 10k entities.")

if __name__ == "__main__":
    benchmark_economy()
