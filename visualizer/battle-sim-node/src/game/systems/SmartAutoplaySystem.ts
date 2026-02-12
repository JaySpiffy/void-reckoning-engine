/**
 * SMART AUTOPILOT SYSTEM - Intelligent AI Player
 * 
 * This system replaces the basic autoplay with smart decision-making:
 * - Auto-evolves based on optimal DNA strategy
 * - Smart targeting and positioning
 * - Resource management
 * - Ability usage strategy
 */

import type { Vector2 } from '../types';
import type { Player } from '../entities/Player';
import type { Enemy } from '../entities/Enemy';
import { Vec2 } from '../utils/Vector2';
import { dnaSystem } from './DNASystem';
import { mutationSystem, MutationType, MUTATIONS } from './MutationSystem';
import { buildingSystem, BUILDING_ARCHETYPES } from './BuildingSystem';
import { globalEvents } from '../utils';
import { GameEvent, DNAType, BuildingType, type Resources } from '../types';
import { COMPLETE_EVOLUTION_TREE } from './EvolutionTree';
import type { EvolutionPath, Genome } from './DNACore';
import { entityManager } from '../managers/EntityManager';


export interface SmartAutoplayConfig {
  /** How aggressive the AI is (0-1) */
  aggressiveness: number;
  /** Preferred combat range */
  preferredRange: number;
  /** Health % to retreat at */
  retreatThreshold: number;
  /** Whether to auto-evolve */
  autoEvolve: boolean;
  /** Whether to use abilities intelligently */
  smartAbilities: boolean;
  /** Whether to auto-build */
  autoBuild: boolean;
  /** Whether to auto-buy mutations */
  autoMutate: boolean;
}

const DEFAULT_CONFIG: SmartAutoplayConfig = {
  aggressiveness: 0.7,
  preferredRange: 150,
  retreatThreshold: 0.3,
  autoEvolve: true,
  smartAbilities: true,
  autoBuild: false, // Disabled by default - can be enabled for testing
  autoMutate: true, // NEW: Auto-buy mutations
};

// NEW: Mutation configuration
interface MutationConfig {
  minPointsBeforePurchase: number; // Wait until we have this many points
  prioritizeStability: boolean;
  prioritizePurity: boolean;
  maxMutationsPerWave: number;
}

export class SmartAutoplaySystem {
  private enabled: boolean = false;
  private config: SmartAutoplayConfig;
  
  // State tracking
  private currentTarget: Enemy | null = null;
  private lastEvolutionCheck: number = 0;
  private movementVector: Vector2 = { x: 0, y: 0 };
  private targetPosition: Vector2 = { x: 0, y: 0 };
  private wantsToAttack: boolean = false;
  private abilitySlotToUse: number = 0;
  
  // Cooldowns

  private abilityCooldowns: number[] = [0, 0, 0, 0, 0];
  
  // dashCooldown removed - tracked in abilityCooldowns[0]
  
  constructor(config: Partial<SmartAutoplayConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    // Listen for evolution opportunities
    globalEvents.on(GameEvent.EVOLUTION_AVAILABLE, (data: { paths: Array<{ id: string; name: string }> }) => {
      if (this.enabled && this.config.autoEvolve) {
        this.handleEvolutionAvailable(data.paths);
      }
    });
  }
  
  /**
   * Auto-evolve based on optimal strategy
   * Analyzes DNA, stats, and game state to pick the best evolution path
   */
  private handleEvolutionAvailable(paths: Array<{ id: string; name: string }>): void {
    const now = Date.now();
    if (now - this.lastEvolutionCheck < 1000) return; // Debounce
    this.lastEvolutionCheck = now;
    
    const genome = dnaSystem.getGenome();
    const player = this.getPlayer();
    
    // Get full evolution path data
    const availablePaths = paths
      .map(p => COMPLETE_EVOLUTION_TREE[p.id])
      .filter((p): p is EvolutionPath => p !== undefined);
    
    if (availablePaths.length === 0) return;
    
    // Score each path
    const scoredPaths = availablePaths.map(path => ({
      path,
      score: this.scoreEvolutionPath(path, genome, player)
    }));
    
    // Sort by score descending
    scoredPaths.sort((a, b) => b.score - a.score);
    
    const bestPath = scoredPaths[0];
    if (bestPath && bestPath.score > 0) {
      // Log decision for debugging
      console.log(`[SmartAI] Evolving to ${bestPath.path.name} (score: ${bestPath.score.toFixed(1)})`);
      dnaSystem.evolve(bestPath.path.id);
    }
  }
  
  /**
   * Score an evolution path based on multiple factors
   */
  private scoreEvolutionPath(path: EvolutionPath, genome: Genome, player: Player | null): number {
    let score = 0;
    
    // 1. DNA Match Score (0-40 points)
    score += this.calculateDNAMatchScore(path, genome);
    
    // 2. Stat Synergy Score (0-30 points)
    if (player) {
      score += this.calculateStatSynergyScore(path, player);
    }
    
    // 3. Purity Bonus (0-20 points)
    // Higher purity = more focused evolution = better bonuses
    const purityBonus = genome.purity * 20;
    score += purityBonus;
    
    // 4. Generation Match (0-10 points)
    // Prefer paths matching current generation for progression
    const currentGen = genome.generation;
    const pathGen = path.requirements.minGeneration || 0;
    if (currentGen === pathGen) {
      score += 10;
    }
    
    return score;
  }
  
  /**
   * Calculate how well the path matches current DNA
   */
  private calculateDNAMatchScore(path: EvolutionPath, genome: Genome): number {
    let score = 0;
    
    // Get DNA requirements
    const minDNA = path.requirements.minDNA;
    const dominantType = genome.dominantType;
    
    // Check if path matches dominant DNA type
    for (const [requiredType, requiredAmount] of Object.entries(minDNA)) {
      const strand = genome.strands.get(requiredType as DNAType);
      if (strand) {
        // Score based on how much DNA we have vs required
        const ratio = Math.min(strand.value / requiredAmount, 1.5);
        score += ratio * 20;
        
        // Extra bonus for dominant type match
        if (requiredType === dominantType) {
          score += 10;
        }
      }
    }
    
    // Penalize if we don't meet requirements (shouldn't happen, but safety check)
    for (const [requiredType, requiredAmount] of Object.entries(minDNA)) {
      const strand = genome.strands.get(requiredType as DNAType);
      if (!strand || strand.value < requiredAmount) {
        score -= 50; // Heavy penalty
      }
    }
    
    return Math.max(0, score);
  }
  
  /**
   * Calculate stat synergy based on current needs
   */
  private calculateStatSynergyScore(path: EvolutionPath, player: Player): number {
    let score = 0;
    const bonuses = path.bonuses;
    
    // Health need analysis
    const healthPercent = player.stats.health / player.stats.maxHealth;
    if (healthPercent < 0.5) {
      // Need more health - bonus for health multipliers
      score += (bonuses.healthMultiplier - 1) * 20;
    }
    
    // Damage analysis - always good but scales with need
    const avgEnemyHealth = 50; // Approximate
    const damageNeed = avgEnemyHealth / (player.stats.damage || 1);
    if (damageNeed > 2) {
      score += (bonuses.damageMultiplier - 1) * 15;
    }
    
    // Speed analysis - mobility is always valuable
    score += (bonuses.speedMultiplier - 1) * 10;
    
    // Special abilities bonus
    score += bonuses.specialAbilities.length * 3;
    
    return Math.max(0, score);
  }
  
  /**
   * Helper to get current player
   */
  private getPlayer(): Player | null {
    return entityManager.getPlayer();
  }
  
  // ==========================================
  // PHASE 2: MUTATION PURCHASING STRATEGY
  // ==========================================
  
  private mutationConfig: MutationConfig = {
    minPointsBeforePurchase: 10, // Wait for 10 points before spending
    prioritizeStability: true,
    prioritizePurity: true,
    maxMutationsPerWave: 2,
  };
  
  private mutationsThisWave: number = 0;
  private lastMutationCheck: number = 0;
  
  /**
   * Check and buy mutations automatically
   * Called periodically during gameplay
   */
  checkAndBuyMutations(): void {
    if (!this.enabled || !this.config.autoMutate) return;
    
    const now = Date.now();
    if (now - this.lastMutationCheck < 2000) return; // Check every 2 seconds
    this.lastMutationCheck = now;
    
    const points = dnaSystem.getMutationPoints();
    if (points < this.mutationConfig.minPointsBeforePurchase) return;
    
    const genome = dnaSystem.getGenome();
    
    // Don't buy too many mutations per wave
    if (this.mutationsThisWave >= this.mutationConfig.maxMutationsPerWave) return;
    
    // Evaluate which mutation to buy
    const bestMutation = this.evaluateBestMutation(genome, points);
    if (bestMutation) {
      const success = mutationSystem.applyMutation(bestMutation.type, bestMutation.targetDnaType);
      if (success) {
        this.mutationsThisWave++;
        console.log(`[SmartAI] Bought mutation: ${MUTATIONS[bestMutation.type].name} (${bestMutation.reason})`);
      }
    }
  }
  
  /**
   * Evaluate all mutations and return the best one to buy
   */
  private evaluateBestMutation(genome: Genome, availablePoints: number): { 
    type: MutationType; 
    targetDnaType?: DNAType; 
    reason: string;
  } | null {
    
    const candidates: Array<{
      type: MutationType;
      targetDnaType?: DNAType;
      score: number;
      reason: string;
    }> = [];
    
    // 1. GENETIC PURIFICATION - Priority if purity is low
    if (this.mutationConfig.prioritizePurity && genome.purity < 0.7) {
      const mutation = MUTATIONS[MutationType.GENETIC_PURIFICATION];
      if (availablePoints >= mutation.cost) {
        const purityGain = mutation.effect.purityIncrease || 0;
        const score = (0.7 - genome.purity) * 100 + purityGain * 50;
        candidates.push({
          type: MutationType.GENETIC_PURIFICATION,
          score,
          reason: `Low purity (${(genome.purity * 100).toFixed(0)}%), gaining ${(purityGain * 100).toFixed(0)}% purity`,
        });
      }
    }
    
    // 2. DNA STABILITY BOOST - Priority if dominant DNA is unstable
    if (this.mutationConfig.prioritizeStability) {
      const dominantStrand = genome.strands.get(genome.dominantType);
      if (dominantStrand && dominantStrand.stability < 0.7) {
        const mutation = MUTATIONS[MutationType.DNA_STABILITY_BOOST];
        if (availablePoints >= mutation.cost) {
          const stabilityGain = mutation.effect.stabilityIncrease || 0;
          const score = (0.7 - dominantStrand.stability) * 100 + stabilityGain * 50;
          candidates.push({
            type: MutationType.DNA_STABILITY_BOOST,
            targetDnaType: genome.dominantType,
            score,
            reason: `Stabilizing ${genome.dominantType} (${(dominantStrand.stability * 100).toFixed(0)}% stable)`,
          });
        }
      }
    }
    
    // 3. Check for corrupted DNA strands (stability < 0.5)
    for (const [dnaType, strand] of genome.strands) {
      if (strand.stability < 0.5 && availablePoints >= MUTATIONS[MutationType.DNA_STABILITY_BOOST].cost) {
        const mutation = MUTATIONS[MutationType.DNA_STABILITY_BOOST];
        const stabilityGain = mutation.effect.stabilityIncrease || 0;
        const score = (0.5 - strand.stability) * 150 + stabilityGain * 30; // Higher priority for corrupted
        
        candidates.push({
          type: MutationType.DNA_STABILITY_BOOST,
          targetDnaType: dnaType,
          score,
          reason: `Emergency stabilization for ${dnaType} (${(strand.stability * 100).toFixed(0)}% stable)`,
        });
      }
    }
    
    // 4. RESISTANCE BOOST - If we have points to spare
    if (availablePoints >= 20) {
      // Find most dangerous enemy type from recent history
      // For now, pick based on current DNA weaknesses
      const weakTypes = this.getWeaknesses(genome);
      if (weakTypes.length > 0) {
        const targetType = weakTypes[0];
        candidates.push({
          type: MutationType.RESISTANCE_BOOST,
          targetDnaType: targetType,
          score: 30,
          reason: `Gaining resistance to ${targetType}`,
        });
      }
    }
    
    // Sort by score descending
    candidates.sort((a, b) => b.score - a.score);
    
    if (candidates.length > 0 && candidates[0].score > 20) {
      return {
        type: candidates[0].type,
        targetDnaType: candidates[0].targetDnaType,
        reason: candidates[0].reason,
      };
    }
    
    return null;
  }
  
  /**
   * Get DNA types the player is weak against
   */
  private getWeaknesses(genome: Genome): DNAType[] {
    const weaknesses: DNAType[] = [];
    
    // Simple weakness logic based on DNA type opposites
    const weaknessMap: Record<DNAType, DNAType[]> = {
      [DNAType.FIRE]: [DNAType.WATER, DNAType.ICE],
      [DNAType.WATER]: [DNAType.LIGHTNING, DNAType.ICE],
      [DNAType.EARTH]: [DNAType.WIND, DNAType.FIRE],
      [DNAType.WIND]: [DNAType.ICE, DNAType.LIGHTNING],
      [DNAType.LIGHTNING]: [DNAType.EARTH],
      [DNAType.ICE]: [DNAType.FIRE],
      [DNAType.POISON]: [DNAType.FIRE, DNAType.LIGHTNING],
      [DNAType.VOID]: [DNAType.LIGHT],
      [DNAType.LIGHT]: [DNAType.VOID],
      [DNAType.ARCANE]: [DNAType.VOID],
      [DNAType.GRASS]: [DNAType.FIRE, DNAType.ICE],
      [DNAType.FUNGUS]: [DNAType.FIRE, DNAType.ICE],
      [DNAType.INSECT]: [DNAType.FIRE, DNAType.POISON],
      [DNAType.BEAST]: [DNAType.POISON, DNAType.ARCANE],
      [DNAType.REPTILE]: [DNAType.ICE, DNAType.EARTH],
      [DNAType.AQUATIC]: [DNAType.LIGHTNING, DNAType.POISON],
      [DNAType.PHYSICAL]: [DNAType.ARCANE],
      [DNAType.CRYSTAL]: [DNAType.PHYSICAL],
      [DNAType.SLIME]: [DNAType.FIRE, DNAType.ICE],
      [DNAType.MECH]: [DNAType.LIGHTNING, DNAType.ARCANE],
      [DNAType.CHAOS]: [DNAType.LIGHT, DNAType.ARCANE],
    };
    
    const dominantWeaknesses = weaknessMap[genome.dominantType] || [];
    
    // Check which weaknesses are actually threatening (high DNA values)
    for (const weakType of dominantWeaknesses) {
      const strand = genome.strands.get(weakType);
      if (strand && strand.value > 10) {
        weaknesses.push(weakType);
      }
    }
    
    return weaknesses;
  }
  
  /**
   * Reset mutation counter each wave
   */
  resetMutationCounter(): void {
    this.mutationsThisWave = 0;
  }
  
  // ==========================================
  // PHASE 3: BUILDING AI STRATEGY
  // ==========================================
  
  private buildingConfig = {
    minResourcesPercent: 0.3, // Keep at least 30% of resources
    maxBuildingsPerWave: 3,
    buildCooldown: 5000, // 5 seconds between building checks
    preferredDistanceFromPlayer: 150,
  };
  
  private buildingsThisWave: number = 0;
  private lastBuildingCheck: number = 0;
  private recentBuildPositions: Vector2[] = []; // Track recent builds to avoid clustering
  
  /**
   * Check and place buildings automatically
   */
  checkAndPlaceBuildings(player: Player, resources: Resources): void {
    if (!this.enabled || !this.config.autoBuild) return;
    
    const now = Date.now();
    if (now - this.lastBuildingCheck < this.buildingConfig.buildCooldown) return;
    this.lastBuildingCheck = now;
    
    // Don't build too many per wave
    if (this.buildingsThisWave >= this.buildingConfig.maxBuildingsPerWave) return;
    
    // Get available buildings sorted by priority
    const buildPriority = this.getBuildPriority(player, resources);
    
    for (const buildingType of buildPriority) {
      // Check if we can afford it (keeping reserve)
      if (!this.canAffordBuilding(buildingType, resources)) continue;
      
      // Find best position
      const position = this.findBuildPosition(buildingType, player);
      if (!position) continue;
      
      // Place the building
      const building = buildingSystem.placeBuilding(
        buildingType,
        position,
        resources as Record<string, number>
      );
      
      if (building) {
        this.buildingsThisWave++;
        this.recentBuildPositions.push(position);
        
        // Keep only last 10 positions
        if (this.recentBuildPositions.length > 10) {
          this.recentBuildPositions.shift();
        }
        
        console.log(`[SmartAI] Built ${buildingType} at (${position.x.toFixed(0)}, ${position.y.toFixed(0)})`);
        return; // Only build one per check
      }
    }
  }
  
  /**
   * Determine build priority based on game state
   */
  private getBuildPriority(player: Player, resources: Resources): BuildingType[] {
    const priority: BuildingType[] = [];
    const healthPercent = player.stats.health / player.stats.maxHealth;
    
    // High priority: Healing shrine when health is low
    if (healthPercent < 0.5) {
      priority.push(BuildingType.HEALING_SHRINE);
    }
    
    // Medium priority: Towers for defense
    const enemyCount = entityManager.getEnemies().length;
    if (enemyCount > 5) {
      priority.push(BuildingType.TOWER);
    }
    
    // Early game: Resource generator if we have resources to spare
    if (resources.gold > 100 && resources.wood > 80) {
      priority.push(BuildingType.RESOURCE_GENERATOR);
    }
    
    // Default: Walls for defense
    priority.push(BuildingType.WALL);
    
    // Fallback towers
    priority.push(BuildingType.TOWER);
    
    return [...new Set(priority)]; // Remove duplicates
  }
  
  /**
   * Check if we can afford a building while keeping resource reserves
   */
  private canAffordBuilding(type: BuildingType, resources: Resources): boolean {
    const archetype = BUILDING_ARCHETYPES[type];
    if (!archetype) return false;
    
    for (const [res, amount] of Object.entries(archetype.cost)) {
      const resourceType = res.toLowerCase() as keyof Resources;
      const current = resources[resourceType] || 0;
      const minReserve = this.getResourceReserve(resourceType);
      
      if (current < (amount as number) + minReserve) return false;
    }
    
    return true;
  }
  
  /**
   * Get minimum resource reserve based on resource type
   */
  private getResourceReserve(type: keyof Resources): number {
    const reserves: Record<string, number> = {
      wood: 30,
      stone: 20,
      gold: 25,
      mana: 10,
    };
    return reserves[type] || 10;
  }
  
  /**
   * Find optimal build position for a building type
   */
  private findBuildPosition(type: BuildingType, player: Player): Vector2 | null {
    const playerPos = player.position;
    const enemies = entityManager.getEnemies();
    
    switch (type) {
      case BuildingType.WALL:
        return this.findWallPosition(playerPos, enemies);
      case BuildingType.TOWER:
        return this.findTowerPosition(playerPos, enemies);
      case BuildingType.HEALING_SHRINE:
        return this.findShrinePosition(playerPos);
      case BuildingType.RESOURCE_GENERATOR:
        return this.findGeneratorPosition(playerPos);
      default:
        return null;
    }
  }
  
  /**
   * Find position for wall (choke point or between player and enemies)
   */
  private findWallPosition(playerPos: Vector2, enemies: Enemy[]): Vector2 | null {
    // If enemies exist, place wall between player and closest enemy
    if (enemies.length > 0) {
      const closestEnemy = enemies
        .filter(e => e.isActive)
        .sort((a, b) => 
          Vec2.distance(playerPos, a.position) - Vec2.distance(playerPos, b.position)
        )[0];
      
      if (closestEnemy) {
        const enemyDist = Vec2.distance(playerPos, closestEnemy.position);
        if (enemyDist < 300) {
          // Place wall 100 units from player toward enemy
          const dir = Vec2.normalize(Vec2.sub(closestEnemy.position, playerPos));
          const wallPos = Vec2.add(playerPos, Vec2.mul(dir, 100));
          
          if (this.isValidBuildPosition(wallPos)) {
            return wallPos;
          }
        }
      }
    }
    
    // Otherwise, place in a defensive circle around player
    const angle = Math.random() * Math.PI * 2;
    const dist = 120 + Math.random() * 50;
    const pos = {
      x: playerPos.x + Math.cos(angle) * dist,
      y: playerPos.y + Math.sin(angle) * dist,
    };
    
    return this.isValidBuildPosition(pos) ? pos : null;
  }
  
  /**
   * Find position for tower (defensive position with good coverage)
   */
  private findTowerPosition(playerPos: Vector2, _enemies: Enemy[]): Vector2 | null {
    // Place tower near player but not too close
    const angle = Math.random() * Math.PI * 2;
    const dist = 150 + Math.random() * 100;
    const pos = {
      x: playerPos.x + Math.cos(angle) * dist,
      y: playerPos.y + Math.sin(angle) * dist,
    };
    
    return this.isValidBuildPosition(pos) ? pos : null;
  }
  
  /**
   * Find position for healing shrine (close to player)
   */
  private findShrinePosition(playerPos: Vector2): Vector2 | null {
    // Place healing shrine close to player
    const angle = Math.random() * Math.PI * 2;
    const dist = 80 + Math.random() * 40;
    const pos = {
      x: playerPos.x + Math.cos(angle) * dist,
      y: playerPos.y + Math.sin(angle) * dist,
    };
    
    return this.isValidBuildPosition(pos) ? pos : null;
  }
  
  /**
   * Find position for resource generator (away from combat)
   */
  private findGeneratorPosition(playerPos: Vector2): Vector2 | null {
    // Place generator away from immediate combat but not too far
    const angle = Math.random() * Math.PI * 2;
    const dist = 200 + Math.random() * 100;
    const pos = {
      x: playerPos.x + Math.cos(angle) * dist,
      y: playerPos.y + Math.sin(angle) * dist,
    };
    
    return this.isValidBuildPosition(pos) ? pos : null;
  }
  
  /**
   * Check if position is valid for building
   */
  private isValidBuildPosition(pos: Vector2): boolean {
    // Check distance from recent builds (avoid clustering)
    for (const recentPos of this.recentBuildPositions) {
      if (Vec2.distance(pos, recentPos) < 80) {
        return false; // Too close to another building
      }
    }
    
    // Check distance from player (don't build on top of player)
    const player = this.getPlayer();
    if (player && Vec2.distance(pos, player.position) < 50) {
      return false;
    }
    
    // TODO: Check if position is within world bounds
    // TODO: Check if position collides with existing entities
    
    return true;
  }
  
  /**
   * Reset building counter each wave
   */
  resetBuildingCounter(): void {
    this.buildingsThisWave = 0;
    this.recentBuildPositions = [];
  }
  
  enable(): void {
    this.enabled = true;
    // SmartAI enabled
  }
  
  disable(): void {
    this.enabled = false;
    this.currentTarget = null;
    // SmartAI disabled
  }
  
  toggle(): boolean {
    if (this.enabled) {
      this.disable();
    } else {
      this.enable();
    }
    return this.enabled;
  }
  
  isEnabled(): boolean {
    return this.enabled;
  }
  
  /**
   * Main update - called every frame
   */
  update(deltaTime: number, player: Player | null, enemies: Enemy[], resources?: Resources): void {
    if (!this.enabled || !player) {
      this.movementVector = { x: 0, y: 0 };
      this.wantsToAttack = false;
      this.abilitySlotToUse = 0;
      return;
    }
    
    // Update cooldowns
    this.updateCooldowns(deltaTime);
    
    // Check for mutation purchases
    this.checkAndBuyMutations();
    
    // Check for building placement (if resources provided)
    if (resources) {
      this.checkAndPlaceBuildings(player, resources);
    }
    
    // Get active enemies
    const activeEnemies = enemies.filter(e => e.isActive);
    
    // Calculate strategy
    const healthPercent = player.stats.health / player.stats.maxHealth;
    const shouldRetreat = healthPercent < this.config.retreatThreshold;
    
    // Find best target
    this.currentTarget = this.selectBestTarget(player, activeEnemies);
    
    if (this.currentTarget) {
      const distance = Vec2.distance(player.position, this.currentTarget.position);
      
      // Decide movement
      if (shouldRetreat && distance < 200) {
        // Run away!
        this.movementVector = this.calculateRetreatVector(player.position, activeEnemies);
      } else if (distance > this.config.preferredRange + 50) {
        // Move closer
        this.movementVector = this.calculateApproachVector(player.position, this.currentTarget.position);
      } else if (distance < this.config.preferredRange - 30) {
        // Too close, back up
        this.movementVector = this.calculateKiteVector(player.position, this.currentTarget.position);
      } else {
        // In sweet spot, strafe
        this.movementVector = this.calculateStrafeVector(player.position, this.currentTarget.position, deltaTime);
      }
      
      // Set target for attacks
      this.targetPosition = { ...this.currentTarget.position };
      this.wantsToAttack = true;
      
      // Decide ability usage
      if (this.config.smartAbilities) {
        this.decideAbilityUsage(player, distance, activeEnemies);
      }
    } else {
      // No enemies, wander or seek
      this.movementVector = { x: 0, y: 0 };
      this.wantsToAttack = false;
      this.abilitySlotToUse = 0;
    }
  }
  
  /**
   * Select the best target based on threat and value
   */
  private selectBestTarget(player: Player, enemies: Enemy[]): Enemy | null {
    if (enemies.length === 0) return null;
    
    let bestTarget: Enemy | null = null;
    let bestScore = -Infinity;
    
    for (const enemy of enemies) {
      const distance = Vec2.distance(player.position, enemy.position);
      
      // Score factors
      const distanceScore = -distance * 0.5; // Prefer closer enemies
      const healthScore = -(enemy.stats.health / enemy.stats.maxHealth) * 20; // Prefer damaged enemies
      const threatScore = enemy.stats.damage * 2; // Prioritize dangerous enemies
      const isRanged = enemy.stats.attackRange > 50 ? 15 : 0; // Prioritize ranged enemies
      
      // Boss bonus
      const isBoss = enemy.enemyType === 'boss' ? 50 : 0;
      
      const score = distanceScore + healthScore + threatScore + isRanged + isBoss;
      
      if (score > bestScore) {
        bestScore = score;
        bestTarget = enemy;
      }
    }
    
    return bestTarget;
  }
  
  /**
   * Decide which ability to use and when
   */
  private decideAbilityUsage(player: Player, distance: number, enemies: Enemy[]): void {
    this.abilitySlotToUse = 0;
    
    // Slot 2: Dash - use to escape or close gap
    if (this.abilityCooldowns[1] <= 0) {
      const healthPercent = player.stats.health / player.stats.maxHealth;
      if (healthPercent < 0.4 && distance < 100) {
        this.abilitySlotToUse = 2; // Dash away
        this.abilityCooldowns[1] = 3; // 3s cooldown tracking
        return;
      }
    }
    
    // Slot 3-5: Special abilities - use on cooldown if mana available
    for (let slot = 3; slot <= 5; slot++) {
      if (this.abilityCooldowns[slot - 1] <= 0 && player.stats.mana > 20) {
        // Check if there are enough enemies to justify AOE
        const nearbyEnemies = enemies.filter(e => 
          Vec2.distance(player.position, e.position) < 300
        ).length;
        
        if (nearbyEnemies >= 2 || (slot === 5 && nearbyEnemies >= 1)) {
          this.abilitySlotToUse = slot;
          this.abilityCooldowns[slot - 1] = 5; // Approximate cooldown
          return;
        }
      }
    }
  }
  
  /**
   * Update ability cooldowns
   */
  private updateCooldowns(deltaTime: number): void {
    for (let i = 0; i < this.abilityCooldowns.length; i++) {
      if (this.abilityCooldowns[i] > 0) {
        this.abilityCooldowns[i] -= deltaTime;
      }
    }
  }
  
  // Movement calculations
  private calculateApproachVector(from: Vector2, to: Vector2): Vector2 {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length === 0) return { x: 0, y: 0 };
    return { x: dx / length, y: dy / length };
  }
  
  private calculateKiteVector(playerPos: Vector2, enemyPos: Vector2): Vector2 {
    const dx = playerPos.x - enemyPos.x;
    const dy = playerPos.y - enemyPos.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length === 0) return { x: 1, y: 0 };
    return { x: dx / length, y: dy / length };
  }
  
  private calculateStrafeVector(playerPos: Vector2, enemyPos: Vector2, _deltaTime: number): Vector2 {
    const dx = enemyPos.x - playerPos.x;
    const dy = enemyPos.y - playerPos.y;
    // Perpendicular direction
    const strafeFactor = Math.sin(Date.now() / 500) > 0 ? 1 : -1;
    return { x: -dy * strafeFactor * 0.7, y: dx * strafeFactor * 0.7 };
  }
  
  private calculateRetreatVector(playerPos: Vector2, enemies: Enemy[]): Vector2 {
    let totalDx = 0;
    let totalDy = 0;
    let count = 0;
    
    for (const enemy of enemies) {
      const dist = Vec2.distance(playerPos, enemy.position);
      if (dist < 300) {
        const weight = 1 / (dist + 1);
        totalDx += (enemy.position.x - playerPos.x) * weight;
        totalDy += (enemy.position.y - playerPos.y) * weight;
        count++;
      }
    }
    
    if (count === 0) return { x: 0, y: 0 };
    
    // Invert to run away
    let retreatX = -totalDx;
    let retreatY = -totalDy;
    const length = Math.sqrt(retreatX * retreatX + retreatY * retreatY);
    if (length > 0) {
      retreatX /= length;
      retreatY /= length;
    }
    
    return { x: retreatX, y: retreatY };
  }
  
  // Output methods (called by GameManager)
  getMovementVector(): Vector2 {
    return { ...this.movementVector };
  }
  
  getTargetPosition(): Vector2 {
    return { ...this.targetPosition };
  }
  
  shouldAttack(): boolean {
    return this.wantsToAttack;
  }
  
  getAbilitySlotToUse(): number {
    const slot = this.abilitySlotToUse;
    this.abilitySlotToUse = 0; // Consume
    return slot;
  }
}

export const smartAutoplaySystem = new SmartAutoplaySystem();
