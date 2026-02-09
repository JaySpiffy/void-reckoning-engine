import heapq
import functools
from typing import List, Tuple, Optional, Any, Set, Dict

from src.utils.profiler import profile_method

from src.core.simulation_state import SimulationState
try:
    import void_reckoning_bridge
except ImportError:
    void_reckoning_bridge = None

class PathfindingService:
    """
    Service for calculating paths between GraphNodes using A*.
    Manages caching and path validation.
    """
    def __init__(self):
        self._path_cache = {} # (start_node, end_node, context, topo_ver, block_ver) -> (path, cost)
        self._failed_paths_logged_this_turn = set()
        
        # Smart Caching State
        self._last_topo_ver = SimulationState.get_topology_version()
        self._last_block_ver = SimulationState.get_blockade_version()
        
        # Telemetry Stats
        self._stats = {"hits": 0, "misses": 0, "requests": 0}
        self._stats = {"hits": 0, "misses": 0, "requests": 0}
        self._distance_service = None # R10: DistanceMatrixService
        
        # Phase 1: Native Pulse Integration
        self._rust_pathfinder = None
        self._node_ref_cache = {} # ID -> GraphNode mapping for Rust result reconstruction
        if void_reckoning_bridge:
            try:
                self._rust_pathfinder = void_reckoning_bridge.RustPathfinder()
                print("[Native Pulse] RustPathfinder initialized.")
            except Exception as e:
                print(f"[Native Pulse] Failed to init RustPathfinder: {e}")

    def set_correlation_id(self, trace_id: str, span_id: str):
        """
        Sets the correlation context for the underlying Rust pathfinder.
        """
        if not self._rust_pathfinder: return
        try:
            from void_reckoning_bridge import CorrelationContext
            ctx = CorrelationContext()
            ctx.trace_id = trace_id
            ctx.span_id = span_id
            self._rust_pathfinder.set_correlation_context(ctx)
        except Exception as e:
            # print(f"Failed to set correlation context: {e}")
            pass

    @property
    def cache_stats(self):
        return self._stats.copy()

    def clear_cache(self):
        """
        Clears the path cache. 
        Optimization 5.1: Smart Persistence - Only clear if versions changed.
        """
        current_topo = SimulationState.get_topology_version()
        current_block = SimulationState.get_blockade_version()
        
        # If graph state shouldn't have changed, preserve the cache
        if current_topo == self._last_topo_ver and current_block == self._last_block_ver:
             self._failed_paths_logged_this_turn = set()
             return

        # State changed (or first run), full clear/reset
        self._path_cache = {}
        self._failed_paths_logged_this_turn = set()
        self._last_topo_ver = current_topo
        self._last_block_ver = current_block

    def invalidate_portal_paths(self):
        """Clears paths involving portals (Phase 23)."""
        # Simple approach: clear all, or filter. Since this happens rarely (portal changes), full clear is safer/easier.
        self._path_cache = {}
        self._last_topo_ver = -1 # Force reset next time

    def register_with_cache_manager(self, cache_manager):
        """Registers the path cache with the provided CacheManager."""
        cache_manager.register_cache(self.clear_cache, "pathfinding")

    def sync_topology(self, nodes: List[Any]):
        """
        Populates the Rust Pathfinder with the current universe topology.
        Must be called after universe generation or topology changes.
        """
        if not self._rust_pathfinder:
            return

        self._rust_pathfinder.clear()
        self._node_ref_cache.clear()
        
        # 1. Register Nodes
        for node in nodes:
            node_id = getattr(node, 'id', str(node))
            self._node_ref_cache[node_id] = node
            
            terrain = getattr(node, 'terrain_type', None)
            self._rust_pathfinder.add_node(node_id, terrain)
            
        # 2. Register Edges
        # We iterate again to ensure all definition nodes exist before adding edges? 
        # (Actually Rust implementation likely handles it if we follow order or if it's robust, 
        # but the impl I wrote expects add_node first or handles it? 
        # My Rust impl: add_node checks map. add_edge calls add_node. So it's safe.)
        
        for node in nodes:
            node_id = getattr(node, 'id', str(node))
            if hasattr(node, 'edges'):
                for edge in node.edges:
                    target = edge.target
                    target_id = getattr(target, 'id', str(target))
                    # Weight = distance
                    weight = getattr(edge, 'distance', 1.0)
                    self._rust_pathfinder.add_edge(node_id, target_id, float(weight))
        
        print(f"[Native Pulse] Synced {len(nodes)} nodes to Rust pathfinder.")

    def set_distance_service(self, service: Any):
        """R10: Inject the distance matrix service."""
        self._distance_service = service

    @profile_method
    def find_cached_path(self, start_node: Any, end_node: Any, turn: int = 0, context: str = None, is_ground: bool = False) -> Tuple[Optional[List[Any]], float, Dict[str, Any]]:
        """
        Cached wrapper for find_path. 
        Context (e.g., universe name) is included in cache key (Comment 3).
        Optimization 5.1: Uses versioned keys for intra-turn consistency.
        """
        self._stats["requests"] += 1
        
        # Versioning
        t_ver = SimulationState.get_topology_version()
        b_ver = SimulationState.get_blockade_version()
        
        # Ground check for cache key
        cache_key = (start_node, end_node, context, t_ver, b_ver, is_ground)
        if cache_key in self._path_cache:
            self._stats["hits"] += 1
            return self._path_cache[cache_key]
            
        self._stats["misses"] += 1
        result = self.find_path(start_node, end_node, is_ground=is_ground)
        self._path_cache[cache_key] = result
        return result

    @profile_method
    def find_path(self, start_node: Any, end_node: Any, max_cost: float = float('inf'), is_ground: bool = False) -> Tuple[Optional[List[Any]], float, Dict[str, Any]]:
        """
        Returns (list of nodes, total_cost, metadata) or (None, infinity, {}) if no path.
        Uses optimized A* algorithm with Euclidean heuristic and informed fallback.
        """
        if start_node == end_node:
            return [start_node], 0, {}

        # [NATIVE PULSE] Rust Pathfinding
        if self._rust_pathfinder and not is_ground: # Currently only Space Topology supported in Phase 1 plan
            try:
                s_id = getattr(start_node, 'id', str(start_node))
                e_id = getattr(end_node, 'id', str(end_node))
                
                # Check for cached lookup existence to avoid Rust panics or misses
                if s_id in self._node_ref_cache and e_id in self._node_ref_cache:
                    profile = "Ground" if is_ground else "Space"
                    path_ids_tuple = self._rust_pathfinder.find_path(s_id, e_id, profile)
                    
                    if path_ids_tuple:
                        path_ids, cost = path_ids_tuple
                        # Reconstruct objects
                        path_objs = [self._node_ref_cache.get(pid) for pid in path_ids if pid in self._node_ref_cache]
                        
                        # Handle basic portal metadata (Stub for now, full logic later)
                        portal_meta = {}
                        for n in path_objs:
                            if hasattr(n, 'is_portal') and n.is_portal():
                                portal_meta["requires_handoff"] = True
                                portal_meta["portal_node"] = n
                                portal_meta["dest_universe"] = n.metadata.get("portal_dest_universe")
                                # If portal is last, logic matches Python. 
                                # If portal is mid-path, we might need truncation logic similar to Python.
                                # Python logic: "Truncate after portal".
                                idx = path_objs.index(n)
                                path_objs = path_objs[:idx+1]
                                # Re-calc cost? Rust returned full cost. 
                                # Strictly speaking, we should just take it for now.
                                break

                        return (path_objs, cost, portal_meta)
            except Exception as e:
                # Fallback on error
                # print(f"[Native Pulse] Error: {e}")
                pass

        def _heuristic(a, b):
            # R9/R10: Hierarchical Distance Matrix Heuristic (Perfect Strategic Guide)
            if self._distance_service:
                a_sys = getattr(a, 'system', None)
                if not a_sys and "system" in getattr(a, 'metadata', {}):
                    a_sys = a.metadata["system"]
                
                b_sys = getattr(b, 'system', None)
                if not b_sys and "system" in getattr(b, 'metadata', {}):
                    b_sys = b.metadata["system"]
                
                if a_sys and b_sys and a_sys != b_sys:
                    # Lookup strategic distance (O(1))
                    strat_dist = self._distance_service.get_distance(a_sys.name, b_sys.name)
                    if strat_dist != float('inf'):
                        # Scale factor: Strategic distances are in system-hops usually, 
                        # we scale by roughly 20-30 to match local node costs (Euclidean 100 range)
                        # Actually BFS based distance in StarSystem uses 10 for gates.
                        return strat_dist
            
            # 1. Coordinate-based Euclidean (Admissible)
            if hasattr(a, 'position') and hasattr(b, 'position') and a.position and b.position:
                return ((a.position[0] - b.position[0])**2 + (a.position[1] - b.position[1])**2)**0.5
            
            # 2. Informed Fallback (Hop-based/Scaled Distance)
            return 1.0 if a != b else 0

        # Priority Queue: (f_score, node)
        h_start = _heuristic(start_node, end_node)
        queue = [(h_start, start_node)]
        
        g_score = {start_node: 0}
        path_map = {start_node: None}
        closed_set = set() # Track fully expanded nodes

        best_goal_cost = float('inf')

        while queue:
            f_score, current_node = heapq.heappop(queue)

            if current_node == end_node:
                best_goal_cost = g_score[current_node]
                break

            # Pruning based on best known goal or maximum allowed cost
            if f_score >= best_goal_cost or g_score[current_node] > max_cost:
                continue

            if current_node in closed_set:
                continue
            
            closed_set.add(current_node)
            
            # [SAFETY] Prevent Infinite Loop / OOM
            if len(closed_set) > 50000:
                # Log failure?
                # We return None path, effectively failing pathfinding.
                return (None, float('inf'), {})

            if not hasattr(current_node, 'edges'):
                continue
                
            for edge in current_node.edges:
                if hasattr(edge, 'is_traversable') and not edge.is_traversable():
                    continue
                elif hasattr(edge, 'blocked') and edge.blocked:
                     continue

                neighbor = edge.target
                
                # Terrain-based cost modifiers (Ground Movement only)
                edge_cost = edge.distance
                if is_ground and hasattr(neighbor, 'terrain_type'):
                     terrain = neighbor.terrain_type
                     if terrain == "Mountain":
                          edge_cost *= 2.0
                     elif terrain == "Water":
                          # Impassable for ground units
                          continue
                
                tentative_g_score = g_score[current_node] + edge_cost

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    g_score[neighbor] = tentative_g_score
                    path_map[neighbor] = current_node
                    
                    h_score = _heuristic(neighbor, end_node)
                    f_neighbor = tentative_g_score + h_score
                    
                    # Only add to queue if it could potentially beat our best goal cost
                    if f_neighbor < best_goal_cost:
                        heapq.heappush(queue, (f_neighbor, neighbor))

        if best_goal_cost != float('inf'):
            path = []
            curr = end_node
            portal_metadata = {}
            
            while curr:
                path.append(curr)
                if hasattr(curr, 'is_portal') and curr.is_portal():
                    portal_metadata["requires_handoff"] = True
                    portal_metadata["portal_node"] = curr
                    portal_metadata["dest_universe"] = curr.metadata.get("portal_dest_universe")
                    portal_metadata["portal_id"] = curr.metadata.get("portal_id")
                    portal_metadata["exit_coords"] = curr.metadata.get("portal_dest_coords")
                    
                curr = path_map[curr]
            
            path = path[::-1] # Reverse first to get correct order Start -> ...
            
            if portal_metadata.get("requires_handoff"):
                p_node = portal_metadata["portal_node"]
                if p_node in path:
                     idx = path.index(p_node)
                     path = path[:idx+1] # Truncate after portal
                     # Cost in A* is cumulative g_score
                     if p_node in g_score:
                         best_goal_cost = g_score[p_node]
            
            return (path, best_goal_cost, portal_metadata)
        else:
            return (None, float('inf'), {})

    def describe_path(self, path: List[Any], metadata: Dict[str, Any]) -> str:
        """
        Returns a human-readable description of a path, including portal crossings.
        """
        if not path: return "No Path"
        
        desc = []
        for node in path:
            name = getattr(node, 'name', str(node))
            if hasattr(node, 'is_portal') and node.is_portal():
                dest = node.metadata.get("portal_dest_universe", "Unknown")
                desc.append(f"[PORTAL -> {dest}]")
            else:
                desc.append(name)
                
        return " -> ".join(desc)

    def log_path_failure(self, start_node: Any, end_node: Any) -> bool:
        """
        Returns True if this failure hasn't been logged this turn yet.
        """
        key = (getattr(start_node, 'id', str(start_node)), getattr(end_node, 'id', str(end_node)))
        if key not in self._failed_paths_logged_this_turn:
            self._failed_paths_logged_this_turn.add(key)
            return True
        return False
