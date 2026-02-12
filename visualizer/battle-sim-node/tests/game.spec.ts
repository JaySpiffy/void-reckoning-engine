import type { Page } from '@playwright/test';
import { test, expect } from '@playwright/test';

// Helper to wait for game initialization
async function waitForGameLoad(page: Page) {
  // Wait for canvas to be present
  await page.waitForSelector('canvas', { timeout: 10000 });
  // Wait a bit for game systems to initialize
  await page.waitForTimeout(500);
}

// Helper to get console logs
test.beforeEach(async ({ page }, _testInfo) => {
  // Capture console logs
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || text.includes('Error') || text.includes('FAILED')) {
      console.error(`[${type.toUpperCase()}] ${text}`);
    }
  });

  // Capture page errors
  page.on('pageerror', (err) => {
    console.error(`[PAGE ERROR] ${err.message}`);
  });
});

test.describe('Darwin\'s Island ReHelixed', () => {
  test('game loads with menu visible', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Check that the menu title is visible
    const title = page.locator('text=Darwin\'s Island ReHelixed');
    await expect(title).toBeVisible();

    // Check that Start Game button exists
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible();

    // Check canvas exists
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();

    // Verify canvas has correct dimensions
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox).not.toBeNull();
    expect(canvasBox!.width).toBeGreaterThan(0);
    expect(canvasBox!.height).toBeGreaterThan(0);
  });

  test('can start the game', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Click start button
    const startButton = page.locator('button:has-text("Start Game")');
    await startButton.click();

    // Wait for game to start
    await page.waitForTimeout(500);

    // Menu should be gone
    const title = page.locator('text=Darwin\'s Island ReHelixed');
    await expect(title).not.toBeVisible();

    // HUD elements should be visible
    const waveIndicator = page.locator('text=Wave:');
    await expect(waveIndicator).toBeVisible();

    const scoreIndicator = page.locator('text=Score:');
    await expect(scoreIndicator).toBeVisible();
  });

  test('player can move with WASD', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Start the game
    await page.locator('button:has-text("Start Game")').click();
    await page.waitForTimeout(500);

    // Press W key
    await page.keyboard.press('w');
    await page.waitForTimeout(100);
    await page.keyboard.up('w');

    // Press A key
    await page.keyboard.press('a');
    await page.waitForTimeout(100);
    await page.keyboard.up('a');

    // No errors should occur
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.waitForTimeout(500);
    expect(consoleErrors).toHaveLength(0);
  });

  test('can pause and resume game', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Start the game
    await page.locator('button:has-text("Start Game")').click();
    await page.waitForTimeout(500);

    // Press P to pause
    await page.keyboard.press('p');
    await page.waitForTimeout(1000); 

    // Pause screen should be visible
    const pausedText = page.locator('h2:has-text("Paused")');
    await expect(pausedText).toBeVisible();

    // Click resume
    const resumeButton = page.locator('button:has-text("Resume")');
    await expect(resumeButton).toBeVisible();
    await resumeButton.click();

    // Pause screen should be gone
    await expect(pausedText).not.toBeVisible();
  });

  test('can open evolution panel', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Start the game
    await page.locator('button:has-text("Start Game")').click();
    await page.waitForTimeout(1000);

    // Press T to open evolution panel
    await page.keyboard.press('t');
    await page.waitForTimeout(500);

    // Evolution panel button should be visible (Ability button has 'Ability' text)
    const evolutionButton = page.locator('button:has-text("Ability")');
    await expect(evolutionButton).toBeVisible();

    // Click the evolution button
    await evolutionButton.click();
    await page.waitForTimeout(500);
    
    // Check if the panel opened (it has "Element Evolution" heading)
    await expect(page.locator('h2:has-text("Element Evolution")')).toBeVisible();
  });

  test('game handles mouse input', async ({ page }) => {
    await page.goto('/');
    await waitForGameLoad(page);

    // Start the game
    await page.locator('button:has-text("Start Game")').click();
    await page.waitForTimeout(500);

    // Get canvas position
    const canvas = page.locator('canvas');
    const box = await canvas.boundingBox();
    expect(box).not.toBeNull();

    // Move mouse to canvas center
    await page.mouse.move(box!.x + box!.width / 2, box!.y + box!.height / 2);
    await page.waitForTimeout(100);

    // Click on canvas (should fire projectile)
    await page.mouse.down();
    await page.waitForTimeout(100);
    await page.mouse.up();
    await page.waitForTimeout(200);

    // No errors should occur
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.waitForTimeout(500);
    expect(consoleErrors).toHaveLength(0);
  });

  test('no console errors on load', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    page.on('console', (msg) => {
      const text = msg.text();
      if (msg.type() === 'error') {
        errors.push(text);
      } else if (msg.type() === 'warning' && !text.includes('[vite]')) {
        warnings.push(text);
      }
    });

    page.on('pageerror', (err) => {
      errors.push(`PageError: ${err.message}`);
    });

    await page.goto('/');
    await waitForGameLoad(page);

    // Wait for any async initialization
    await page.waitForTimeout(1000);

    // Check for critical errors (exclude non-critical warnings)
    const criticalErrors = errors.filter(e =>
      !e.includes('source map') &&
      !e.includes('React does not recognize') &&
      !e.includes('favicon')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
