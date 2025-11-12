#!/bin/bash

set -e

# Run the scraper first (if it exists)
if [ -f "/app/scraper.py" ]; then
    echo "Running scraper.py..."
    python /app/scraper.py || echo "Warning: scraper.py execution failed"
fi

# Run pytest with CTRF JSON output
echo "Running tests..."
pytest /tests/test_solution.py \
    --ctrf /logs/verifier/ctrf.json \
    -v \
    --tb=short

exit_code=$?

# Write reward based on test results
if [ $exit_code -eq 0 ]; then
    echo "All tests passed!"
    echo "1.0" > /logs/verifier/reward.txt
    echo '{"reward": 1.0, "passed": true, "tests": "all"}' > /logs/verifier/reward.json
else
    echo "Some tests failed"
    echo "0.0" > /logs/verifier/reward.txt
    echo '{"reward": 0.0, "passed": false, "tests": "some_failed"}' > /logs/verifier/reward.json
fi

# Always exit 0 so Harbor can collect results
exit 0
