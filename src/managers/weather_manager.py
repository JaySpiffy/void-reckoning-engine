import random
from src.config import logging_config

class FluxStormManager:
    """
    Phase 15.5: Manages Graph Edge stability and blocking hazards.
    """
    def __init__(self, engine):
        self.engine = engine
        self.edges = [] # List of all GraphEdge objects in the universe
        self.active_storms = {} # {edge_id: turns_remaining}
        
    def collect_edges(self):
        """Scans the galaxy to index all edges for weather simulation."""
        self.edges = []
        seen_links = set()
        
        # 1. System Internal Edges
        for s in self.engine.systems:
            for node in getattr(s, "nodes", []):
                # FILTER: Only track edges connected to Flux Points for Storms
                for edge in node.edges:
                    # If this is a Flux Route (connected to FluxPoint), track it.
                    if edge.source.type == "FluxPoint" or edge.target.type == "FluxPoint":
                        # Deduplication Logic: Treat A->B and B->A as the same "Link" for weather purposes.
                        link_id = tuple(sorted((id(edge.source), id(edge.target))))
                        if link_id in seen_links:
                            continue
                            
                        seen_links.add(link_id)
                        self.edges.append(edge)

        if self.engine.logger:
            self.engine.logger.environment(f"FluxStormManager monitoring {len(self.edges)} navigational vectors.")

    def update_storms(self):
        """Runs the weather cycle. Manages storm lifecycle (Spawn -> Decay -> Expire)."""
        raw = getattr(self.engine.game_config, 'raw_config', {})
        weather_cfg = raw.get("mechanics", {}).get("weather_config", {})
        
        # Config
        # [TUNING] Dynamic Cap Calculation
        max_storm_pct = weather_cfg.get("max_storm_percentage", 5.0)
        
        # Calculate max storms based on total edges
        total_edges = len(self.edges)
        max_storms = int(total_edges * (max_storm_pct / 100.0))
        
        # [SAFETY] Hard Cap to prevent paralysis on large maps
        HARD_CAP = 50 # Never more than 50 storms, regardless of percentage
        if max_storms > HARD_CAP:
            max_storms = HARD_CAP
            
        if max_storms < 1 and max_storm_pct > 0: max_storms = 1

        min_dur = weather_cfg.get("min_duration", 5)
        max_dur = weather_cfg.get("max_duration", 20)
        storm_chance = weather_cfg.get("storm_chance_per_turn", 0.01)
        
        expired = []
        
        # 1. Decay Active Storms
        for edge_id, turns in self.active_storms.items():
            self.active_storms[edge_id] -= 1
            if self.active_storms[edge_id] <= 0:
                expired.append(edge_id)
                
        # 2. Process Expirations
        for edge_id in expired:
            del self.active_storms[edge_id]
            for edge in self.edges:
                if id(edge) == edge_id:
                    edge.blocked = False
                    edge.stability = 1.0 # Reset to stable
                    # [OPTIMIZATION] Removed Individual Clear Log to reduce spam
                    break
                    
        # 3. Spawn New Storms
        current_count = len(self.active_storms)
        open_slots = max_storms - current_count
        
        if open_slots > 0:
            # Get all valid candidates (unblocked edges)
            candidates = [e for e in self.edges if not e.blocked and id(e) not in self.active_storms]
            
            if candidates:
                random.shuffle(candidates)
                spawns_this_turn = 0
                
                for target in candidates:
                    if spawns_this_turn >= open_slots:
                        break
                        
                    if random.random() < storm_chance:
                        target.blocked = True
                        target.stability = 0.0
                        duration = random.randint(min_dur, max_dur)
                        self.active_storms[id(target)] = duration
                        target._storm_dur_cached = duration
                        
                        # [OPTIMIZATION] Removed Individual Eruption Log to reduce spam
                        # Only log if specifically debugging weather
                        if logging_config.LOGGING_FEATURES.get('weather_effects_tracing', False):
                             if self.engine.logger:
                                 self.engine.logger.environment(f"[STORM] {target.source.name}->{target.target.name} ({duration}t)")
                        
                        spawns_this_turn += 1
                        current_count += 1

        # Summary Log Only
        if self.engine.logger:
             # Periodically log storm summary
             if self.engine.turn_counter % 5 == 0:
                 self.engine.logger.environment(f"[WEATHER] Active Flux Storms: {len(self.active_storms)}/{max_storms} (Total nav-vectors: {len(self.edges)})")
