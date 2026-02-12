#!/bin/bash

# ============================================
# DARWIN'S ISLAND - VISUAL AUTOMATION
# ============================================

echo "📸 Running Visual Verification..."

# 1. Clear previous artifacts
rm -rf test-results/screenshots/*.png

# 2. Run Playwright Visual Test
npx playwright test visual-test.spec.ts --reporter=list

# 3. Check for errors
if [ $? -eq 0 ]; then
    echo "✅ Visual tests passed!"
    echo "Files generated in test-results/screenshots/:"
    ls -lh test-results/screenshots/*.png
else
    echo "❌ Visual tests failed. See test-results/ for details."
fi

echo "📊 Console logs summary:"
tail -n 20 test-results/screenshots/console-logs.txt
