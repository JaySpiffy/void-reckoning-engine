#!/bin/bash
# Full validation script - run before committing

echo "🔍 Running validation checks..."
cd "$(dirname "$0")/.."

EXIT_CODE=0

# Type checking
echo ""
echo "📋 Type checking..."
npx tsc --noEmit
if [ $? -ne 0 ]; then
    echo "❌ Type checking failed"
    EXIT_CODE=1
else
    echo "✅ Type checking passed"
fi

# Linting
echo ""
echo "🔧 Linting..."
npx eslint . --max-warnings=0
if [ $? -ne 0 ]; then
    echo "❌ Linting failed"
    EXIT_CODE=1
else
    echo "✅ Linting passed"
fi

# Build test
echo ""
echo "📦 Build test..."
npx vite build 2>&1 | grep -E "(error|Error|failed|Failed)" > /dev/null
if [ $? -eq 0 ]; then
    echo "❌ Build failed"
    EXIT_CODE=1
else
    echo "✅ Build passed"
fi

# Summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 All validations passed!"
else
    echo "⚠️  Some validations failed. Fix before committing."
fi

exit $EXIT_CODE
