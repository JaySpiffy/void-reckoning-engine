def ensure_tactical_ships(ships):
    """
    Ensures ships have necessary tactical attributes (grid_size, weapon_arcs, armor_front).
    """
    tactical_ships = []
    for s in ships:
        if hasattr(s, 'grid_size') and hasattr(s, 'weapon_arcs') and hasattr(s, 'armor_front'):
            tactical_ships.append(s)
            continue
        
        # Upgrade/Fix Unit to Ship
        if not hasattr(s, 'grid_size'): s.grid_size = [1, 1]
        if not hasattr(s, 'facing'): s.facing = 0
        if not hasattr(s, 'agility'): s.agility = 45
        if not hasattr(s, 'weapon_arcs'): s.weapon_arcs = {}
        if not hasattr(s, 'armor_front'): 
            base_arm = getattr(s, 'armor', 0)
            s.armor_front = base_arm
            s.armor_side = int(base_arm * 0.75)
            s.armor_rear = int(base_arm * 0.5)
        tactical_ships.append(s)
    return tactical_ships
