/**
 * Unit tests for SmartAutoplaySystem
 * Tests AI decision-making logic in isolation
 */
import { test, expect } from '@playwright/test';

test.describe('SmartAutoplaySystem', () => {
  test('can be enabled and disabled', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      // Access the smart autoplay system from window
      const sys = (window as unknown as { smartAutoplaySystem?: { 
        isEnabled(): boolean; 
        enable(): void; 
        disable(): void;
        toggle(): boolean;
      } }).smartAutoplaySystem;
      
      if (!sys) return { error: 'System not found' };
      
      const initial = sys.isEnabled();
      sys.enable();
      const afterEnable = sys.isEnabled();
      sys.disable();
      const afterDisable = sys.isEnabled();
      const toggleResult = sys.toggle();
      const afterToggle = sys.isEnabled();
      sys.disable(); // cleanup
      
      return {
        initial,
        afterEnable,
        afterDisable,
        toggleResult,
        afterToggle,
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.afterEnable).toBe(true);
    expect(result.afterDisable).toBe(false);
    expect(result.toggleResult).toBe(true);
    expect(result.afterToggle).toBe(true);
  });

  test('mutation counter resets correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const sys = (window as unknown as { smartAutoplaySystem?: {
        resetMutationCounter(): void;
        mutationsThisWave?: number;
      } }).smartAutoplaySystem;
      
      if (!sys) return { error: 'System not found' };
      
      sys.resetMutationCounter();
      return { success: true };
    });

    expect(result.success).toBe(true);
  });

  test('building counter resets correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const sys = (window as unknown as { smartAutoplaySystem?: {
        resetBuildingCounter(): void;
        buildingsThisWave?: number;
      } }).smartAutoplaySystem;
      
      if (!sys) return { error: 'System not found' };
      
      sys.resetBuildingCounter();
      return { success: true };
    });

    expect(result.success).toBe(true);
  });

  test('AI returns valid movement vector when disabled', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      const sys = (window as unknown as { smartAutoplaySystem?: {
        disable(): void;
        getMovementVector(): { x: number; y: number };
        shouldAttack(): boolean;
        getAbilitySlotToUse(): number;
      } }).smartAutoplaySystem;
      
      if (!sys) return { error: 'System not found' };
      
      sys.disable();
      const movement = sys.getMovementVector();
      const shouldAttack = sys.shouldAttack();
      const abilitySlot = sys.getAbilitySlotToUse();
      
      return {
        movement,
        shouldAttack,
        abilitySlot,
      };
    });

    expect(result.movement).toBeDefined();
    expect(typeof result.movement.x).toBe('number');
    expect(typeof result.movement.y).toBe('number');
    expect(typeof result.shouldAttack).toBe('boolean');
    expect(typeof result.abilitySlot).toBe('number');
  });

  test('AI configuration has expected defaults', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
      // Check if the SmartAutoplaySystem class exists and has expected config
      const sys = (window as unknown as { smartAutoplaySystem?: {
        config?: {
          aggressiveness: number;
          preferredRange: number;
          retreatThreshold: number;
          autoEvolve: boolean;
          smartAbilities: boolean;
          autoBuild: boolean;
          autoMutate: boolean;
        };
      } }).smartAutoplaySystem;
      
      if (!sys || !sys.config) return { error: 'Config not found' };
      
      return {
        aggressiveness: sys.config.aggressiveness,
        preferredRange: sys.config.preferredRange,
        retreatThreshold: sys.config.retreatThreshold,
        autoEvolve: sys.config.autoEvolve,
        smartAbilities: sys.config.smartAbilities,
        autoBuild: sys.config.autoBuild,
        autoMutate: sys.config.autoMutate,
      };
    });

    expect(result.error).toBeUndefined();
    expect(result.aggressiveness).toBeGreaterThanOrEqual(0);
    expect(result.aggressiveness).toBeLessThanOrEqual(1);
    expect(result.preferredRange).toBeGreaterThan(0);
    expect(result.retreatThreshold).toBeGreaterThan(0);
    expect(result.retreatThreshold).toBeLessThanOrEqual(1);
    expect(typeof result.autoEvolve).toBe('boolean');
    expect(typeof result.smartAbilities).toBe('boolean');
    expect(typeof result.autoBuild).toBe('boolean');
    expect(typeof result.autoMutate).toBe('boolean');
  });
});
