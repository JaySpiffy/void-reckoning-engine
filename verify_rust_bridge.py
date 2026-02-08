import void_reckoning_bridge
import time

print(f"Successfully imported void_reckoning_bridge module: {void_reckoning_bridge}")

try:
    pf = void_reckoning_bridge.RustPathfinder()
    print("Created RustPathfinder instance")
    
    pf.add_node("Sol")
    pf.add_node("Alpha Centauri")
    pf.add_edge("Sol", "Alpha Centauri", 4.3)
    
    path, cost = pf.find_path("Sol", "Alpha Centauri")
    print(f"Path found: {path}, Cost: {cost}")
    
    import math
    assert path == ["Sol", "Alpha Centauri"]
    assert math.isclose(cost, 4.3, rel_tol=1e-5)
    print("VERIFICATION SUCCESS")

except Exception as e:
    print(f"VERIFICATION FAILED: {e}")
