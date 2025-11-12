#!/bin/bash
#
# Run Harbor job locally with DeepAgents
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "Harbor + DeepAgents + LangSmith Demo"
echo "========================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠${NC} No .env file found. Using environment variables..."
fi

# Require explicit model selection
if [ -z "$MODEL_NAME" ]; then
    echo -e "${RED}✗${NC} Error: MODEL_NAME not set"
    echo "   Example: MODEL_NAME=openai/gpt-5-mini bash scripts/run_local.sh"
    exit 1
fi

echo "Using model: $MODEL_NAME"

# Check required provider keys based on selected model
if [[ "$MODEL_NAME" == openai/* || "$MODEL_NAME" == gpt-* ]]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}✗${NC} Error: OPENAI_API_KEY not set for model $MODEL_NAME"
        echo "   Please set it in .env or export it"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY is set"
elif [[ "$MODEL_NAME" == anthropic/* || "$MODEL_NAME" == claude-* ]]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}✗${NC} Error: ANTHROPIC_API_KEY not set for model $MODEL_NAME"
        echo "   Please set it in .env or export it"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} ANTHROPIC_API_KEY is set"
else
    echo -e "${YELLOW}⚠${NC} Unknown provider for model '$MODEL_NAME'. Skipping API key check."
fi

if [ -z "$LANGCHAIN_API_KEY" ]; then
    echo -e "${YELLOW}⚠${NC} Warning: LANGCHAIN_API_KEY not set"
    echo "   LangSmith tracing will be disabled"
else
    echo -e "${GREEN}✓${NC} LANGCHAIN_API_KEY is set"
    echo -e "${GREEN}✓${NC} LangSmith tracing enabled"
fi

echo ""
echo "Starting Harbor job with DeepAgents..."
echo ""

# Run Harbor job
harbor run --config configs/job.yaml

echo ""
echo -e "${GREEN}========================================="
echo "Job Complete!"
echo "=========================================${NC}"
echo ""
echo "Results location:"
echo "  → Job results: jobs/<job-name>/result.json"
echo "  → Trajectories: jobs/<job-name>/<trial>/agent/trajectory.json"
echo ""

if [ ! -z "$LANGCHAIN_API_KEY" ]; then
    echo "LangSmith Dashboard:"
    echo "  → https://smith.langchain.com"
    echo ""
fi

echo "Next steps:"
echo "  1. View results: cat jobs/*/result.json | jq '.'"
echo "  2. Export to LangSmith: python scripts/export_traces.py"
echo "  3. Deploy to Modal: modal run scripts/run_modal.py"
