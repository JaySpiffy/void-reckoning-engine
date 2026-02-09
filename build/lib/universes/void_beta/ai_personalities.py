from universes.base.personality_template import FactionPersonality

PERSONALITY_DB = {
    # 1. Templars_of_the_Flux (Aggressive Crusaders)
    "Templars_of_the_Flux": FactionPersonality(
        name="Templars_of_the_Flux",
        aggression=1.5,
        expansion_bias=1.2,
        cohesiveness=0.8,
        description="Fanatical crusaders who favor aggressive expansion and melee combat.",
        strategic_doctrine="AGGRESSIVE_EXPANSION",
        combat_doctrine="SHOCK_ASSAULT",
        tech_doctrine="PURITAN",
        tech_focus=["military", "volatility"],
        quirks={"threat_affinity": 2.0}
    ),

    # 2. Transcendent_Order (Elitist Tech-Mages)
    "Transcendent_Order": FactionPersonality(
        name="Transcendent_Order",
        aggression=0.8,
        expansion_bias=0.8,
        cohesiveness=1.2,
        retreat_threshold=0.3, # Value elite lives
        description="Quality over quantity. Favors powerful, consolidated fleets.",
        strategic_doctrine="CONSOLIDATION",
        combat_doctrine="ELITE_CASTER",
        tech_doctrine="PRAGMATIC",
        tech_focus=["energy", "aether", "information"],
        quirks={"research_multiplier": 1.2}
    ),

    # 3. SteelBound_Syndicate (Defensive Industrialists)
    "SteelBound_Syndicate": FactionPersonality(
        name="SteelBound_Syndicate",
        aggression=0.7,
        expansion_bias=1.0,
        cohesiveness=1.5,
        retreat_threshold=0.2, # Stubborn
        description="Slow, methodical expansion backed by heavy armor.",
        strategic_doctrine="DEFENSIVE_CONSOLIDATION",
        combat_doctrine="ATTRITION",
        tech_doctrine="PRAGMATIC",
        tech_focus=["mass", "cohesion", "engineering"],
        quirks={"navy_recruitment_mult": 0.9, "army_recruitment_mult": 1.2}
    ),

    # 4. BioTide_Collective (Biological Flood)
    "BioTide_Collective": FactionPersonality(
        name="BioTide_Collective",
        aggression=1.8,
        expansion_bias=1.5,
        cohesiveness=0.4, # Swarm tactics
        retreat_threshold=0.1, # Fearless
        description="Endless expansion consumed by hunger. Losses are acceptable.",
        strategic_doctrine="AGGRESSIVE_EXPANSION",
        combat_doctrine="SWARM",
        tech_doctrine="XENOPHOBIC",
        tech_focus=["mass", "volatility", "frequency"],
        quirks={"biomass_hunger": 2.0, "navy_recruitment_mult": 1.5}
    ),

    # 5. Algorithmic_Hierarchy (Machine Intelligence)
    "Algorithmic_Hierarchy": FactionPersonality(
        name="Algorithmic_Hierarchy",
        aggression=1.0,
        expansion_bias=1.0,
        cohesiveness=1.0,
        retreat_threshold=0.5, # Calculated
        description="Logical and efficient. Assimilates technology.",
        strategic_doctrine="BALANCED",
        combat_doctrine="COORDINATED_FIRE",
        tech_doctrine="ADAPTIVE",
        tech_focus=["information", "energy", "stability"],
        quirks={"on_kill_effect": "assimilate"}
    ),
    
    # 6. Nebula_Drifters (Raiders)
    "Nebula_Drifters": FactionPersonality(
        name="Nebula_Drifters",
        aggression=1.2,
        expansion_bias=0.6, # Doesn't paint map
        cohesiveness=0.6, # Wolfpacks
        retreat_threshold=0.7, # Runs away easily
        description="Hit-and-run raiders who prefer looting to conquering.",
        strategic_doctrine="RAID_ECONOMY",
        combat_doctrine="SKIRMISH",
        tech_doctrine="ADAPTIVE",
        tech_focus=["frequency", "volatility"],
        quirks={"casualty_plunder_ratio": 0.5, "evasion_rating": 1.2}
    ),

    # 7. Aurelian_Hegemony (Standard Empire)
    "Aurelian_Hegemony": FactionPersonality(
        name="Aurelian_Hegemony",
        aggression=1.0,
        expansion_bias=1.0,
        cohesiveness=1.0,
        description="A balanced empire focusing on standard expansion and diplomacy.",
        strategic_doctrine="BALANCED",
        combat_doctrine="STANDARD",
        tech_doctrine="PRAGMATIC",
        tech_focus=["mass", "energy", "leadership"],
        quirks={"diplomacy_bonus": 20}
    ),

    # 8. VoidSpawn_Entities (Chaotic Invaders)
    "VoidSpawn_Entities": FactionPersonality(
        name="VoidSpawn_Entities",
        aggression=2.0,
        expansion_bias=0.8, # Focused on destruction
        cohesiveness=0.2, # Chaotic
        retreat_threshold=0.0, # Never retreat
        description="Manifestations of chaos seeking purely to destroy.",
        strategic_doctrine="AGGRESSIVE_EXPANSION",
        combat_doctrine="SHOCK_ASSAULT",
        tech_doctrine="RADICAL",
        tech_focus=["aether", "volatility", "will"],
        quirks={"threat_affinity": 1.5}
    ),
    
    # 9. ScrapLord_Marauders (Resource Opportunists)
    "ScrapLord_Marauders": FactionPersonality(
        name="ScrapLord_Marauders",
        aggression=0.6,
        expansion_bias=0.7,
        cohesiveness=0.5,
        retreat_threshold=0.6,
        description="Survivalists who avoid fair fights and scavenge tech.",
        strategic_doctrine="OPPORTUNISTIC",
        combat_doctrine="AMBUSH",
        tech_doctrine="ADAPTIVE",
        tech_focus=["mass", "engineering"],
        quirks={"casualty_plunder_ratio": 0.8}
    ),

    # 10. Primeval_Sentinels (Fallen Empire)
    "Primeval_Sentinels": FactionPersonality(
        name="Primeval_Sentinels",
        aggression=0.2, # Isolationist
        expansion_bias=0.1, # Owns enough
        cohesiveness=1.5, # Deathballs
        retreat_threshold=0.2,
        description="Ancient protectors who only fight when provoked.",
        strategic_doctrine="DEFENSIVE_CONSOLIDATION",
        combat_doctrine="SUPERIOR_FIREPOWER",
        tech_doctrine="XENOPHOBIC",
        tech_focus=["aether", "focus", "stability"],
        quirks={"tech_advantage": 2.0}
    )
}

def get_personality(faction_name: str) -> FactionPersonality:
    """Retrieves personality for a faction."""
    return PERSONALITY_DB.get(faction_name, FactionPersonality(name=faction_name))
