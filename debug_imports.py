
import void_reckoning_bridge
print("Dir(void_reckoning_bridge):")
print(dir(void_reckoning_bridge))

if hasattr(void_reckoning_bridge, 'observability'):
    print("\nDir(void_reckoning_bridge.observability):")
    print(dir(void_reckoning_bridge.observability))
else:
    print("\n'observability' not found in void_reckoning_bridge")
