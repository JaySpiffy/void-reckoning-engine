/**
 * Unit tests for Simulation Infrastructure
 * Tests SimulationLogger, SimulationMetrics, and SimulationReplay
 */
import { test, expect } from '@playwright/test';

test.describe('SimulationLogger', () => {
  test('simulation logger exists with expected API', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const logger = (window as unknown as { simulationLogger?: {
        startSession?(config: unknown): string;
        endSession?(): unknown;
        logResult?(result: unknown): void;
        getCurrentStats?(): unknown;
        getSessionDuration?(): number;
        getSavedSessions?(): unknown[];
      } }).simulationLogger;
      
      if (!logger) return { error: 'SimulationLogger not found' };
      
      return {
        hasStartSession: typeof logger.startSession === 'function',
        hasEndSession: typeof logger.endSession === 'function',
        hasLogResult: typeof logger.logResult === 'function',
        hasGetCurrentStats: typeof logger.getCurrentStats === 'function',
        hasGetSessionDuration: typeof logger.getSessionDuration === 'function',
        hasGetSavedSessions: typeof logger.getSavedSessions === 'function',
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.hasStartSession).toBe(true);
    expect(result.hasEndSession).toBe(true);
    expect(result.hasLogResult).toBe(true);
    expect(result.hasGetCurrentStats).toBe(true);
    expect(result.hasGetSessionDuration).toBe(true);
    expect(result.hasGetSavedSessions).toBe(true);
  });

  test('can start and end session', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const logger = (window as unknown as { simulationLogger?: {
        startSession(config: unknown): string;
        endSession(): { id: string } | null;
        getSessionDuration(): number;
      } }).simulationLogger;
      
      if (!logger) return { error: 'SimulationLogger not found' };
      
      try {
        const sessionId = logger.startSession({
          maxDuration: 60,
          maxWave: 5,
          speed: 10,
          useSmartAI: true,
          startWave: 1,
        });
        
        const session = logger.endSession();
        const duration = logger.getSessionDuration();
        
        return {
          success: true,
          sessionId: sessionId.startsWith('sess_'),
          hasSession: !!session,
          duration,
        };
      } catch (e) {
        return { success: false, error: String(e) };
      }
    });

    expect(result.success).toBe(true);
    expect(result.sessionId).toBe(true);
    expect(result.hasSession).toBe(true);
    expect(typeof result.duration).toBe('number');
  });

  test('getSavedSessions returns array', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const logger = (window as unknown as { simulationLogger?: {
        getSavedSessions(): unknown[];
      } }).simulationLogger;
      
      if (!logger) return { error: 'SimulationLogger not found' };
      
      const sessions = logger.getSavedSessions();
      return {
        isArray: Array.isArray(sessions),
        length: sessions.length,
      };
    });

    expect(result.isArray).toBe(true);
    expect(typeof result.length).toBe('number');
  });
});

test.describe('SimulationMetrics', () => {
  test('simulation metrics exists with expected API', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const metrics = (window as unknown as { simulationMetrics?: {
        startSession?(sessionId: string): void;
        recordSnapshot?(snapshot: unknown): void;
        endSession?(result?: unknown): unknown[];
        calculateBatchMetrics?(results: unknown[]): unknown;
      } }).simulationMetrics;
      
      if (!metrics) return { error: 'SimulationMetrics not found' };
      
      return {
        hasStartSession: typeof metrics.startSession === 'function',
        hasRecordSnapshot: typeof metrics.recordSnapshot === 'function',
        hasEndSession: typeof metrics.endSession === 'function',
        hasCalculateBatchMetrics: typeof metrics.calculateBatchMetrics === 'function',
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.hasStartSession).toBe(true);
    expect(result.hasRecordSnapshot).toBe(true);
    expect(result.hasEndSession).toBe(true);
    expect(result.hasCalculateBatchMetrics).toBe(true);
  });

  test('can start session and record snapshots', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const metrics = (window as unknown as { simulationMetrics?: {
        startSession(sessionId: string): void;
        recordSnapshot(snapshot: unknown): void;
        endSession(): unknown[];
      } }).simulationMetrics;
      
      if (!metrics) return { error: 'SimulationMetrics not found' };
      
      try {
        metrics.startSession('test_metrics_session');
        
        metrics.recordSnapshot({
          timestamp: Date.now(),
          gameTime: 10.5,
          wave: 2,
          playerHealth: 80,
          playerPosition: { x: 100, y: 200 },
          enemyCount: 5,
          dnaDistribution: {},
          activeAbilities: ['Fireball'],
        });
        
        const snapshots = metrics.endSession();
        
        return {
          success: true,
          snapshotCount: snapshots.length,
        };
      } catch (e) {
        return { success: false, error: String(e) };
      }
    });

    expect(result.success).toBe(true);
    expect(result.snapshotCount).toBeGreaterThanOrEqual(0);
  });

  test('calculateBatchMetrics returns expected structure', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const metrics = (window as unknown as { simulationMetrics?: {
        calculateBatchMetrics(results: unknown[]): {
          survival: {
            rate: number;
            avgWaves: number;
            medianWaves: number;
            bestRun: number;
          };
          performance: {
            avgScore: number;
            avgKills: number;
            avgDuration: number;
            totalEvolutions: number;
          };
          dna: {
            typeDistribution: Record<string, number>;
            purityDistribution: { low: number; medium: number; high: number };
            dominantTypes: Record<string, number>;
          };
          buildings: {
            avgPerRun: number;
            typeDistribution: Record<string, number>;
          };
          mutations: {
            avgPerRun: number;
            typeDistribution: Record<string, number>;
          };
        };
      } }).simulationMetrics;
      
      if (!metrics) return { error: 'SimulationMetrics not found' };
      
      try {
        const mockResults = [
          {
            id: 'sim_1',
            success: true,
            wavesCompleted: 5,
            score: 1000,
            enemiesKilled: 20,
            duration: 60,
            evolutionHistory: [{ wave: 2, path: 'fire', name: 'Fire' }],
            dnaAcquired: { FIRE: 10 },
            mutationsPurchased: 2,
            buildingsConstructed: 1,
          },
        ];
        
        const batchMetrics = metrics.calculateBatchMetrics(mockResults);
        
        return {
          success: true,
          hasSurvival: !!batchMetrics.survival,
          hasPerformance: !!batchMetrics.performance,
          hasDna: !!batchMetrics.dna,
          hasBuildings: !!batchMetrics.buildings,
          hasMutations: !!batchMetrics.mutations,
          survivalRate: batchMetrics.survival.rate,
          avgWaves: batchMetrics.survival.avgWaves,
        };
      } catch (e) {
        return { success: false, error: String(e) };
      }
    });

    expect(result.success).toBe(true);
    expect(result.hasSurvival).toBe(true);
    expect(result.hasPerformance).toBe(true);
    expect(result.hasDna).toBe(true);
    expect(result.hasBuildings).toBe(true);
    expect(result.hasMutations).toBe(true);
    expect(typeof result.survivalRate).toBe('number');
    expect(typeof result.avgWaves).toBe('number');
  });
});

test.describe('SimulationReplay', () => {
  test('simulation replay exists with expected API', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const replay = (window as unknown as { simulationReplay?: {
        startRecording?(config: unknown): string;
        recordFrame?(gameTime: number, frameData: unknown): void;
        recordDecision?(decision: unknown, gameTime: number): void;
        stopRecording?(finalResult: unknown): unknown;
        getReplay?(id: string): unknown;
        getSavedReplays?(): unknown[];
        isCurrentlyRecording?(): boolean;
        getRecordingProgress?(): { time: number; frames: number } | null;
      } }).simulationReplay;
      
      if (!replay) return { error: 'SimulationReplay not found' };
      
      return {
        hasStartRecording: typeof replay.startRecording === 'function',
        hasRecordFrame: typeof replay.recordFrame === 'function',
        hasRecordDecision: typeof replay.recordDecision === 'function',
        hasStopRecording: typeof replay.stopRecording === 'function',
        hasGetReplay: typeof replay.getReplay === 'function',
        hasGetSavedReplays: typeof replay.getSavedReplays === 'function',
        hasIsCurrentlyRecording: typeof replay.isCurrentlyRecording === 'function',
        hasGetRecordingProgress: typeof replay.getRecordingProgress === 'function',
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.hasStartRecording).toBe(true);
    expect(result.hasRecordFrame).toBe(true);
    expect(result.hasRecordDecision).toBe(true);
    expect(result.hasStopRecording).toBe(true);
    expect(result.hasGetReplay).toBe(true);
    expect(result.hasGetSavedReplays).toBe(true);
    expect(result.hasIsCurrentlyRecording).toBe(true);
    expect(result.hasGetRecordingProgress).toBe(true);
  });

  test('can start and stop recording', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const replay = (window as unknown as { simulationReplay?: {
        startRecording(config: unknown): string;
        stopRecording(finalResult: unknown): { id: string } | null;
        isCurrentlyRecording(): boolean;
        getRecordingProgress(): { time: number; frames: number } | null;
      } }).simulationReplay;
      
      if (!replay) return { error: 'SimulationReplay not found' };
      
      try {
        const replayId = replay.startRecording({
          speed: 10,
          useSmartAI: true,
          maxDuration: 60,
        });
        
        const isRecording = replay.isCurrentlyRecording();
        const progress = replay.getRecordingProgress();
        
        const stopped = replay.stopRecording({
          wavesCompleted: 5,
          score: 1000,
          success: true,
        });
        
        const afterStop = replay.isCurrentlyRecording();
        
        return {
          success: true,
          replayId: replayId.startsWith('replay_'),
          isRecording,
          hasProgress: !!progress,
          stopped: !!stopped,
          afterStop,
        };
      } catch (e) {
        return { success: false, error: String(e) };
      }
    });

    expect(result.success).toBe(true);
    expect(result.replayId).toBe(true);
    expect(result.isRecording).toBe(true);
    expect(result.hasProgress).toBe(true);
    expect(result.stopped).toBe(true);
    expect(result.afterStop).toBe(false);
  });

  test('getSavedReplays returns array', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const replay = (window as unknown as { simulationReplay?: {
        getSavedReplays(): unknown[];
      } }).simulationReplay;
      
      if (!replay) return { error: 'SimulationReplay not found' };
      
      const replays = replay.getSavedReplays();
      return {
        isArray: Array.isArray(replays),
        length: replays.length,
      };
    });

    expect(result.isArray).toBe(true);
    expect(typeof result.length).toBe('number');
  });
});
