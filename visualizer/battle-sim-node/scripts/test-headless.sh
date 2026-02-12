#!/bin/bash
# Run tests headlessly

echo "🧪 Running headless tests..."
cd "$(dirname "$0")/.."

# Run playwright tests
npx playwright test --reporter=line "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed"
fi

exit $EXIT_CODE
