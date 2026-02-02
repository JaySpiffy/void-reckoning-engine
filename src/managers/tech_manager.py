import os
import logging
import json
import re
from typing import Optional, List, Dict, Any
import src.core.config as config
from src.factories.tech_factory import ProceduralTechGenerator

class TechManager:
    """
    Manages tech trees, dependencies, and the new 'Card-Based' research system.
    """
    def __init__(self, tech_dir: Optional[str] = None, game_config: Optional[dict] = None):
        """
        Initializes the TechManager and loads all tech trees.
        Args:
            tech_dir: Optional override for technology directory (Dependency Injection)
            game_config: Configuration dictionary/object
        """
        self.tech_dir = tech_dir
        self.config = game_config or {}
        
        # Determine Cost Multiplier
        multiplier = 1.0
        if hasattr(self.config, "tech_cost_multiplier"):
             multiplier = self.config.tech_cost_multiplier
        elif isinstance(self.config, dict):
             multiplier = self.config.get("tech_cost_multiplier", 1.0)
        self.cost_multiplier = float(multiplier)
        self.logger = logging.getLogger("TechManager")

        self.faction_tech_trees = {} 
        self.hybrid_tech_trees = {} # Store cross-universe tech data
        self.tech_effects = {} # {tech_id: [parsed_effects]}
        
        # [NEW] Research State
        # {faction_id: {"current_project": str, "progress": 0.0, "drawn_cards": []}}
        self.research_state = {} 

        self.load_tech_trees()
        self.load_hybrid_tech_trees()
        
    def apply_procedural_evolution(self, universe_id: str):
        """
        Mutates the loaded tech trees based on the universe ID (deterministic).
        Implements 'Self-Evolving Tech Trees'.
        """
        print(f"[TechManager] Applying Procedural Evolution for Universe: {universe_id}")
        generator = ProceduralTechGenerator(universe_id)
        
        for faction, tree in self.faction_tech_trees.items():
            # Evolve the tree
            result = generator.evolve_tree(tree)
            
            # Update the in-memory tree
            tree["techs"] = result["techs"]
            tree["units"] = result["units"]
            
        print(f"[TechManager] Evolution Complete.")

    def draw_research_cards(self, faction: Any, num_cards: int = 3) -> List[str]:
        """
        Draws X random available techs from the faction's tree.
        Respects prerequisites.
        Adds weighting to prioritize 'Unlock' techs (Weapons/Hulls).
        """
        # Support both ID string and Faction Object
        if isinstance(faction, str):
            faction_id = faction
            # We need the actual faction object to check unlocked_techs
            # For now return empty if we can't access unlocked_techs
            return [] 
        else:
            faction_id = faction.name.replace(" ", "_").lower()
            
        tree = self.faction_tech_trees.get(faction_id)
        if not tree:
            # Fallback to default if custom tree not found
            tree = self.faction_tech_trees.get("default")
            if not tree: return []

        available = []
        researched = set(faction.unlocked_techs)
        
        # Check prerequisites
        for tech_id, cost in tree["techs"].items():
            if tech_id in researched: continue
            
            # Check prerequisites
            reqs = tree.get("prerequisites", {}).get(tech_id, [])
            if not reqs:
                available.append(tech_id)
            else:
                # ALL prereqs must be met
                if all(r in researched for r in reqs):
                    available.append(tech_id)
        
        if not available: return []
        
        # [WEIGHTING LOGIC]
        # User requested: "make sure (unlock) tecs come up not just random ones"
        weights = []
        for t in available:
            w = 1.0
            if "Unlock" in t: 
                w = 10.0 # High priority for Unlocks
            if "Tech_Unlock_Titan" in t:
                w = 50.0 # Legendary Priority
            weights.append(w)
            
        # If pool < num_cards, return all.
        if len(available) <= num_cards:
            drawn = available
        else:
            # Weighted pull without replacement is tricky in pure random module.
            # Simpler: Shuffle with weights? Or iterative weighted choice.
            drawn = []
            pool = list(zip(available, weights))
            
            for _ in range(num_cards):
                if not pool: break
                # Extract for choices
                choices = [p[0] for p in pool]
                wts = [p[1] for p in pool]
                
                import random
                picked = random.choices(choices, weights=wts, k=1)[0]
                drawn.append(picked)
                
                # Remove from pool
                pool = [p for p in pool if p[0] != picked]

        # Update State
        if faction_id not in self.research_state:
            self.research_state[faction_id] = {"current_project": None, "progress": 0.0, "drawn_cards": []}
            
        self.research_state[faction_id]["drawn_cards"] = drawn
        self.logger.info(f"[Research] {faction_id} drew cards: {drawn}")
        return drawn

    def select_research_project(self, faction: Any, tech_id: str):
        """
        Locks in a research project from the hand.
        """
        faction_id = faction.name
        if faction_id not in self.research_state:
             self.research_state[faction_id] = {"current_project": None, "progress": 0.0, "drawn_cards": []}
             
        state = self.research_state[faction_id]
        
        # Validation: Must be in drawn cards OR (Debug bypass)
        if tech_id not in state["drawn_cards"]:
            self.logger.warning(f"[Research] {faction_id} tried to pick {tech_id} which was NOT in hand {state['drawn_cards']}. Allowing for now (debug).")
            
        state["current_project"] = tech_id
        state["progress"] = 0.0
        
        # Update Faction Object State as well (if we want to mirror it)
        faction.active_research = tech_id
        
        self.logger.info(f"[Research] {faction_id} started researching: {tech_id}")

    def _get_researched_techs(self, faction_id: str) -> List[str]:
        # Deprecated / Unused now that we use faction object
        return []

    def upgrade_weapon(self, faction_name: str, weapon_id: str, arsenal: Dict) -> Optional[Dict]:
        """
        Researches an improvement for a specific weapon (Mark II, III, etc.).
        Returns the new weapon data or None if failed.
        """
        original = arsenal.get(weapon_id)
        if not original: return None
        
        # Determine new Mark
        current_name = original.get("name", "Unknown")
        import re
        match = re.search(r"Mark ([IVX]+|[\d]+)", current_name)
        if match:
             # Logic to increment roman numeral or int? 
             # Let's simple append " Mk II" if not present, or " Mk III" etc.
             # Simplified: Just append " (+)" for now or handled via ID
             new_name = current_name + " (+)"
             new_id = weapon_id + "_plus"
        else:
             new_name = current_name + " Mk II"
             new_id = weapon_id + "_mk2"
             
        if new_id in arsenal: return None # Already exists
        
        # Clone and Buff
        import copy
        new_weapon = copy.deepcopy(original)
        new_weapon["id"] = new_id
        new_weapon["name"] = new_name
        
        stats = new_weapon.get("stats", {})
        
        # Buff Logic (+10% Power, +5% Range, +15% Cost)
        if "power" in stats: stats["power"] = int(stats["power"] * 1.10)
        if "range" in stats: stats["range"] = int(stats["range"] * 1.05)
        # Cost check? Usually processed at ship design level based on components.
        # But if weapon has inherent cost:
        if "cost" in new_weapon: new_weapon["cost"] = int(new_weapon.get("cost", 100) * 1.15)
        
        arsenal[new_id] = new_weapon
        print(f"[Research] {faction_name} upgraded {current_name} to {new_name}!")
        return new_weapon
        
    def load_tech_trees(self):
        # Updated to new path 04_Technology
        tech_dir = self.tech_dir if self.tech_dir else config.TECH_DIR
        if not os.path.exists(tech_dir):
            return

        generic_techs = {"units": {}, "techs": {}, "prerequisites": {}}
        
        # --- Stage 1: Load from technology_registry.json if exists ---
        registry_path = os.path.join(tech_dir, "technology_registry.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r', encoding='utf-8') as rf:
                    reg_data = json.load(rf)
                
                for t_id, t_data in reg_data.items():
                    f = t_data.get("faction", "Global").lower()
                    
                    if f not in self.faction_tech_trees:
                        self.faction_tech_trees[f] = {"units": {}, "techs": {}, "prerequisites": {}}
                    
                    target = generic_techs if f == "global" else self.faction_tech_trees[f]
                    
                    # Register Tech
                    base_cost = t_data.get("cost", 1000)
                    target["techs"][t_id] = int(base_cost * self.cost_multiplier)
                    
                    # Register Unlocks
                    for ship in t_data.get("unlocks_ships", []):
                        target["units"][ship] = t_id
                    for build in t_data.get("unlocks_buildings", []):
                        target["units"][build] = t_id
                        
            except Exception as e:
                print(f"[ERROR] TechManager failed to load registry: {e}")

        # --- Stage 2: Fallback/Supplemental MD Parsing ---

        for filename in os.listdir(tech_dir):
            if filename.endswith("_tech_tree.md") or filename.endswith("_tech.md"):
                if filename.endswith("_tech_tree.md"):
                     faction_raw = filename.split("_tech_tree.md")[0]
                else:
                     faction_raw = filename.split("_tech.md")[0]
                faction = faction_raw.lower()
                
                # Check for Generic Tree (fortification)
                is_generic = (faction == "fortification")
                
                if is_generic:
                    target_dict = generic_techs
                else:
                    # Fix: Do NOT overwrite existing tree if loaded from Registry
                    if faction not in self.faction_tech_trees:
                         self.faction_tech_trees[faction] = {"units": {}, "techs": {}, "prerequisites": {}}
                    target_dict = self.faction_tech_trees[faction]
                
                with open(os.path.join(tech_dir, filename), 'r', encoding='utf-8') as f:
                    last_tech = None
                    for line in f:
                        line_strip = line.strip()
                        
                        # CRITICAL: Skip metadata keys that look like bullet points (but NOT Unlocks/Effects which we parse)
                        if any(prop in line for p in ["Cost:", "Description:", "Name:", "Prerequisites:"] for prop in [f"**{p}**", f"- {p}", f"* {p}", p]):
                            continue
                        # --- Mermaid Parsing ---
                        if "-->" in line:
                            parts = line.split("-->")
                            parent_raw = parts[0].strip()
                            child_raw = parts[1].strip()
                            
                            if "[" in parent_raw: parent_name = parent_raw.split("[")[1].split("]")[0]
                            else: parent_name = parent_raw

                            # Fix for Mermaid IDs like Headquarters___None
                            if "Headquarters___None" in parent_name:
                                parent_name = "Headquarters"
                            
                            # Clean up Labels "Headquarters / None"
                            if "/" in parent_name:
                                parent_name = parent_name.split("/")[0].strip()
                                
                            if "(" in child_raw:
                                content = child_raw.split("(")[1].split(")")[0]
                                unit_name = content.split("[")[0].strip() if "[" in content else content.strip()
                            else: unit_name = child_raw
                                
                            if not is_generic and faction_raw:
                                parent_name = f"Tech_{faction_raw}_{parent_name}"
                                
                            target_dict["units"][unit_name] = parent_name
                            if parent_name not in target_dict["techs"]:
                                target_dict["techs"][parent_name] = int(1000 * self.cost_multiplier) # Default cost with mult
                            last_tech = parent_name
                                
                        # --- Header Parsing (Phase 106.1) ---
                        elif line_strip.startswith("### "):
                            header_name = line_strip.replace("### ", "").strip()
                            if "(" in header_name and ")" in header_name:
                                header_id = header_name.split("(")[1].split(")")[0].strip()
                            else:
                                header_id = header_name
                            
                            # Unify with Registry ID format (Tech_Faction_Name)
                            if not is_generic and faction_raw and header_id:
                                header_id = f"Tech_{faction_raw}_{header_id}"
                            
                            if header_id and header_id not in ["Tier 1", "Tier 2", "Tier 3", "Tier 4"]:
                                # [FIX] Normalize ID to match Registry (spaces to underscores)
                                header_id = header_id.replace(" ", "_")
                                
                                if header_id not in target_dict["techs"]:
                                    target_dict["techs"][header_id] = int(1000 * self.cost_multiplier)
                                last_tech = header_id

                        # --- Bullet List Parsing (Phase 106 + Star Wars Hybrid) ---
                        elif any(line_strip.startswith(p) for p in ["*", "-"]) and ("**" in line or "(" in line):
                            # Skip if it's a known property
                            # We check for several formats: "**Effects:**", "- Effects:", etc.
                            is_property = False
                            for p_key in ["Unlocks:", "Effects:", "Cost:", "Description:", "Prerequisites:", "Name:"]:
                                if f"**{p_key}**" in line or f"* {p_key}" in line or f"- {p_key}" in line or line_strip.startswith(p_key):
                                    is_property = True
                                    break
                            
                            if is_property:
                                if "Unlocks:" in line and last_tech:
                                    try:
                                        # Split by commas and handle multi-unlock
                                        unlock_str = line.split("Unlocks:")[1].strip()
                                        unlocks = [u.strip().strip("[]").replace(".", "") for u in re.split(r'[,;]', unlock_str)]
                                        for u in unlocks:
                                            if u:
                                                target_dict["units"][u] = last_tech
                                    except:
                                        pass
                                
                                if "Effects:" in line and last_tech:
                                    try:
                                        effects_part = line.split("Effects:")[1].strip()
                                        effects = [e.strip().replace("*", "") for e in re.split(r'[,;]', effects_part)]
                                        # Filter out Unlocks from effects strings if they were merged
                                        effects = [e for e in effects if "Unlocks" not in e and "[" not in e]
                                        
                                        self.tech_effects[last_tech] = self.tech_effects.get(last_tech, []) + effects
                                        if hasattr(self, 'logger') and self.logger:
                                            self.logger.info(f"[TechManager] Parsed effects for {last_tech}: {effects}")
                                    except:
                                        pass
                            else:
                                try:
                                    tech_name = line.split("**")[1].strip()
                                    # Check for ID in parentheses like (Pilot_Academy)
                                    tech_id = tech_name
                                    if "(" in line and ")" in line:
                                        tech_id = line.split("(")[1].split(")")[0].strip()
                                    
                                    # [FIX] Normalize ID
                                    tech_id = tech_id.replace(" ", "_")
                                    
                                    if tech_id and tech_id not in target_dict["techs"]:
                                        target_dict["techs"][tech_id] = int(1000 * self.cost_multiplier)
                                    last_tech = tech_id
                                        
                                    # Inline Unlocks?
                                    if "Unlocks:" in line:
                                        unlocks_part = line.split("Unlocks:")[1].strip()
                                        unlocks = [u.strip() for u in re.split(r'[,;]', unlocks_part)]
                                        for u in unlocks:
                                            target_dict["units"][u] = last_tech
                                except:
                                    pass
                                    pass

        # Merge Generic into All
        for f_name, f_tree in self.faction_tech_trees.items():
            f_tree["units"].update(generic_techs["units"])
            f_tree["techs"].update(generic_techs["techs"])

        # Manual Aliasing for Chaos Sub-Factions (Merge instead of Overwrite)
        if "chaos" in self.faction_tech_trees:
            chaos_tree = self.faction_tech_trees["chaos"]
            sub_factions = ["chaos_undivided", "chaos_khorne", "chaos_nurgle", "chaos_tzeentch", "chaos_slaanesh"]
            for sub in sub_factions:
                 if sub not in self.faction_tech_trees:
                     self.faction_tech_trees[sub] = {"units": {}, "techs": {}}
                 
                 # Merge Generic Chaos into Sub-Faction
                 self.faction_tech_trees[sub]["units"].update(chaos_tree["units"])
                 self.faction_tech_trees[sub]["techs"].update(chaos_tree["techs"])
                 if "prerequisites" in chaos_tree:
                     self.faction_tech_trees[sub].setdefault("prerequisites", {}).update(chaos_tree["prerequisites"])

        # --- Stage 3: Load Structured Tech Tree (Edges) ---
        self._load_tech_tree_structure(tech_dir)

        # --- Stage 4: Procedural Expansion (100s of Techs) ---
        generator = ProceduralTechGenerator("void_reckoning")
        
        for f_name, tree in self.faction_tech_trees.items():
            if f_name == "global": continue
            print(f"[TechManager] Procedurally expanding tree for {f_name}...")
            result = generator.generate_procedural_tree(f_name, tree)
            
            # Update Tree
            tree["techs"].update(result["techs"])
            if "prerequisites" in result:
                tree.setdefault("prerequisites", {}).update(result["prerequisites"])
            
            # Store generated effects
            if "effects" in result:
                for t_id, eff_list in result["effects"].items():
                    self.tech_effects[t_id] = self.tech_effects.get(t_id, []) + eff_list

    def _load_tech_tree_structure(self, tech_dir: str):
        """Loads edges from tech_tree.json to enforce prerequisites."""
        tree_path = os.path.join(tech_dir, "tech_tree.json")
        if not os.path.exists(tree_path):
            return

        try:
            with open(tree_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            edges = data.get("edges", [])
            if not edges and "nodes" in data:
                 # Fallback: check if edges are mixed in nodes (unlikely based on analysis but safe)
                 pass

            # We need to map edges to Faction Trees
            # The edges are globally defined but IDs contain Faction Names usually?
            # Actually tech_tree.json seems to correspond to the current universe?
            # Yes, "universes/void_reckoning/technology/tech_tree.json"
            
            # Helper to normalize ID (Tree uses underscores, Registry uses spaces)
            def normalize(tid):
                return tid.replace(" ", "_")

            # Build normalized maps for all loaded techs
            faction_maps = {}
            for f_name, tree in self.faction_tech_trees.items():
                faction_maps[f_name] = {normalize(k): k for k in tree["techs"].keys()}
            
            count = 0
            for edge in edges:
                u_raw = edge.get("from")
                v_raw = edge.get("to")
                if not u_raw or not v_raw: continue
                
                u_norm = normalize(u_raw)
                v_norm = normalize(v_raw)
                
                # Try to find which faction this edge belongs to
                # Heuristic: Check which faction allows this tech
                # Optimally, we extract faction from ID "Tech_Faction_..."
                
                for f_name, normalized_map in faction_maps.items():
                    if u_norm in normalized_map and v_norm in normalized_map:
                        real_u = normalized_map[u_norm]
                        real_v = normalized_map[v_norm]
                        
                        tree = self.faction_tech_trees[f_name]
                        tree.setdefault("prerequisites", {}).setdefault(real_v, []).append(real_u)
                        count += 1
                        # Assumption: Edge applies to one faction (or all if they share IDs?)
                        # Tech IDs are usually unique per faction.
            
            print(f"[TechManager] Loaded {count} prerequisite links from tech_tree.json")

        except Exception as e:
            print(f"[ERROR] Failed to load tech_tree.json: {e}")

    def can_research(self, faction_name: str, tech_id: str, unlocked_techs: List[str] = None, faction_obj = None) -> bool:
        """
        Checks if a faction satisfies the prerequisites for a tech.
        Args:
            faction_name: Name of the faction
            tech_id: Tech ID to check
            unlocked_techs: List of unlocked tech IDs (optional, can use faction_obj)
            faction_obj: Faction instance (optional, for convenience)
        """
        f_lower = faction_name.lower()
        tree = self.faction_tech_trees.get(f_lower)
        if not tree: return False # Unknown faction?
        
        # If tech not in tree, maybe it's synthetic/generic? 
        # If allow unknown techs: return True. But let's imply it must be in tree or passed lists.
        # But wait, EconomyManager injects synthetic techs dynamically.
        # If it's not in the tree's keys, it has no prerequisites => True.
        
        prereqs = tree.get("prerequisites", {}).get(tech_id, [])
        if not prereqs: return True
        
        # Get unlocked list
        if unlocked_techs is None:
            if faction_obj:
                unlocked_techs = faction_obj.unlocked_techs
            else:
                return False # Cannot check without state
        
        for p in prereqs:
            if p not in unlocked_techs:
                return False
                
        # Also check Hybrid Requirements?
        if tech_id in self.hybrid_tech_trees:
             if faction_obj and not self.is_hybrid_tech_available(faction_obj, tech_id):
                 return False
                 
        return True

    def load_hybrid_tech_trees(self):
        """Scans hybrid_tech directories for cross-universe and syncretic tech."""
        scan_dirs = [os.path.join("universes", "base", "hybrid_tech")]
        
        # Add Active Universe specific hybrid techs if configured
        active_universe = getattr(config, 'ACTIVE_UNIVERSE', None)
        if active_universe:
            scan_dirs.append(os.path.join("universes", active_universe, "technology", "hybrid_tech"))

        for hybrid_dir in scan_dirs:
            if not os.path.exists(hybrid_dir):
                if "base" in hybrid_dir:
                    os.makedirs(hybrid_dir, exist_ok=True)
                continue

            for filename in os.listdir(hybrid_dir):
                if filename.endswith(".md"):
                    filepath = os.path.join(hybrid_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extract PARSER_DATA JSON block
                        if "PARSER_DATA" in content:
                            json_str = content.split("PARSER_DATA")[1].split("```json")[1].split("```")[0].strip()
                            tech_data = json.loads(json_str)
                            tech_id = tech_data.get("tech_id")
                            if tech_id:
                                self.hybrid_tech_trees[tech_id] = tech_data
                    except Exception as e:
                        print(f"[TechManager] Error parsing hybrid tech {filename}: {e}")

    def get_required_tech_for_unit(self, faction: str, unit_name: str) -> Optional[str]:
        """Returns the tech ID required for a unit, if any."""
        f_lower = faction.lower()
        if f_lower in self.faction_tech_trees:
            return self.faction_tech_trees[f_lower]["units"].get(unit_name)
        return None

    def get_hybrid_tech_requirements(self, tech_id: str) -> dict:
        """Returns requirement dict for a hybrid tech."""
        tech = self.hybrid_tech_trees.get(tech_id)
        if not tech: return {}
        return {
            "prerequisites": tech.get("prerequisites", {}),
            "intel_cost": tech.get("intel_cost", 0),
            "research_turns": tech.get("research_turns", 3)
        }

    def is_hybrid_tech_available(self, faction_obj, tech_id: str) -> bool:
        """Checks if faction has prerequisites from both universes."""
        reqs = self.get_hybrid_tech_requirements(tech_id)
        if not reqs: return False
        
        for universe, techs in reqs["prerequisites"].items():
            for t_id in techs:
                if t_id not in faction_obj.unlocked_techs:
                    return False
        return True

    def unlock_hybrid_tech(self, faction_obj, tech_id: str, turn: int = 0):
        """Unlocks a hybrid tech for a faction."""
        if tech_id not in self.hybrid_tech_trees: return
        if self.is_hybrid_tech_available(faction_obj, tech_id):
            if tech_id not in faction_obj.unlocked_techs:
                faction_obj.unlock_tech(tech_id, turn=turn)
                print(f"[HYBRID] {faction_obj.name} unlocked {tech_id}")

    def validate_hybrid_tech(self, tech_data: dict) -> bool:
        """Validates hybrid tech data consistency."""
        required_keys = ["tech_id", "universes", "prerequisites", "intel_cost"]
        if not all(k in tech_data for k in required_keys): return False
        if not isinstance(tech_data["intel_cost"], int) or tech_data["intel_cost"] < 0: return False
        return True
    def analyze_tech_tree(self, faction: str) -> dict:
        """
        Analyzes the tech tree to determine the strategic value of each technology.
        Value = Direct Unlocks + (N * Recursive Unlocks).
        
        Returns:
            Dict[str, float]: {tech_name: strategic_value}
        """
        # 2. Score Techs
        tech_values = {}
        
        # Add Hybrid Techs to analysis
        for h_id, h_data in self.hybrid_tech_trees.items():
            # Basic value for hybrid techs
            tech_values[h_id] = 5.0 # High base value for hybrid prestige
            
        tree = self.faction_tech_trees.get(faction)
        if not tree: return tech_values # Return only hybrid values if no tree
        
        # 1. Build Adjacency List (Parent -> Children)
        # tree["units"] is Child -> Parent
        adjacency = {}
        for child, parent in tree["units"].items():
            if parent not in adjacency: adjacency[parent] = []
            adjacency[parent].append(child)
            
        all_techs = list(tree["techs"].keys())
        memo = {}
        all_techs = list(tree["techs"].keys())
        
        memo = {}

        def get_subtree_score(node):
            if node in memo: return memo[node]
            
            score = 0
            # Direct children
            children = adjacency.get(node, [])
            
            # Value Logic:
            # - Unlocking a Unit = 1 point
            # - Unlocking a Tech = 0.5 points (intermediate step) + Its Subtree
            
            for child in children:
                is_tech = child in tree["techs"]
                if is_tech:
                    # Recursive value
                    score += 0.5 + get_subtree_score(child)
                else:
                    # Leaf Unit/Building
                    score += 1.0 # TODO: We could weigh units by power rating here!
            
            memo[node] = score
            return score

        for tech in all_techs:
            tech_values[tech] = get_subtree_score(tech)
            
        # Add Hybrid Techs to analysis
        for h_id, h_data in self.hybrid_tech_trees.items():
            # Basic value for hybrid techs
            # Ensure they have at least a base value of 1.0 even if not in subtree
            subtree_val = tech_values.get(h_id, 0.0)
            tech_values[h_id] = max(1.0, subtree_val, 5.0) # Boost hybrid prestige
            
        return tech_values

    def calculate_tech_tree_depth(self, faction: str, unlocked_techs: List[str]) -> Dict[str, Any]:
        """
        Calculates tech tree depth metrics for a faction.
        
        Args:
            faction: Faction name
            unlocked_techs: List of unlocked tech IDs
        
        Returns:
            Dict with depth metrics: total_depth, avg_depth, tier_breakdown
        """
        f_lower = faction.lower()
        tree = self.faction_tech_trees.get(f_lower)
        
        if not tree:
            return {
                "total_depth": 0, 
                "avg_depth": 0.0, 
                "tier_breakdown": {},
                "unlocked_count": len(unlocked_techs)
            }
        
        # Build dependency graph (child -> parent)
        dependencies = tree.get("units", {})
        
        # Calculate depth for each unlocked tech
        depths = {}
        tier_counts = {}
        
        def get_depth(tech_id, visited=None):
            if visited is None:
                visited = set()
            
            if tech_id in visited:
                return 0  # Circular dependency guard
            
            if tech_id in depths:
                return depths[tech_id]
            
            visited.add(tech_id)
            
            parent = dependencies.get(tech_id)
            if not parent or parent == "ROOT": # Assuming ROOT or None
                d = 1
            else:
                d = 1 + get_depth(parent, visited)
                
            depths[tech_id] = d
            return d
        
        # Calculate depth for all unlocked techs
        # Only count depth for techs that exist in the tree definition
        # (ignoring dynamic/synthetic techs if any)
        known_techs = tree.get("techs", {})
        
        relevant_techs = [t for t in unlocked_techs if t in known_techs]
        
        for tech_id in relevant_techs:
            d = get_depth(tech_id)
            tier_counts[d] = tier_counts.get(d, 0) + 1
        
        # Total depth is sum of levels of all unlocked techs?
        # Or Just the max depth reached?
        # "metrics like total depth, average depth" implies sum.
        # Note: depths dict might contain parents that aren't unlocked if we walked up.
        # We should only aggregate stats for the *unlocked* techs.
        
        unlocked_depths = [depths[t] for t in relevant_techs if t in depths]
        total = sum(unlocked_depths)
        avg = total / len(unlocked_depths) if unlocked_depths else 0.0
        
        return {
            "total_depth": total,
            "avg_depth": avg,
            "tier_breakdown": tier_counts,
            "unlocked_count": len(unlocked_techs)
        }

    # --- Infinite Research System (Batch 13) ---
    def generate_next_tier_tech(self, faction_name: str, base_tech_id: str) -> Optional[str]:
        """
        Dynamically generates the next tier of a technology.
        Example: "Lasers III" -> "Lasers IV"
        """
        f_lower = faction_name.lower()
        tree = self.faction_tech_trees.get(f_lower)
        if not tree: return None
        
        # 1. Parse current tier
        match = re.search(r" (I|II|III|IV|V|VI|VII|VIII|IX|X|\d+)$", base_tech_id)
        current_tier = 1
        base_name = base_tech_id
        if match:
            suffix = match.group(1)
            base_name = base_tech_id[:match.start()].strip()
            # Convert Roman/Int to Int
            if suffix.isdigit():
                 current_tier = int(suffix)
            else:
                 romans = {"I":1, "II":2, "III":3, "IV":4, "V":5, "VI":6, "VII":7, "VIII":8, "IX":9, "X":10}
                 current_tier = romans.get(suffix, 1)
        
        next_tier = current_tier + 1
        new_id = f"{base_name} {next_tier}"
        
        # 2. Check if already exists
        if new_id in tree["techs"]:
            return new_id
            
        # 3. Create new procedural tech
        prev_cost = tree["techs"].get(base_tech_id, int(1000 * self.cost_multiplier))
        new_cost = int(prev_cost * 1.5) # +50% cost per tier
        
        tree["techs"][new_id] = new_cost
        tree.setdefault("prerequisites", {})[new_id] = [base_tech_id]
        
        # 4. Clone Passive Effects from base (Phase 107 Persistence)
        if base_tech_id in self.tech_effects:
             self.tech_effects[new_id] = self.tech_effects[base_tech_id][:]
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.debug(f"[TechManager] Generated Infinite Tech: {new_id} (Cost: {new_cost}) for {faction_name}")
        return new_id

    def draw_research_cards(self, faction, num_cards: int = 3) -> List[dict]:
        """
        Draws N random research options from available techs.
        Used for the 'Card System' (Stellaris-style).
        """
        available = self.get_available_research(faction)
        if not available:
             return []
             
        # If fewer options than cards, return all
        if len(available) <= num_cards:
            return available
            
        # Random draw
        # Future: Implement weighting logic here if needed (e.g. bias towards cheaper or cheaper+synergy)
        # For now, uniform random is fair enough for the specific 'Draw' mechanic.
        import random
        return random.sample(available, num_cards)

    def get_available_research(self, faction) -> List[dict]:
        """
        Returns a list of all currently researchable technologies.
        Includes base tree unlockables and next-tier procedural techs.
        """
        available = []
        all_techs = self.faction_tech_trees.get(faction.name.lower(), {}).get("techs", {})
        
        # 1. Base Techs
        for tech_id, cost in all_techs.items():
            if tech_id in ["None", "Headquarters"]: continue
            if tech_id in faction.unlocked_techs: continue
            if tech_id in [p.tech_id for p in faction.research_queue]: continue
            
            if self.can_research(faction.name, tech_id, faction_obj=faction):
                available.append({"id": tech_id, "cost": cost})
                
        # 2. Generate Next Tiers for Completed Leafs
        # Should we do this on-demand or pre-generate?
        # On-demand: For every unlocked tech, check if it has a successor. If not, offer one.
        for unlocked in faction.unlocked_techs:
             # Check if this tech is a 'leaf' in the current context (no unlocked children)
             # actually we just check if we can invent the next one
             next_id = self.generate_next_tier_tech(faction.name, unlocked)
             if next_id:
                  # Check if we already have it or queued it
                  if next_id in faction.unlocked_techs: continue
                  if next_id in [p.tech_id for p in faction.research_queue]: continue
                  
                  # It's available
                  cost = all_techs.get(next_id, 2000) # Default cost if not in tree yet? 
                  # generate_next_tier_tech updates the tree, so it should be there.
                  if next_id in all_techs:
                       cost = all_techs[next_id]
                  
                  available.append({"id": next_id, "cost": cost})
                  
        return available

    def log_tech_tree_progress(self, engine, faction_name: str):
        """
        Logs tech tree progress metrics for a faction.
        """
        if not hasattr(engine, 'telemetry') or not engine.telemetry:
            return

        f_obj = engine.get_faction(faction_name)
        if not f_obj: return
        
        metrics = self.calculate_tech_tree_depth(faction_name, f_obj.unlocked_techs)
        
        # Calculate Queue Depth
        queue_depth = len(f_obj.research_queue)
        
        from src.reporting.telemetry import EventCategory
        engine.telemetry.log_event(
            EventCategory.TECHNOLOGY,
            "tech_tree_progress",
            {
                "faction": faction_name,
                "unlocked_count": metrics["unlocked_count"],
                "total_depth": metrics["total_depth"],
                "avg_depth": metrics["avg_depth"],
                "tier_breakdown": metrics["tier_breakdown"],
                "research_queue_length": queue_depth,
                "intel_points": getattr(f_obj, 'intel_points', 0)
            },
            turn=engine.turn_counter,
            faction=faction_name
        )
    def log_tech_roi(self, engine, faction_name: str, tech_id: str):
        """Logs the Return on Investment for a specific technology (Metric #4)."""
        if not hasattr(engine, 'telemetry') or not engine.telemetry:
            return

        from src.reporting.telemetry import EventCategory

        f_obj = engine.get_faction(faction_name)
        if not f_obj: return
        
        # We need to know when it was unlocked to calculate ROI
        # For now, we'll assume the caller provides a tech that was unlocked 10-20 turns ago.
        # This is a simplistic ROI: 
        # If it's an economic tech, check income delta.
        # If it's a military tech, check power delta or win rate.
        
        tech_tree = self.faction_tech_trees.get(faction_name.lower(), {})
        tech_cost = tech_tree.get("techs", {}).get(tech_id, 1000)
        
        impact = {
            "economic_benefit": 0.0,
            "military_benefit": 0.0,
            "strategic_benefit": 0.0
        }
        
        # Heuristic implementation for ROI
        if "Industry" in tech_id or "Economy" in tech_id:
            impact["economic_benefit"] = f_obj.stats.get("turn_req_income", 0) * 0.05 # Assume 5% contribution
        elif "Combat" in tech_id or "Weapon" in tech_id:
            impact["military_benefit"] = f_obj.military_power * 0.02 # Assume 2% force multiplier
            
        roi_score = (impact["economic_benefit"] + impact["military_benefit"]) / tech_cost if tech_cost > 0 else 0.0

        engine.telemetry.log_event(
            EventCategory.TECHNOLOGY,
            "research_roi",
            {
                "faction": faction_name,
                "tech_id": tech_id,
                "turn": engine.turn_counter,
                "cost": tech_cost,
                "impact": impact,
                "roi_score": roi_score,
                "is_profitable": roi_score > 1.0
            },
            turn=engine.turn_counter,
            faction=faction_name
        )

    def get_tech_effects(self, tech_id: str) -> List[str]:
        """Returns the list of raw effect strings for a tech."""
        return self.tech_effects.get(tech_id, [])

    def steal_technology(self, thief_faction, target_faction, tech_id: str):
        """
        Allows a thief faction to steal a specific tech from a target faction.
        """
        if tech_id in thief_faction.unlocked_techs: return
        
        # Verify tech validity (must exist in game)
        # We can assume if it was on a ship, it's a valid ID.
        
        # Unlock immediately
        thief_faction.unlock_tech(tech_id)
        
        print(f"[ESPIONAGE] {thief_faction.name} STOLE {tech_id} from {target_faction.name}!")
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"[ESPIONAGE] {thief_faction.name} stole {tech_id}")
        # We add it to 'stolen_techs' to track it.
        if not hasattr(thief_faction, 'stolen_techs'): thief_faction.stolen_techs = set()
        
        thief_faction.stolen_techs.add(tech_id)
        thief_faction.unlock_tech(tech_id)
        print(f"[ESPIONAGE] {thief_faction.name} stole {tech_id} from {target_faction.name}!")

    def combine_technologies(self, faction, tech_a: str, tech_b: str) -> Optional[str]:
        """
        Synthesizes a new Hybrid Tech from two existing techs.
        """
        if tech_a not in faction.unlocked_techs or tech_b not in faction.unlocked_techs:
            return None
            
        new_id = f"Hybrid_{tech_a}_X_{tech_b}"
        if new_id in faction.unlocked_techs: return new_id
        
        # Create Data
        name_a = tech_a.split("_")[-1]
        name_b = tech_b.split("_")[-1]
        new_name = f"Integrated {name_a}-{name_b}"
        
        # Auto-add to tree
        tree = self.faction_tech_trees.get(faction.name.lower())
        if tree:
             cost = 5000 # High cost to stabilize
             tree["techs"][new_id] = cost
             tree.setdefault("prerequisites", {})[new_id] = [tech_a, tech_b]
             
             # Combine Effects
             eff_a = self.get_tech_effects(tech_a)
             eff_b = self.get_tech_effects(tech_b)
             self.tech_effects[new_id] = eff_a + eff_b + ["+10% Synergy Efficiency"]
             
             print(f"[RESEARCH] {faction.name} synthesized new tech: {new_name} ({new_id})")
             return new_id
        return None

    def parse_effect_to_modifier(self, effect_str: str) -> Optional[tuple]:
        """
        Parses a string like "+10% Damage" or "-20% Cost" into (key, multiplier_delta).
        """
        # Clean string
        s = effect_str.strip().lower()
        
        # Regex for percentage
        import re
        match = re.search(r"([+-]?\d+)%\s+(.+)", s)
        if match:
            val_str = match.group(1)
            stat_name = match.group(2).strip()
            
            # Remove trailing periods
            stat_name = stat_name.rstrip(".")
            
            value = float(val_str) / 100.0
            
            # Map Stat Name to Internal Modifier Key
            mapping = {
                "damage": "damage_mult",
                "unit health": "unit_health_mult",
                "vehicle health": "vehicle_health_mult",
                "construction speed": "construction_speed_mult",
                "requisition income": "income_requisition_mult",
                "trade income": "income_trade_mult",
                "morale": "morale_base_add", 
                "ranged damage": "ranged_damage_mult",
                "artillery damage": "artillery_damage_mult",
                "planetary defense": "planetary_defense_mult",
                "xp gain": "xp_gain_mult",
                
                # --- Procedural Stats Mappings ---
                "energy damage": "energy_damage_mult",
                "ap damage": "ap_damage_mult",
                "ballistic damage": "ballistic_damage_mult",
                "explosive damage": "explosive_damage_mult",
                "melee damage": "melee_damage_mult",
                "shield cap": "shield_max_mult",
                "armor value": "armor_mult",
                "hit points": "unit_health_mult",
                "mineral income": "income_minerals_mult",
                "energy income": "income_energy_mult",
                "speed": "movement_speed_mult",
                "flux speed": "flux_speed_mult",
                "efficiency": "global_efficiency_mult",
                "fleet cap": "fleet_cap_mult",
                "research speed": "research_speed_mult"
            }
            
            if stat_name in mapping:
                return (mapping[stat_name], value)
            
            # Partial match checks
            if "health" in stat_name: return ("unit_health_mult", value)
            if "damage" in stat_name: return ("damage_mult", value)
            if "income" in stat_name: return ("income_mult", value)
            if "speed" in stat_name: return ("movement_speed_mult", value)
            
            # Suppress warning for purely decorative stats
            ignored = ["flavor", "visuals", "synergy efficiency"]
            if stat_name not in ignored:
                 print(f"[TechManager] WARNING: Unmapped tech effect stat: '{stat_name}' from string '{effect_str}'")
                 
            return None
            
        return None
