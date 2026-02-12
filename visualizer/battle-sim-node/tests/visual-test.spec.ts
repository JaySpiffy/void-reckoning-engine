import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('take screenshot of game running', async ({ page }) => {
  // Collect console logs
  const logs: string[] = [];
  page.on('console', (msg) => {
    const text = msg.text();
    logs.push(`[${msg.type()}] ${text}`);
     
    if (msg.type() === 'error') console.error(`[${msg.type()}] ${text}`);
  });

  page.on('pageerror', (err) => {
    logs.push(`[ERROR] ${err.message}`);
     
    console.error(`[PAGE ERROR] ${err.message}`);
  });

  // Navigate to game
  await page.goto('/');

  // Wait for canvas
  await page.waitForSelector('canvas', { timeout: 15000 });
  await page.waitForTimeout(1000);

  // Take screenshot of menu
  // Take screenshot of menu
  const screenshotDir = path.join(process.cwd(), 'test-results', 'screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  await page.screenshot({
    path: path.join(screenshotDir, '01-menu.png'),
    fullPage: true
  });

  // Click start game
  await page.locator('button:has-text("Start Game")').click();
  
  // Wait for game loop to stabilize and enemies to move on screen
  // Enemies spawn at ~400 distance, player speed ~300. 2-3 seconds ensures contact.
  await page.waitForTimeout(3000);

  // Take screenshot of gameplay
  await page.screenshot({
    path: path.join(screenshotDir, '02-gameplay.png'),
    fullPage: true
  });

  // Move around
  await page.keyboard.press('w');
  await page.waitForTimeout(200);
  await page.keyboard.press('a');
  await page.waitForTimeout(200);
  await page.keyboard.press('s');
  await page.waitForTimeout(200);
  await page.keyboard.press('d');
  await page.waitForTimeout(200);

  // Click to shoot
  const canvas = page.locator('canvas');
  const box = await canvas.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.waitForTimeout(500);
    await page.mouse.up();
  }

  await page.waitForTimeout(500);

  // Take screenshot after movement and shooting
  await page.screenshot({
    path: path.join(screenshotDir, '03-action.png'),
    fullPage: true
  });

  // --- Capture Specific Panels ---

  // 1. Open DNA Evolution Panel (Y)
  await page.keyboard.press('y');
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, '04-dna-panel.png'), fullPage: true });
  await page.keyboard.press('y'); // Close
  await page.waitForTimeout(200);

  // 2. Open Mutation Shop (M)
  await page.keyboard.press('m');
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, '05-mutation-shop.png'), fullPage: true });
  await page.keyboard.press('m'); // Close
  await page.waitForTimeout(200);

  // 3. Open Build Menu (B)
  await page.keyboard.press('b');
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, '06-build-menu.png'), fullPage: true });
  await page.keyboard.press('Escape'); // Close / Cancel placement
  await page.waitForTimeout(200);

  // 4. Open Ability Evolution (T)
  await page.keyboard.press('t');
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, '07-ability-evolution.png'), fullPage: true });
  await page.keyboard.press('t'); // Close
  await page.waitForTimeout(200);

  // Save logs
  fs.writeFileSync(
    path.join(screenshotDir, 'console-logs.txt'),
    logs.join('\n')
  );

  // Verify no critical errors
  const errors = logs.filter(l =>
    l.includes('[error]') ||
    l.includes('[ERROR]') ||
    l.includes('FAILED')
  );

  /* eslint-disable no-console */
  console.log(`\n=== Test Summary ===`);
  console.log(`Total logs: ${logs.length}`);
  console.log(`Errors: ${errors.length}`);

  if (errors.length > 0) {
    console.log('Errors found:');
    errors.forEach(e => console.log(`  - ${e}`));
  }
  /* eslint-enable no-console */

  // Assert game is working
  expect(errors.filter(e =>
    !e.includes('source map') &&
    !e.includes('favicon')
  )).toHaveLength(0);
});
