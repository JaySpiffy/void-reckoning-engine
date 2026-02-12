export * from './EntityManager';
export * from './GameManager';
export * from './LogManager';
export * from './BattleManager';
export * from './BattleGameManager';

import { GameManager } from './GameManager';
import type { GameConfig } from './GameManager';

export function createGame(config: GameConfig): GameManager {
  return new GameManager(config);
}
