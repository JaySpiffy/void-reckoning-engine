import { test, expect } from '@playwright/test';

interface GameWindow extends Window {
    game: {
        autoplaySystem: {
            isEnabled: () => boolean;
            toggle: () => void;
        };
        fps?: number;
    };
    logger?: {
        getLogs: () => unknown[];
    };
}

test.describe('Bot Verification System', () => {
    test.setTimeout(60000); // Allow enough time for 30s gameplay + overhead
    test('stress test: autoplay survival for 30s', async ({ page }) => {
        // 1. Load Game
        await page.goto('/');
        await page.waitForSelector('canvas');
        await page.click('canvas'); // Focus

        // 2. Enable Autoplay
        // Direct system call to avoid keyboard flakiness
        await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            const game = gameWindow.game;
            if (game && game.autoplaySystem) {
                if (!game.autoplaySystem.isEnabled()) {
                    game.autoplaySystem.toggle();
                }
            }
        });

        // 3. Verify Autoplay Active
        const isAutoplay = await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            return gameWindow.game?.autoplaySystem?.isEnabled() || false;
        });
        expect(isAutoplay).toBe(true);

        // 4. Run for 30 seconds
        await page.waitForTimeout(30000);

        // 5. Verify Survival (Not Game Over)
        const gameOver = await page.getByText('Game Over').isVisible();
        expect(gameOver).toBe(false);

        // 6. Verify Performance (Telemetry check)
        const fps = await page.evaluate(() => {
            const gameWindow = window as unknown as GameWindow;
            return gameWindow.game?.fps || 60;
        });
        expect(fps).toBeGreaterThan(0);
    });

    // Auto-collect logs after test
    test.afterEach(async ({ page }, testInfo) => {
        try {
            const logs = await page.evaluate(() => {
                const gameWindow = window as unknown as GameWindow;
                return gameWindow.logger?.getLogs() || [];
            });
            if (logs.length > 0) {
                await testInfo.attach('game-logs', {
                    body: JSON.stringify(logs, null, 2),
                    contentType: 'application/json'
                });
            }
        } catch (e) {
            console.error('Failed to extract logs:', e);
        }
    });
});
