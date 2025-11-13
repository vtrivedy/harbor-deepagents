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

# Rebuild the harness wheel after making code changes
##IMPORTANT: run again if the tbench run errors, working on a cleaner fix for custom harnesses
uv sync --no-editable
```

### 2. Example Configuration

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

Make sure `harbor` is on your `PATH` (e.g., via `uv tool install harbor`) before running these commands.

```bash
# Run the web-scraper demo task with OpenAI
uv run harness --model openai/gpt-5-mini

# (Optional) Same command but read MODEL_NAME + API keys from .env
uv run harness

# Results are saved to jobs/
ls jobs/deepagents-web-scraper/

# View the reward score
cat jobs/deepagents-web-scraper/result.json | jq '.reward_stats.mean'
```

### 4. Run Terminal Bench 2.0 (single task or full suite)

```bash
# Run a single task locally in Docker
uv run tb-docker --task prove-plus-comm --model openai/gpt-5-mini

# Run on cloud sandboxes (Daytona or Modal)
# NOTE: Sandbox environments may have issues with downloading uv, python, container definition
uv run tb-daytona --task prove-plus-comm --model anthropic/claude-sonnet-4-5-20250620
# Or use Modal instead
harbor run --config configs/terminal-bench-modal.yaml -d terminal-bench@2.0 --task-name prove-plus-comm

# Omit --task to process the full benchmark dataset
uv run tb-docker --model openai/gpt-5-mini
```

Each run auto-generates a Harbor `--job-name` in the format `<config>-<task>-<model>-<timestamp>`, so every invocation gets its own folder under `jobs/`. Pass `--job-name my-run` if you want to set it manually.

Prefer using `uv run` for convenience, but the raw Harbor command from the docs also works (example for Terminal Bench):

```bash
harbor run -d "terminal-bench@2.0" \
  -m "openai/gpt-5-mini" \
  -a "harbor_deepagents.agents.deepagent_harbor:DeepAgentHarbor" \
  -e daytona \  # or: modal, docker, e2b
  -n 1 \
  --task-name prove-plus-comm
```


### 5. View Traces in LangSmith

If you enabled LangSmith tracing:
1. Visit https://smith.langchain.com
2. Navigate to your project (e.g., "harbor-tracing")
3. See full execution traces with tool calls, LLM responses, and costs
4. Harbor reward scores are automatically logged as feedback

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

### Modify the System Prompt

Edit [src/harbor_deepagents/agents/prompts.py](src/harbor_deepagents/agents/prompts.py):

```python
HARBOR_SYSTEM_PROMPT = """You are an expert software engineer...
# Add your custom instructions here
"""
```

### Change the Model

Edit [configs/job.yaml](configs/job.yaml):

```yaml
agents:
  - import_path: harbor_deepagents.agents.deepagent_harbor:DeepAgentHarbor
    model_name: openai/gpt-5-mini      # Try: gpt-4o, claude-sonnet-4-5
    kwargs:
      max_iterations: 50
      temperature: 0.0
```

## Creating Custom Tasks

1. **Copy the template:**
   ```bash
   cp -r tasks/web-scraper-task tasks/my-custom-task
   ```

2. **Define your task** in `instruction.md`:
   ```markdown
   Create a Python script that does X, Y, Z...
   ```

3. **Set up verification** in `tests/test_solution.py`:
   ```python
   def test_solution():
       # Your test logic
       assert output == expected
   ```

4. **Update config** in `configs/job.yaml`:
   ```yaml
   tasks:
     - path: tasks/my-custom-task
   ```

5. **Run it:**
   ```bash
   harbor run --config configs/job.yaml
   ```

### How LangSmith Tracing Works

Simply enable tracing in your `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
```

Every LLM call, tool use, and agent step is automatically logged. No code changes needed.


## Learn More
- **Harbor**: https://github.com/HarborBench/harbor - Agent benchmarking framework
- **DeepAgents**: https://github.com/langchain-ai/deepagents - LangChain agent harness
- **LangSmith**: https://docs.smith.langchain.com - LLM observability platform
- **Terminal Bench 2.0**: Standard benchmark suite for coding agents
