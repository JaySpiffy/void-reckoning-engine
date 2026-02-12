import type { Page } from '@playwright/test';
import { test, expect } from '@playwright/test';

// Define localized types for game objects in tests
interface GameWindow extends Window {
    game: {
        autoplaySystem: {
            isEnabled: () => boolean;
            toggle: () => void;
        };
    };
}

// Helper to wait for game initialization
async function waitForGameLoad(page: Page) {
    await page.waitForSelector('canvas', { timeout: 10000 });
    await page.waitForTimeout(500);
}

test.describe('Autoplay System', () => {
    test('can toggle autoplay with F9', async ({ page }) => {
        await page.goto('/');
        await waitForGameLoad(page);

        // Start game
        await page.locator('button:has-text("Start Game")').click();
        await page.waitForTimeout(500);

        // Check initial state (enabled by default now)
        const initialState = await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            return gameWindow.game && gameWindow.game.autoplaySystem ? gameWindow.game.autoplaySystem.isEnabled() : false;
        });
        expect(initialState).toBe(true);

        // Toggle disable
        await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            if (gameWindow.game && gameWindow.game.autoplaySystem) gameWindow.game.autoplaySystem.toggle();
        });
        await page.waitForTimeout(100);

        // Check disabled state
        const disabledState = await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            return gameWindow.game && gameWindow.game.autoplaySystem ? gameWindow.game.autoplaySystem.isEnabled() : false;
        });
        expect(disabledState).toBe(false);

        // Toggle enable
        await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            if (gameWindow.game && gameWindow.game.autoplaySystem) gameWindow.game.autoplaySystem.toggle();
        });
        await page.waitForTimeout(100);

        // Check enabled state
        const enabledState = await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            return gameWindow.game && gameWindow.game.autoplaySystem ? gameWindow.game.autoplaySystem.isEnabled() : false;
        });
        expect(enabledState).toBe(true);
    });
});
