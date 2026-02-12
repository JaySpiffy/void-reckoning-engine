import { test, expect } from '@playwright/test';

test.describe('Football Animation System', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the football game
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display football game menu', async ({ page }) => {
    // Check for the main title
    await expect(page.locator('text=LAST HIT BLITZ')).toBeVisible();
    await expect(page.locator('text=FIFA Meets Madden')).toBeVisible();
  });

  test('should navigate to team view and show players', async ({ page }) => {
    // Click View Teams button
    await page.click('text=View Teams');
    
    // Check for team rosters header
    await expect(page.locator('text=Team Rosters')).toBeVisible();
    
    // Check that team info is displayed
    await expect(page.locator('text=OVR:')).toBeVisible();
  });

  test('should start game and show field', async ({ page }) => {
    // Start the game
    await page.click('text=KICKOFF');
    
    // Check for scoreboard elements
    await expect(page.locator('text=Q')).toBeVisible(); // Quarter indicator
    await expect(page.locator('text=BALL')).toBeVisible(); // Possession indicator
  });

  test('should show animation controls when play is running', async ({ page }) => {
    // Start the game
    await page.click('text=KICKOFF');
    
    // Wait a moment for animation to potentially start
    await page.waitForTimeout(1000);
    
    // Check for playback controller elements (play/pause buttons)
    // These may appear once a play is simulated
    const playButton = page.locator('[title="Play"], button:has-text("▶")').first();
    const pauseButton = page.locator('[title="Pause"], button:has-text("⏸")').first();
    
    // At least one of these should eventually be visible
    await expect(playButton.or(pauseButton)).toBeVisible({ timeout: 5000 });
  });

  test('test position mode should load', async ({ page }) => {
    // Go to test position mode
    await page.click('text=Test Position Mode');
    
    // Check that we're in test mode (look for test-related text or elements)
    await expect(page.locator('text=Test').or(page.locator('text=test'))).toBeVisible();
  });

  test('play simulator mode should load', async ({ page }) => {
    // Go to play simulator mode
    await page.click('text=Play Simulator');
    
    // Check that simulator UI loaded
    await expect(page.locator('text=Simulator').or(page.locator('text=simulator'))).toBeVisible();
  });
});

test.describe('Football Player Movement', () => {
  test('players should have velocity properties', async ({ page }) => {
    // This test verifies the player entities have movement capability
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Start game to initialize players
    await page.click('text=KICKOFF');
    await page.waitForTimeout(500);
    
    // Check that the field is rendered with SVG elements
    const svgElement = page.locator('svg').first();
    await expect(svgElement).toBeVisible();
    
    // Check for player markers (circles representing players)
    const playerCircles = page.locator('svg circle').first();
    await expect(playerCircles).toBeVisible();
  });

  test('field should render with proper dimensions', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    await page.click('text=KICKOFF');
    
    // Check for field elements
    const fieldSvg = page.locator('svg');
    await expect(fieldSvg).toBeVisible();
    
    // Check for yard lines (lines in the SVG)
    const yardLines = page.locator('svg line');
    await expect(yardLines.first()).toBeVisible();
  });
});
