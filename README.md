# Building DeepAgent Harnesses for Terminal Bench 2.0 with Harbor

Build, evaluate, and improve custom agents on standardized benchmarks like Terminal Bench 2.0 using **DeepAgents** (LangChain's agent framework), **Harbor** (a framework for running agents in container environments), and **LangSmith** (built in logging and observability).

## What is This?

This repo provides a **DeepAgent harness** - a complete agent implementation built on [LangChain DeepAgents](https://github.com/langchain-ai/deepagents) that can:

- ✅ **Run Harbor tasks** - Execute any Harbor benchmark in sandboxed environments
- ✅ **Customize your agent** - Modify prompts, tools, and behavior for your use case
- ✅ **Log to LangSmith** - Automatically trace all runs with full observability
- ✅ **Measure & improve** - Analyze traces to optimize your agent harness design

**DeepAgents** is LangChain's official agent framework (built on LangChain 1.0) that provides:

- **Planning** - `write_todos` tool for task decomposition
- **Real Filesystem** - `ls`, `read_file`, `write_file`, `edit_file`, `glob_search`, `grep_search` via FilesystemBackend
- **Subagent Spawning** - `task` tool for delegating to specialized agents
- **Production-Ready** - Powers Claude Code and other LangChain apps

## Supported Sandbox Providers

Run your agent in multiple execution environments:

- 🐳 **Docker** (local)
- ☁️ **Modal, Daytona, E2B** - Cloud sandboxes

## Quick Start

### 1. Installation

```bash
# Clone or download this repo
git clone https://github.com/vtrivedy/harbor-deepagents
cd harbor-deepagents

# Create virtual environment
python3.12 -m venv .venv-standard
source .venv-standard/bin/activate

# Install the deepagents harness
pip install -e .

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

# Optional(recommended): Daytona (for cloud sandboxes)
DAYTONA_API_KEY=dtn_...
```

### 3. Run Your First Task

```bash
# Run the web-scraper demo task
harbor run --config configs/job.yaml

# Results are saved to jobs/
ls jobs/deepagents-web-scraper/

# View the reward score
cat jobs/deepagents-web-scraper/result.json | jq '.reward_stats.mean'
```


### 4. View Traces in LangSmith

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

## Project Structure

```
harbor-deepagents/
├── src/harbor_deepagents/
│   └── agents/
│       ├── deepagent_harbor.py       # Main harness implementation
│       ├── harbor_tools.py           # Custom bash tool
│       ├── prompts.py                # System prompt
│       └── langsmith_integration.py  # Feedback API
│
├── tasks/
│   └── web-scraper-task/            # Example Harbor task
│       ├── task.toml                # Task config
│       ├── instruction.md           # Agent instructions
│       ├── environment/             # Sandbox setup
│       └── tests/                   # Verification tests
│
├── configs/
│   └── job.yaml                     # Harbor job configuration
│
├── .env                             # API keys (create this)
├── pyproject.toml                   # Package dependencies
└── README.md                        # You are here
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

### Use Different Sandbox Providers

**Docker (local):**
```yaml
environment:
  type: docker
```

**Modal (serverless cloud):**
```yaml
environment:
  type: modal
  # Requires: modal setup
```

**Daytona (cloud dev environments):**
```yaml
environment:
  type: daytona
  # Requires: DAYTONA_API_KEY in .env
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


## Use Cases

### 1. Harness Development & Iteration

Test and improve your agent harness:

```bash
# Run a task
harbor run --config configs/job.yaml

# Analyze traces in LangSmith
# - Where did the agent struggle?
# - Which tools were used inefficiently?
# - What prompt improvements could help?

# Update prompts in src/harbor_deepagents/agents/prompts.py
# Re-run and compare performance
```

### 2. Model Comparison

Evaluate different models on the same tasks:

```yaml
agents:
  - import_path: harbor_deepagents.agents.deepagent_harbor:DeepAgentHarbor
    model_name: openai/gpt-5-mini
  - import_path: harbor_deepagents.agents.deepagent_harbor:DeepAgentHarbor
    model_name: anthropic/claude-sonnet-4-5-20250929
```

Compare costs, success rates, and step counts in LangSmith.

### 3. Benchmark Evaluation

Run on Terminal Bench 2.0 or custom benchmarks:

```bash
harbor run \
  --dataset terminal-bench@2.0 \
  --config configs/job.yaml \
  --n-concurrent 4
```

Track aggregate metrics:
- Mean reward across all tasks
- Cost per task
- Success rate by task category

## Technical Details

### Why DeepAgents?

We built this harness on **LangChain DeepAgents** instead of from scratch because:

1. **Start Quickly** - DeepAgents have batteries included defaults
2. **Built-in Planning** - `write_todos` tool for task decomposition
3. **Real Filesystem** - FilesystemBackend for file system ops
4. **Subagent Support** - `task` tool for spawning specialized agents
5. **LangChain 1.0** - Latest framework with lots of built-in tooling

### How LangSmith Tracing Works

Simply enable tracing in your `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...
```

Every LLM call, tool use, and agent step is automatically logged. No code changes needed.

**Bonus:** Harbor reward scores are pushed to LangSmith as feedback via the `send_harbor_feedback()` function in [langsmith_integration.py](src/harbor_deepagents/agents/langsmith_integration.py).

### Tool Architecture

The harness provides **one custom tool** to DeepAgents:

```python
@tool
def bash(command: str) -> str:
    """Execute bash commands in Harbor's sandboxed environment."""
    result = await environment.exec(command)
    return result.stdout
```

This `bash` tool works across **all sandbox providers** (Docker, Modal, Daytona, E2B, Runloop) thanks to Harbor's unified environment abstraction.

DeepAgents provides the rest:
- File operations: `ls`, `read_file`, `write_file`, `edit_file`, `glob_search`, `grep_search`
- Planning: `write_todos`
- Orchestration: `task` (for subagents)

## Learn More

- **Harbor**: https://github.com/HarborBench/harbor - Agent benchmarking framework
- **DeepAgents**: https://github.com/langchain-ai/deepagents - LangChain agent harness
- **LangSmith**: https://docs.smith.langchain.com - LLM observability platform
- **Terminal Bench 2.0**: Standard benchmark suite for coding agents
