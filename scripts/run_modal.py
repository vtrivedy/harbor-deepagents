"""Run Harbor job on Modal cloud infrastructure with DeepAgents."""

import asyncio
from pathlib import Path

import modal

# Create Modal app
app = modal.App("harbor-deepagents")

# Define Modal image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        # Harbor
        "harbor>=0.1.7",
        # LangChain 1.0 + DeepAgents
        "langchain>=1.0.0",
        "langchain-anthropic>=1.0.0",
        "deepagents>=0.1.0",
        # LangSmith
        "langsmith>=0.2.0",
        # Utilities
        "python-dotenv>=1.1.1",
        "pyyaml>=6.0.2",
    )
    .apt_install("docker.io", "git")
)

# Mount local code and tasks
code_mount = modal.Mount.from_local_dir(
    "src/harbor_deepagents",
    remote_path="/root/harbor_deepagents",
)

tasks_mount = modal.Mount.from_local_dir(
    "tasks",
    remote_path="/root/tasks",
)

configs_mount = modal.Mount.from_local_file(
    "configs/job.yaml",
    remote_path="/root/configs/job.yaml",
)


@app.function(
    image=image,
    mounts=[code_mount, tasks_mount, configs_mount],
    secrets=[
        modal.Secret.from_name("anthropic-api-key"),
        modal.Secret.from_name("langsmith-api-key"),
    ],
    timeout=3600,  # 1 hour
    cpu=4,
    memory=8192,
)
def run_harbor_job():
    """Execute Harbor job with DeepAgents on Modal."""
    import sys

    # Add local code to path
    sys.path.insert(0, "/root")

    # Import after path is set
    from harbor.job import Job
    from harbor.models.job.config import JobConfig

    # Load job config
    config_path = Path("/root/configs/job.yaml")
    config = JobConfig.model_validate_yaml(config_path.read_text())

    # Override paths for Modal environment
    config.jobs_dir = Path("/root/jobs")

    # Update task paths to Modal paths
    for task_config in config.tasks:
        if hasattr(task_config, "path"):
            task_config.path = Path(f"/root/{task_config.path}")

    # Run job
    print("=" * 80)
    print("Starting Harbor Job on Modal with DeepAgents")
    print("=" * 80)
    print(f"Tasks: {len(config.tasks)}")
    print(f"Agents: {len(config.agents)}")
    print(f"Attempts: {config.n_attempts}")
    print("=" * 80)
    print("")

    job = Job(config)
    result = asyncio.run(job.run())

    print("")
    print("=" * 80)
    print("JOB COMPLETE")
    print("=" * 80)
    print(f"Total trials: {result.n_total_trials}")

    # Print stats
    for evals_key, dataset_stats in result.stats.evals.items():
        print(f"\n{evals_key}:")
        print(f"  Trials: {dataset_stats.n_trials}")
        print(f"  Errors: {dataset_stats.n_errors}")
        if dataset_stats.metrics:
            for metric in dataset_stats.metrics:
                for key, value in metric.items():
                    print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")

    return {
        "n_trials": result.n_total_trials,
        "stats": result.stats.model_dump(),
    }


@app.local_entrypoint()
def main():
    """Local entrypoint for Modal deployment."""
    print("Deploying Harbor + DeepAgents job to Modal...")
    print("")

    result = run_harbor_job.remote()

    print("")
    print("=" * 80)
    print("Modal Deployment Complete!")
    print("=" * 80)
    print("")
    print(f"Results: {result}")
    print("")
    print("View logs and results in Modal dashboard:")
    print("  → https://modal.com")


if __name__ == "__main__":
    app()
