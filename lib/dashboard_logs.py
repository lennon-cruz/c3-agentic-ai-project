"""
Dashboard logging: schema, serialize, and append agent runs and eval data to JSONL.
Single source of truth for log format; used by the notebook; dashboard reads the files.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# Optional imports for extracting from Run/messages; only needed when logging from run object
try:
    from lib.state_machine import Run
    from lib.messages import AIMessage
except ImportError:
    Run = None  # type: ignore
    AIMessage = None  # type: ignore

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
AGENT_RUNS_FILE = LOGS_DIR / "agent_runs.jsonl"
EVAL_CASES_FILE = LOGS_DIR / "eval_cases.jsonl"
EVAL_SUMMARIES_FILE = LOGS_DIR / "eval_summaries.jsonl"

# Max query length to store
QUERY_TRUNCATE_LEN = 200


def _ensure_logs_dir() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    _ensure_logs_dir()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _steps_taken_from_run(run: "Run") -> int:
    if run is None or not run.snapshots:
        return 0
    return len(
        [
            s
            for s in run.snapshots
            if s.step_id not in ("__entry__", "__termination__")
        ]
    )


def _tool_calls_from_messages(messages: List[Any]) -> List[str]:
    if not messages or AIMessage is None:
        return []
    names = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if hasattr(tc, "function") and getattr(tc.function, "name", None):
                    names.append(tc.function.name)
    return names


def _run_execution_time_sec(run: "Run") -> Optional[float]:
    if run is None or not run.end_timestamp or not run.start_timestamp:
        return None
    return (run.end_timestamp - run.start_timestamp).total_seconds()


def log_agent_run(
    run_id: str,
    timestamp: str,
    source: str,
    *,
    session_id: Optional[str] = None,
    query: Optional[str] = None,
    total_tokens: Optional[int] = None,
    execution_time_sec: Optional[float] = None,
    steps_taken: Optional[int] = None,
    tool_calls: Optional[List[str]] = None,
    benchmark_run_id: Optional[str] = None,
    case_id: Optional[str] = None,
    prompt_version: Optional[str] = None,
) -> None:
    """
    Append one agent run record to logs/agent_runs.jsonl.
    Required: run_id, timestamp, source. Others optional.
    """
    record: Dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "source": source,
    }
    if session_id is not None:
        record["session_id"] = session_id
    if query is not None:
        record["query"] = query[:QUERY_TRUNCATE_LEN] if len(query) > QUERY_TRUNCATE_LEN else query
    if total_tokens is not None:
        record["total_tokens"] = total_tokens
    if execution_time_sec is not None:
        record["execution_time_sec"] = round(execution_time_sec, 3)
    if steps_taken is not None:
        record["steps_taken"] = steps_taken
    if tool_calls is not None:
        record["tool_calls"] = tool_calls
    if benchmark_run_id is not None:
        record["benchmark_run_id"] = benchmark_run_id
    if case_id is not None:
        record["case_id"] = case_id
    if prompt_version is not None:
        record["prompt_version"] = prompt_version
    _append_jsonl(AGENT_RUNS_FILE, record)


def log_agent_run_from_run(
    run: "Run",
    session_id: str,
    query: str,
    execution_time_sec: float,
    source: str = "interactive",
    benchmark_run_id: Optional[str] = None,
    case_id: Optional[str] = None,
    prompt_version: Optional[str] = None,
) -> None:
    """
    Extract metrics from a Run and append one row to agent_runs.jsonl.
    Use from the notebook after agent.invoke() or inside the benchmark loop.
    """
    if Run is None:
        raise RuntimeError("lib.state_machine.Run not available")
    final_state = run.get_final_state() or {}
    messages = final_state.get("messages", [])
    total_tokens = final_state.get("total_tokens", 0)
    steps_taken = _steps_taken_from_run(run)
    tool_calls = _tool_calls_from_messages(messages)
    ts = datetime.utcnow().isoformat() + "Z"
    log_agent_run(
        run_id=run.run_id,
        timestamp=ts,
        source=source,
        session_id=session_id,
        query=query,
        total_tokens=total_tokens,
        execution_time_sec=execution_time_sec,
        steps_taken=steps_taken,
        tool_calls=tool_calls,
        benchmark_run_id=benchmark_run_id,
        case_id=case_id,
        prompt_version=prompt_version,
    )


def log_eval_case(
    benchmark_run_id: str,
    case_id: str,
    run_id: str,
    timestamp: str,
    source: str,
    *,
    query: str = "",
    tools_used: Optional[List[str]] = None,
    final_score: Optional[float] = None,
    trajectory_score: Optional[float] = None,
    step_tool_correct: Optional[bool] = None,
    task_completed: Optional[bool] = None,
    execution_time: Optional[float] = None,
    total_tokens: Optional[int] = None,
    feedback: Optional[str] = None,
    prompt_version: Optional[str] = None,
) -> None:
    """
    Append one benchmark case to logs/eval_cases.jsonl (flat row).
    Required: benchmark_run_id, case_id, run_id, timestamp, source.
    """
    record: Dict[str, Any] = {
        "benchmark_run_id": benchmark_run_id,
        "case_id": case_id,
        "run_id": run_id,
        "timestamp": timestamp,
        "source": source,
    }
    if query is not None:
        record["query"] = query
    if tools_used is not None:
        record["tools_used"] = tools_used
    if final_score is not None:
        record["final_score"] = round(final_score, 4)
    if trajectory_score is not None:
        record["trajectory_score"] = round(trajectory_score, 4)
    if step_tool_correct is not None:
        record["step_tool_correct"] = step_tool_correct
    if task_completed is not None:
        record["task_completed"] = task_completed
    if execution_time is not None:
        record["execution_time"] = round(execution_time, 3)
    if total_tokens is not None:
        record["total_tokens"] = total_tokens
    if feedback is not None:
        record["feedback"] = feedback
    if prompt_version is not None:
        record["prompt_version"] = prompt_version
    _append_jsonl(EVAL_CASES_FILE, record)


def log_eval_summary(
    benchmark_run_id: str,
    timestamp: str,
    total_cases: int,
    *,
    mean_final_score: Optional[float] = None,
    mean_trajectory_score: Optional[float] = None,
    task_completed_count: Optional[int] = None,
    total_tokens: Optional[int] = None,
    prompt_version: Optional[str] = None,
) -> None:
    """
    Append one benchmark batch summary to logs/eval_summaries.jsonl.
    """
    record: Dict[str, Any] = {
        "benchmark_run_id": benchmark_run_id,
        "timestamp": timestamp,
        "total_cases": total_cases,
    }
    if mean_final_score is not None:
        record["mean_final_score"] = round(mean_final_score, 4)
    if mean_trajectory_score is not None:
        record["mean_trajectory_score"] = round(mean_trajectory_score, 4)
    if task_completed_count is not None:
        record["task_completed_count"] = task_completed_count
    if total_tokens is not None:
        record["total_tokens"] = total_tokens
    if prompt_version is not None:
        record["prompt_version"] = prompt_version
    _append_jsonl(EVAL_SUMMARIES_FILE, record)


def create_benchmark_run_id() -> str:
    """Generate a unique id for a benchmark run (e.g. UUID)."""
    return str(uuid.uuid4())
