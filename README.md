# Building DeepAgent Harnesses for Terminal Bench 2.0 with Harbor

Build, evaluate, and improve custom agents on Terminal Bench 2.0 with **DeepAgents** (LangChain's agent framework), **Harbor** (a framework for running agents in container environments), and **LangSmith** (built in logging and observability).

## What is This?

This repo provides a **DeepAgent harness** - a complete agent implementation built on [LangChain DeepAgents](https://github.com/langchain-ai/deepagents) that can:

- **Run Harbor tasks** - Execute any Harbor benchmark in sandboxed environments
- **Customize your agent harnesses** - Modify prompts, tools, and behavior for your use case
- **Log to LangSmith** - Automatically trace all runs with full observability
- **Measure & improve** - Analyze traces to optimize your agent harness design


## Supported Sandbox Providers
Run your agent in multiple execution environments:
- 🐳 **Docker** (local)
- ☁️ **Modal, Daytona, E2B** - Cloud sandboxes

## Quick Start

### 1. Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/vtrivedy/harbor-deepagents
cd harbor-deepagents
uv python install 3.12
uv sync --no-editable
uv tool install harbor

# IMPORTANT: Rebuild after making code changes
# Run this again if Terminal Bench errors (working on a cleaner fix for custom harnesses)
uv sync --no-editable
```

### 2. Configuration

Create a `.env` file with your API keys:

```bash
# Required: Model provider API key
OPENAI_API_KEY=sk-proj-...                      # For GPT models
# OR
ANTHROPIC_API_KEY=sk-ant-...                    # For Claude models

# Optional: LangSmith tracing (recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=...

# Optional: Cloud sandbox providers
# NOTE: Sandbox environments may have issues with downloading uv, python, container definition
DAYTONA_API_KEY=dtn_...                         # Daytona
modal setup                                     # Modal
```

### 3. Run Your First Task

```bash
# Run the web-scraper demo task
uv run harness --model openai/gpt-5-mini

# Or use MODEL_NAME from .env
uv run harness

# View results
cat jobs/*/result.json | jq '.reward_stats.mean'
```

### 4. Run Terminal Bench 2.0

```bash
# Single task (Docker local)
uv run tb-docker --task prove-plus-comm --model openai/gpt-5-mini

# Full benchmark suite
uv run tb-docker --model openai/gpt-5-mini

# Cloud sandboxes (Daytona/Modal)
# NOTE: Sandbox environments may have issues with downloading uv, python, container definition
uv run tb-daytona --task prove-plus-comm --model anthropic/claude-sonnet-4-5-20250620
```

Each run creates a unique job folder: `<config>-<task>-<model>-<timestamp>`. Override with `--job-name my-run`.


### 5. View Traces in LangSmith

Enable tracing in `.env`:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT=your-project-name
```

View traces at https://smith.langchain.com - Harbor reward scores are automatically logged as feedback.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│              Harbor Orchestrator                        │
│   (Manages task execution across sandbox providers)     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────┐
│                    DeepAgent Harness                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ LangChain 1.0 + DeepAgents Framework                │ │─────▶ LangSmith
│  │ • Planning (write_todos)                            │ │       (Traces +
│  │ • Real Filesystem (FilesystemBackend)               │ │        Feedback)
│  │ • Subagents (task tool)                             │ │
│  │ • Custom Tools (bash from Harbor)                   │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────┐
│            Sandbox Environment (choose one)               │
│  • Docker (local) • Modal (cloud) • Daytona • E2B        │
│                                                           │
│  Provides: /app working directory + bash execution       │
└──────────────────────────┬────────────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │  Task Tests   │
                   │  (Verifier)   │
                   └───────┬───────┘
                           │
                           ▼
                   Reward: 0.0 - 1.0
                   (logged to LangSmith)
```


## Customizing Your Agent

**System Prompt:** Edit [src/harbor_deepagents/agents/prompts.py](src/harbor_deepagents/agents/prompts.py)

**Model:** Edit `model_name` in config files (e.g., [configs/job.yaml](configs/job.yaml))
- OpenAI: `openai/gpt-5-mini`, `openai/gpt-4o`
- Anthropic: `anthropic/claude-sonnet-4-5-20250929`

## Creating Custom Tasks

```bash
# Copy template
cp -r tasks/web-scraper-task tasks/my-custom-task

# Edit instruction.md and tests/test_solution.py
# Update configs/job.yaml with task path

# Run
uv run harness
```

## Learn More
- **Harbor**: https://github.com/HarborBench/harbor - Agent benchmarking framework
- **DeepAgents**: https://github.com/langchain-ai/deepagents - LangChain agent harness
- **LangSmith**: https://docs.smith.langchain.com - LLM observability platform
- **Terminal Bench 2.0**: Standard benchmark suite for coding agents
