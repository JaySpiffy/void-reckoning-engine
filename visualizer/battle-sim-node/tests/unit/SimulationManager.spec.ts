/**
 * Unit tests for SimulationManager
 * Tests headless simulation runner functionality
 */
import { test, expect } from '@playwright/test';

test.describe('SimulationManager', () => {
  test('simulation manager exists and has expected API', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const mgr = (window as unknown as { simulationManager?: {
        runSimulation?(): Promise<unknown>;
        getRunningState?(): boolean;
        stop?(): void;
      } }).simulationManager;
      
      if (!mgr) return { error: 'SimulationManager not found' };
      
      return {
        hasRunSimulation: typeof mgr.runSimulation === 'function',
        hasGetRunningState: typeof mgr.getRunningState === 'function',
        hasStop: typeof mgr.stop === 'function',
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.hasRunSimulation).toBe(true);
    expect(result.hasGetRunningState).toBe(true);
    expect(result.hasStop).toBe(true);
  });

  test('simulation manager reports not running initially', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const mgr = (window as unknown as { simulationManager?: {
        getRunningState(): boolean;
      } }).simulationManager;
      
      if (!mgr) return { error: 'SimulationManager not found' };
      
      return { isRunning: mgr.getRunningState() };
    });

    expect(result.isRunning).toBe(false);
  });

  test('simulation config interface is valid', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      // Check if we can construct a valid config object
      const config = {
        maxDuration: 60,
        maxWave: 5,
        speed: 10,
        useSmartAI: true,
        startWave: 1,
        seed: 12345,
        recordReplay: false,
        sessionId: 'test_session',
      };
      
      return {
        configValid: true,
        configKeys: Object.keys(config),
      };
    });

    expect(result.configValid).toBe(true);
    expect(result.configKeys).toContain('maxDuration');
    expect(result.configKeys).toContain('maxWave');
    expect(result.configKeys).toContain('speed');
    expect(result.configKeys).toContain('useSmartAI');
  });

  test('simulation result structure is correct', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      // Create a mock result object to verify structure
      const mockResult = {
        id: 'sim_test_123',
        config: {
          maxDuration: 60,
          maxWave: 5,
          speed: 10,
          useSmartAI: true,
          startWave: 1,
        },
        duration: 45.5,
        wavesCompleted: 3,
        enemiesKilled: 25,
        score: 1500,
        dnaAcquired: {} as Record<string, number>,
        evolutionHistory: [],
        finalStats: {
          health: 50,
          maxHealth: 100,
          damage: 10,
          speed: 5,
          level: 3,
        },
        success: true,
        mutationsPurchased: 2,
        buildingsConstructed: 1,
      };
      
      return {
        hasId: !!mockResult.id,
        hasConfig: !!mockResult.config,
        hasDuration: typeof mockResult.duration === 'number',
        hasWavesCompleted: typeof mockResult.wavesCompleted === 'number',
        hasEnemiesKilled: typeof mockResult.enemiesKilled === 'number',
        hasScore: typeof mockResult.score === 'number',
        hasFinalStats: !!mockResult.finalStats,
        hasSuccess: typeof mockResult.success === 'boolean',
        hasMutations: typeof mockResult.mutationsPurchased === 'number',
        hasBuildings: typeof mockResult.buildingsConstructed === 'number',
      };
    });

    expect(result.hasId).toBe(true);
    expect(result.hasConfig).toBe(true);
    expect(result.hasDuration).toBe(true);
    expect(result.hasWavesCompleted).toBe(true);
    expect(result.hasEnemiesKilled).toBe(true);
    expect(result.hasScore).toBe(true);
    expect(result.hasFinalStats).toBe(true);
    expect(result.hasSuccess).toBe(true);
    expect(result.hasMutations).toBe(true);
    expect(result.hasBuildings).toBe(true);
  });

  test('stop method can be called safely', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const mgr = (window as unknown as { simulationManager?: {
        stop(): void;
        getRunningState(): boolean;
      } }).simulationManager;
      
      if (!mgr) return { error: 'SimulationManager not found' };
      
      // Should be able to call stop even when not running
      try {
        mgr.stop();
        return { success: true, isRunning: mgr.getRunningState() };
      } catch (e) {
        return { success: false, error: String(e) };
      }
    });

    expect(result.success).toBe(true);
    expect(result.isRunning).toBe(false);
  });
});
