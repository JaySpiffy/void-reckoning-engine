export interface BattleStats {
  rate: number;
  total: number;
}

export interface UnitStats {
  spawn_rate: Record<string, { navy: number; army: number }>;
  loss_rate: Record<string, { navy: number; army: number }>;
  total_spawned: number;
  total_lost: number;
}

export interface ConstructionStats {
  rate: Record<string, number>;
  total: number;
}

export interface EconomyStats {
  flow_rate: Record<string, number>;
  total_revenue: number;
  upkeep_breakdown: Record<string, { military: number; infrastructure: number }>;
}

export interface EconomicHealth {
  net_profit: number;
  gross_income: number;
  total_upkeep: number;
  stockpile_velocity: number | Record<string, unknown>;
  revenue_breakdown: Record<string, number>;
}

export interface BattlePerformance {
  avg_cer: number;
  latest_composition: Record<string, number>;
  latest_attrition: number;
  recent_battle_count: number;
}

export interface FactionStatus {
  Score: number;
  S: number; // Systems
  P: number; // Planets
  B: number; // Buildings
  SB: number; // Starbases
  F: number; // Fleets
  A: number; // Armies
  R: number; // Requisition
  Req?: number;
  T: number; // Tech
  BW: number; // Battle Wins
  BD: number; // Battle Draws
  BF: number; // Battles Fought
  Post: string; // Posture
}

export interface PlanetStatus {
  name: string;
  owner: string;
  type: string;
}

export interface LiveMetrics {
  battles: BattleStats;
  units: UnitStats;
  construction: ConstructionStats;
  economy: EconomyStats;
  economic_health: Record<string, EconomicHealth>;
  battle_performance: Record<string, BattlePerformance>;
  turn: number;
  faction_status: Record<string, FactionStatus>;
  planet_status: PlanetStatus[];
  timestamp?: number;
}

export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: number;
}
