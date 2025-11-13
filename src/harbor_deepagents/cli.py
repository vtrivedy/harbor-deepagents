"""
Command-line entry point for running Harbor + DeepAgents harness workflows via uv.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from langsmith import Client
from rich.console import Console

from harbor_deepagents.agents.langsmith_integration import send_harbor_feedback

console = Console()

DEFAULT_JOB_CONFIG = Path("configs/job.yaml")
TERMINAL_BENCH_CONFIGS: Dict[str, Path] = {
    "docker": Path("configs/terminal-bench-docker.yaml"),
    "daytona": Path("configs/terminal-bench-daytona.yaml"),
}
TERMINAL_BENCH_DATASET = "terminal-bench@2.0"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Harbor DeepAgents harness with simple uv-friendly commands.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--suite",
        choices=["job", "terminal-bench"],
        default="job",
        help="Which pre-defined job config to use when --config is not provided.",
    )
    parser.add_argument(
        "--env-type",
        choices=["docker", "daytona"],
        default="docker",
        help="Execution environment preset (used for Terminal Bench configs).",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help="Explicit Harbor YAML config to run (overrides --suite/--env-type).",
    )
    parser.add_argument(
        "--dataset",
        help="Optional Harbor dataset (e.g., terminal-bench@2.0).",
    )
    parser.add_argument(
        "--task",
        dest="task_name",
        help="Optional single task name to run (maps to --task-name).",
    )
    parser.add_argument(
        "--model",
        help="Model identifier (fallback to MODEL_NAME env var).",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Dotenv file to load provider keys + MODEL_NAME from.",
    )
    parser.add_argument(
        "--no-env-file",
        action="store_true",
        help="Disable automatic dotenv loading.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Harbor command without executing it.",
    )
    parser.add_argument(
        "--job-name",
        help="Optional job name override. Defaults to <config>-<task>-<timestamp>.",
    )
    parser.add_argument(
        "harbor_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments after '--' are passed directly to Harbor.",
    )
    return parser.parse_args(argv)


def load_environment(env_file: Optional[str], skip: bool) -> None:
    if skip or not env_file:
        return
    env_path = Path(env_file)
    if not env_path.exists():
        console.print(f"[yellow]No dotenv file found at {env_path}. Continuing without it.[/]")
        return

    load_dotenv(env_path, override=False)
    console.print(f"[green]Loaded environment variables from {env_path}[/]")


def resolve_config(suite: str, env_type: str, explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit)
    if suite == "terminal-bench":
        config_path = TERMINAL_BENCH_CONFIGS.get(env_type)
        if not config_path:
            raise ValueError(f"Unsupported env_type '{env_type}' for Terminal Bench runs.")
        return config_path
    return DEFAULT_JOB_CONFIG


def determine_model(cli_model: Optional[str]) -> str:
    model = cli_model or os.environ.get("MODEL_NAME")
    if not model:
        console.print(
            "[red]MODEL_NAME is not set. Pass --model or export MODEL_NAME in your environment.[/]"
        )
        sys.exit(1)
    return model


def infer_provider(model: str) -> Optional[str]:
    lowered = model.lower()
    if lowered.startswith(("openai/", "gpt-")):
        return "openai"
    if lowered.startswith(("anthropic/", "claude-")):
        return "anthropic"
    return None


def ensure_provider_keys(model: str) -> None:
    provider = infer_provider(model)
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        console.print("[red]OPENAI_API_KEY is required for OpenAI models.[/]")
        sys.exit(1)
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY is required for Anthropic models.[/]")
        sys.exit(1)


def ensure_env_requirements(env_type: str) -> None:
    if env_type == "daytona" and not os.environ.get("DAYTONA_API_KEY"):
        console.print("[red]DAYTONA_API_KEY is required when env-type is 'daytona'.[/]")
        sys.exit(1)


def build_command(config_path: Path, dataset: Optional[str], task_name: Optional[str]) -> List[str]:
    command: List[str] = ["harbor", "run", "--config", str(config_path)]
    if dataset:
        command.extend(["-d", dataset])
    if task_name:
        command.extend(["--task-name", task_name])
    return command


def normalize_remainder(args: Iterable[str]) -> List[str]:
    remainder = list(args)
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return remainder


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    load_environment(args.env_file, args.no_env_file)

    config_path = resolve_config(args.suite, args.env_type, args.config_path)
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config_path}[/]")
        sys.exit(1)

    dataset = args.dataset or (
        TERMINAL_BENCH_DATASET if args.suite == "terminal-bench" else None
    )

    model = determine_model(args.model)
    os.environ["MODEL_NAME"] = model

    ensure_provider_keys(model)
    ensure_env_requirements(args.env_type)

    extra_args = normalize_remainder(args.harbor_args)
    command = build_command(config_path, dataset, args.task_name)
    if args.job_name:
        command.extend(["--job-name", args.job_name])
    elif "--job-name" not in extra_args:
        auto_name = generate_job_name(config_path, args.task_name, model)
        command.extend(["--job-name", auto_name])
    if extra_args:
        command.extend(extra_args)

    console.print(f"[cyan]Running Harbor job {command[command.index('--job-name') + 1]}[/]")

    if args.dry_run:
        console.print("[yellow]Dry run enabled; skipping execution.[/]")
        return

    try:
        subprocess.run(command, check=True)
        maybe_send_feedback_from_latest_trial()
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Harbor exited with code {exc.returncode}[/]")
        sys.exit(exc.returncode)


def _run_with_preset(preset_args: List[str]) -> None:
    extra_args = sys.argv[1:]
    main(preset_args + list(extra_args))


def run_tb_docker() -> None:
    preset = ["--suite", "terminal-bench", "--env-type", "docker"]
    _run_with_preset(preset)


def run_tb_daytona() -> None:
    preset = ["--suite", "terminal-bench", "--env-type", "daytona"]
    _run_with_preset(preset)


def generate_job_name(config_path: Path, task_name: Optional[str], model: str) -> str:
    """Create a readable job name like tb-daytona-prove-plus-comm-20251112-0730."""

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    base = config_path.stem
    task_segment = task_name or "all-tasks"
    model_segment = model.split("/")[-1]
    slug = "-".join(
        _slugify(segment)
        for segment in (base, task_segment, model_segment, timestamp)
        if segment
    )
    return slug or f"harbor-job-{timestamp}"


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def maybe_send_feedback_from_latest_trial() -> None:
    """Best-effort LangSmith feedback push using the most recent job artifacts."""

    jobs_dir = Path("jobs")
    if not jobs_dir.exists():
        return

    trajectory_files = sorted(
        jobs_dir.glob("*/**/agent/trajectory.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not trajectory_files:
        return

    trajectory_path = trajectory_files[0]
    trial_dir = trajectory_path.parent.parent
    result_path = trial_dir / "result.json"

    if not result_path.exists():
        return

    try:
        trajectory = json.loads(trajectory_path.read_text())
        trial_result = json.loads(result_path.read_text())
    except Exception:
        return

    run_id = trajectory.get("session_id")
    reward = (
        trial_result.get("verifier_result", {})
        .get("rewards", {})
        .get("reward")
    )
    if not run_id or reward is None:
        return
    run_id = resolve_langsmith_run_id(run_id)

    task_name = trial_result.get("task_name") or trial_dir.name
    cost_usd = trial_result.get("agent_result", {}).get("cost_usd")
    total_steps = len(trajectory.get("steps", []))

    try:
        send_harbor_feedback(
            run_id=run_id,
            task_name=task_name,
            reward=reward,
            agent_cost_usd=cost_usd,
            total_steps=total_steps,
        )
        console.print("[green]✓ Sent LangSmith feedback[/]")
    except Exception as exc:
        console.print(f"[yellow]Warning: failed to send LangSmith feedback: {exc}[/]")


def resolve_langsmith_run_id(session_id: str) -> str:
    """Map our session_id to the actual LangSmith run ID, if available."""

    if not os.getenv("LANGCHAIN_TRACING_V2"):
        return session_id

    project_name = os.getenv("LANGCHAIN_PROJECT")
    try:
        client = Client()
        runs = client.list_runs(
            project_name=project_name,
            execution_order="desc",
            filter={"metadata.session_id": {"$eq": session_id}},
        )
        first = next(iter(runs), None)
        if first:
            return str(first.id)
    except Exception as exc:
        console.print(f"[yellow]Warning: unable to resolve LangSmith run id: {exc}[/]")
    return session_id


if __name__ == "__main__":
    main()
