
from typing import List, Dict, Tuple, Optional, Any
import logging
from src.core import gpu_utils
from src.core.gpu_utils import log_backend_usage
from src.models.unit import Unit

logger = logging.getLogger(__name__)

class GPUTracker:
    """
    Maintains a parallel state of unit positions on the GPU (or vectorized CPU numpy)
    to accelerate O(n^2) distance queries and spatial operations.
    """
    
    def __init__(self):
        self.unit_to_index: Dict[int, int] = {} # map(id(unit) -> index)
        self.index_to_unit: Dict[int, Unit] = {} # map(index -> unit)
        self.positions = None # N x 2 array (x, y)
        self.ids = None # N array of IDs (for verification)
        self.factions = None # N array of encoded faction IDs
        self.faction_map = {} # str -> int
        self.active_count = 0
        self.xp = gpu_utils.get_xp()
        
        self.is_dirty = False
        
    def initialize(self, units: List[Unit]):
        """
        Initializes the tracker with a list of units.
        This should be called at the start of a battle or when the roster changes significantly.
        """
        self.unit_to_index.clear()
        self.index_to_unit.clear()
        
        # Encode factions to integers for GPU comparison
        self.faction_map = {}
        next_faction_id = 0
        
        pos_list = []
        id_list = []
        faction_list = []
        
        for idx, u in enumerate(units):
            # We track units by their object ID for fast lookup
            u_id = id(u)
            self.unit_to_index[u_id] = idx
            self.index_to_unit[idx] = u
            
            # Store position
            pos_list.append([float(u.grid_x), float(u.grid_y)])
            id_list.append(u_id)
            
            # Faction
            f = u.faction
            if f not in self.faction_map:
                self.faction_map[f] = next_faction_id
                next_faction_id += 1
            faction_list.append(self.faction_map[f])
            
        self.active_count = len(units)
        
        # Move to Device
        self.positions = gpu_utils.to_gpu(pos_list)
        self.ids = gpu_utils.to_gpu(id_list)
        self.factions = gpu_utils.to_gpu(faction_list)
        self.is_dirty = False
        
        # logger.info(f"GPUTracker initialized with {self.active_count} units")
        log_backend_usage("GPUTracker", logger)

    def update_positions(self, units: List[Unit]):
        """
        Updates positions for a batch of units.
        Ideally called once per movement phase.
        """
        if self.positions is None:
            return
            
        # For small updates, we can do element-wise if needed, but usually we just rebuild 
        # or update a slice. If strict indexing is maintained:
        # We can construct a specialized update mask, but that's complex.
        
        # Simple Approach: partial update via host->device transfer
        # This is strictly faster than N separate writes
        
        # Create a temporary list of (idx, x, y)
        updates = []
        indices = []
        new_pos = []
        
        for u in units:
            u_id = id(u)
            if u_id in self.unit_to_index:
                idx = self.unit_to_index[u_id]
                # Check if actually moved to save bandwidth?
                # Assuming caller only sends moved units
                indices.append(idx)
                new_pos.append([u.grid_x, u.grid_y])
        
        if indices:
            # Scatter update
            # positions[indices] = new_pos
            # CuPy supports advanced indexing
            idx_arr = gpu_utils.to_gpu(indices)
            val_arr = gpu_utils.to_gpu(new_pos)
            
            self.positions[idx_arr] = val_arr
            self.is_dirty = True

    def compute_distance_matrix(self) -> Any:
        """
        Computes the N x N Euclidean distance matrix for all tracked units.
        Returns a GPU array (or numpy array).
        """
        if self.positions is None or self.active_count == 0:
            return self.xp.empty((0,0))
            
        # Broadcasting: (N, 1, 2) - (1, N, 2) -> (N, N, 2)
        # Then norm along last axis
        
        # Optimization: (x - x')^2 + (y - y')^2
        # Use simple squared diff
        
        diff = self.positions[:, None, :] - self.positions[None, :, :]
        dist_sq = self.xp.sum(diff**2, axis=2)
        dist_matrix = self.xp.sqrt(dist_sq)
        
        return dist_matrix

    def get_nearest_neighbors(self, unit: Unit, k: int = 10) -> List[Tuple[Unit, float]]:
        """
        Returns the k-nearest neighbors for a specific unit using the GPU state.
        """
        u_id = id(unit)
        if u_id not in self.unit_to_index:
            return []
            
        idx = self.unit_to_index[u_id]
        
        # Calculate distance vector for just this unit (1 x N)
        # (N, 2) - (1, 2)
        target_pos = self.positions[idx:idx+1] # Keep dim
        diff = self.positions - target_pos 
        dist_sq = self.xp.sum(diff**2, axis=1) # (N,)
        dists = self.xp.sqrt(dist_sq)
        
        # Sort / Partition
        # We want indices of smallest k elements
        # argsort is expensive O(N log N). argpartition is O(N)
        
        k = min(k, self.active_count - 1)
        if k <= 0: return []

        # If we are using CuPy, argpartition might not be fully implemented in older versions or slightly different
        # Standard argsort is safer for general support
        sorted_indices = self.xp.argsort(dists)
        
        # Get top k+1 (including self)
        # Self is always distance 0, so it's first
        top_k_indices = sorted_indices[:k+1]
        
        # Transfer back to CPU
        cpu_indices = gpu_utils.ensure_list(top_k_indices)
        cpu_dists = gpu_utils.ensure_list(dists[top_k_indices])
        
        results = []
        for i, neighbor_idx in enumerate(cpu_indices):
            if neighbor_idx == idx:
                continue # Skip self
                
            n_unit = self.index_to_unit.get(int(neighbor_idx))
            if n_unit:
                # [OPTIONAL] Faction filter could be applied here if we passed it
                results.append((n_unit, float(cpu_dists[i])))
                
        return results

    def compute_flow_field(self) -> Dict[int, Tuple[int, int, float]]:
        """
        Computes the movement vector for ALL units towards their nearest enemy.
        Returns a dictionary {unit_id: (dx, dy, dist_to_target)}
        """
        if self.positions is None or self.active_count < 2:
            return {}
            
        # 1. Compute full Distance Matrix (N x N)
        # diff = (N, 1, 2) - (1, N, 2) -> (N, N, 2)
        diff = self.positions[:, None, :] - self.positions[None, :, :]
        dist_sq = self.xp.sum(diff**2, axis=2) # (N, N)
        
        # 2. Mask Factions (Same faction = Infinity Distance)
        # factions = (N,)
        # Mask = (N, 1) == (1, N) -> (N, N) bool matrix where True = same faction
        f_col = self.factions[:, None]
        f_row = self.factions[None, :]
        same_faction_mask = (f_col == f_row)
        
        # Apply mask: Set distance to infinity/large value where same_faction is True
        # Note: This also masks self (dist 0 -> inf), which is what we want (can't target self)
        max_val = self.xp.amax(dist_sq) + 1.0 
        masked_dist_sq = self.xp.where(same_faction_mask, max_val * 2.0, dist_sq)
        
        # Check if there are ANY enemies. If a row is all 'infinity', no enemies exist.
        # We can check min value per row.
        min_dists_sq = self.xp.min(masked_dist_sq, axis=1)
        valid_targets = min_dists_sq < max_val * 1.5
        
        # 3. Find Nearest Enemy Index
        # argmin over axis 1 (columns) -> for each row (unit), which col (target) is closest
        target_indices = self.xp.argmin(masked_dist_sq, axis=1)
        
        # [Synchronization]
        gpu_utils.synchronize()
        
        # 4. Compute Vector to Target
        # Vector = TargetPos - MyPos
        # Gather target positions
        targets_pos = self.positions[target_indices] # (N, 2)
        
        # Delta
        vectors = targets_pos - self.positions # (N, 2)
        
        # Normalize to direction (sign)
        directions = self.xp.sign(vectors)
        
        # 5. Extract Results
        # Transfer to CPU
        cpu_directions = gpu_utils.to_cpu(directions) # (N, 2)
        cpu_valid = gpu_utils.to_cpu(valid_targets)
        # Calculate actual distances (sqrt) implies GPU op
        min_dists = self.xp.sqrt(min_dists_sq)
        cpu_dists = gpu_utils.to_cpu(min_dists)
        cpu_ids = gpu_utils.ensure_list(self.ids)
        
        result = {}
        for i, uid in enumerate(cpu_ids):
            if cpu_valid[i]:
                dx = int(cpu_directions[i][0])
                dy = int(cpu_directions[i][1])
                dist = float(cpu_dists[i])
                result[uid] = (dx, dy, dist)
                
        return result

    def compute_nearest_enemies(self) -> Dict[int, Tuple[int, float]]:
        """
        Returns a dictionary {attacker_id: (target_id, distance)}
        Finds the nearest enemy for every unit.
        """
        if self.positions is None or self.active_count < 2:
            return {}
            
        # [Duplicated Logic from flow_field can be refactored, but keeping inline for clarity for now]
        # 1. Distance Matrix
        diff = self.positions[:, None, :] - self.positions[None, :, :]
        dist_sq = self.xp.sum(diff**2, axis=2) 
        
        # 2. Mask Factions
        f_col = self.factions[:, None]
        f_row = self.factions[None, :]
        same_faction_mask = (f_col == f_row)
        
        # Apply mask
        max_val = self.xp.amax(dist_sq) + 1.0 
        masked_dist_sq = self.xp.where(same_faction_mask, max_val * 2.0, dist_sq)
        
        min_dists_sq = self.xp.min(masked_dist_sq, axis=1)
        valid_targets = min_dists_sq < max_val * 1.5
        
        # 3. Indices
        target_indices_gpu = self.xp.argmin(masked_dist_sq, axis=1)
        
        # [Synchronization]
        gpu_utils.synchronize()
        
        # 4. Extract
        cpu_target_indices = gpu_utils.to_cpu(target_indices_gpu)
        cpu_valid = gpu_utils.to_cpu(valid_targets)
        min_dists = self.xp.sqrt(min_dists_sq)
        cpu_dists = gpu_utils.to_cpu(min_dists)
        cpu_ids = gpu_utils.ensure_list(self.ids)
        
        # CPU Map
        # We need to map index -> Unit ID
        # self.ids is a GPU array, cpu_ids is list
        
        result = {}
        for i, attacker_uid in enumerate(cpu_ids):
            if cpu_valid[i]:
                target_idx = int(cpu_target_indices[i])
                # We need the ID of the target unit
                # We can look it up from cpu_ids if we trust indices match
                target_uid = cpu_ids[target_idx]
                dist = float(cpu_dists[i])
                
                result[attacker_uid] = (target_uid, dist)
                
        return result

    def log_event(self, event_type, source, target, **kwargs):
        """
        Logs a combat event (stub).
        In a real implementation, this would buffer logs for async writing.
        """
        # For now, just pass or print if debug needed
        pass
        
    def cleanup(self):
        """
        Explicitly releases GPU memory resources.
        """
        self.positions = None
        self.ids = None
        self.factions = None
        self.active_count = 0
        self.unit_to_index.clear()
        self.index_to_unit.clear()
        
        # Call global cleanup
        gpu_utils.clean_memory()
        logger.debug("GPUTracker resources cleaned up.")

    def __del__(self):
        try:
             self.cleanup()
        except:
             pass
