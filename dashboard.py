"""
UdaPlay Agent Dashboard — metrics and evaluation logs.
Run: streamlit run dashboard.py
Reads from logs/agent_runs.jsonl, logs/eval_cases.jsonl, logs/eval_summaries.jsonl, logs/memory_events.jsonl.
"""

import json
from pathlib import Path

import plotly.express as px
import streamlit as st

LOGS_DIR = Path(__file__).resolve().parent / "logs"
AGENT_RUNS_FILE = LOGS_DIR / "agent_runs.jsonl"
EVAL_CASES_FILE = LOGS_DIR / "eval_cases.jsonl"
EVAL_SUMMARIES_FILE = LOGS_DIR / "eval_summaries.jsonl"
MEMORY_EVENTS_FILE = LOGS_DIR / "memory_events.jsonl"


def load_jsonl(path: Path):
    """Yield one JSON object per line; return empty list if file missing."""
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def page_overview(agent_runs, eval_summaries, eval_cases):
    st.header("Overview")
    if not agent_runs and not eval_summaries:
        st.info(
            "**No data yet.** Run the Evaluation section in `Udaplay_02_starter_project.ipynb` "
            "(the benchmark loop with `dashboard_logs`). Optionally log interactive runs after `agent.invoke()` "
            "to see them here."
        )
        return

    n_runs = len(agent_runs)
    n_batches = len(eval_summaries)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total agent runs", n_runs)
    with col2:
        st.metric("Benchmark batches", n_batches)
    with col3:
        avg_tokens = (
            sum(r.get("total_tokens") or 0 for r in agent_runs) / n_runs
            if n_runs else 0
        )
        st.metric("Avg tokens per run", f"{avg_tokens:,.0f}")
    with col4:
        times = [r.get("execution_time_sec") for r in agent_runs if r.get("execution_time_sec") is not None]
        avg_time = sum(times) / len(times) if times else 0
        st.metric("Avg execution time", f"{avg_time:.1f}s")
    with col5:
        if eval_summaries:
            last = eval_summaries[-1]
            st.metric("Last batch mean score", f"{(last.get('mean_final_score') or 0):.2f}")
        else:
            st.metric("Last batch mean score", "—")

    if agent_runs:
        st.subheader("Charts")
        n_recent = min(50, len(agent_runs))
        recent = agent_runs[-n_recent:]
        chart_data = [
            {
                "index": i,
                "timestamp": (r.get("timestamp") or "")[:16].replace("T", " "),
                "tokens": r.get("total_tokens") or 0,
                "steps": r.get("steps_taken") or 0,
                "execution_time_sec": r.get("execution_time_sec") or 0,
                "source": r.get("source") or "",
            }
            for i, r in enumerate(recent)
        ]
        if chart_data:
            fig = px.line(
                chart_data,
                x="index",
                y="tokens",
                title="Tokens per run (last {} runs)".format(n_recent),
                labels={"index": "Run index", "tokens": "Total tokens"},
            )
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=220)
            st.plotly_chart(fig, use_container_width=True)
        steps_data = [r.get("steps_taken") or 0 for r in recent]
        if steps_data:
            fig2 = px.histogram(
                x=steps_data,
                nbins=min(max(max(steps_data) - min(steps_data), 1), 15),
                title="Distribution of steps taken",
                labels={"x": "Steps", "y": "Count"},
            )
            fig2.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=220)
            st.plotly_chart(fig2, use_container_width=True)


def page_agent_runs(agent_runs):
    st.header("Agent runs")
    if not agent_runs:
        st.info(
            "No agent runs in logs. Run the notebook benchmark (Evaluation section); "
            "each case is logged automatically. For ad-hoc runs, call `dashboard_logs.log_agent_run_from_run(...)` after `agent.invoke()`."
        )
        return

    source_filter = st.sidebar.selectbox(
        "Source",
        ["all", "interactive", "eval"],
        index=0,
    )
    filtered = agent_runs
    if source_filter != "all":
        filtered = [r for r in agent_runs if r.get("source") == source_filter]

    table_rows = []
    for r in filtered:
        query = (r.get("query") or "")[:80]
        if len(r.get("query") or "") > 80:
            query += "..."
        tool_calls = r.get("tool_calls") or []
        table_rows.append({
            "timestamp": (r.get("timestamp") or "")[:19].replace("T", " "),
            "run_id": (r.get("run_id") or "")[:8],
            "session_id": (r.get("session_id") or "")[:20],
            "query": query,
            "total_tokens": r.get("total_tokens") or 0,
            "execution_time_sec": round(r.get("execution_time_sec") or 0, 1),
            "steps_taken": r.get("steps_taken") or 0,
            "tools": ", ".join(tool_calls) if tool_calls else "—",
            "source": r.get("source") or "",
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.subheader("Details")
    for r in filtered:
        with st.expander(f"{r.get('timestamp', '')[:19]} · {r.get('run_id', '')[:8]}..."):
            st.write("**Query:**", (r.get("query") or "")[:300])
            st.write("**Session:**", r.get("session_id", ""))
            st.write("**Tokens:**", r.get("total_tokens"), "· **Steps:**", r.get("steps_taken"), "· **Time:**", f"{r.get('execution_time_sec') or 0:.1f}s")
            st.write("**Tools:**", r.get("tool_calls", []))


def page_evaluations(eval_summaries, eval_cases):
    st.header("Evaluations")
    if not eval_summaries:
        st.info(
            "No benchmark runs in logs. Run the **Evaluation** section in `Udaplay_02_starter_project.ipynb` "
            "(the cell that runs `for case in benchmark_cases:` and builds `summary_rows`). "
            "Logging is automatic and writes to `logs/eval_cases.jsonl` and `logs/eval_summaries.jsonl`."
        )
        return

    run_ids = [s.get("benchmark_run_id") for s in eval_summaries]
    selected_id = st.sidebar.selectbox(
        "Benchmark run",
        run_ids,
        format_func=lambda x: (x or "")[:8] + "..." if x else "",
    )
    if not selected_id:
        return

    summary = next((s for s in eval_summaries if s.get("benchmark_run_id") == selected_id), None)
    cases = [c for c in eval_cases if c.get("benchmark_run_id") == selected_id]

    if summary:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total cases", summary.get("total_cases", 0))
        with c2:
            st.metric("Mean final score", f"{(summary.get('mean_final_score') or 0):.2f}")
        with c3:
            st.metric("Mean trajectory score", f"{(summary.get('mean_trajectory_score') or 0):.2f}")
        with c4:
            st.metric("Task completed", f"{summary.get('task_completed_count', 0)} / {summary.get('total_cases', 0)}")

    if cases:
        st.subheader("Scores by case")
        case_ids = [c.get("case_id", "") for c in cases]
        final_scores = [c.get("final_score") or 0 for c in cases]
        traj_scores = [c.get("trajectory_score") or 0 for c in cases]
        fig = px.bar(
            x=case_ids,
            y=final_scores,
            title="Final score by case",
            labels={"x": "Case", "y": "Final score"},
            color=final_scores,
            color_continuous_scale="Blues",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=280, showlegend=False)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Per-case details")
    for row in cases:
        with st.expander(f"{row.get('case_id', '')} · score {row.get('final_score', 0):.2f}"):
            st.write("**Query:**", row.get("query", ""))
            st.write("**Tools used:**", row.get("tools_used", []))
            st.write("**Final score:**", row.get("final_score"), "· **Trajectory score:**", row.get("trajectory_score"))
            st.write("**Task completed:**", row.get("task_completed"), "· **Step tool correct:**", row.get("step_tool_correct"))
            st.write("**Execution time:**", row.get("execution_time"), "s · **Tokens:**", row.get("total_tokens"))
            st.write("**Feedback:**", row.get("feedback", ""))


def page_memory_metrics(memory_events):
    st.header("Memory Metrics")
    if not memory_events:
        st.info(
            "No memory events in logs yet. Rerun the notebook after the memory-aware logging changes so "
            "`logs/memory_events.jsonl` is populated."
        )
        return

    retrieve_events = [e for e in memory_events if e.get("event_type") == "retrieve"]
    store_events = [e for e in memory_events if e.get("event_type") == "store"]
    runs_with_retrieval = len({e.get("run_id") for e in retrieve_events if e.get("run_id")})
    runs_with_store = len({e.get("run_id") for e in store_events if e.get("run_id")})
    avg_retrievals = len(retrieve_events) / runs_with_retrieval if runs_with_retrieval else 0

    st.caption(
        "Proposed memory metrics: total LTM retrieval calls, runs with LTM retrieval, total saved fragments, "
        "runs with LTM saves, and average retrieval calls per memory-using run."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("LTM retrieval calls", len(retrieve_events))
    with c2:
        st.metric("Runs with retrieval", runs_with_retrieval)
    with c3:
        st.metric("Saved fragments", len(store_events))
    with c4:
        st.metric("Runs with saves", runs_with_store)
    with c5:
        st.metric("Avg retrievals / run", f"{avg_retrievals:.1f}")

    if retrieve_events:
        st.subheader("Retrieval activity by run")
        retrieval_by_run = {}
        for event in retrieve_events:
            run_id = event.get("run_id", "")
            if run_id not in retrieval_by_run:
                retrieval_by_run[run_id] = {
                    "run_id": run_id[:8],
                    "session_id": event.get("session_id", ""),
                    "source": event.get("source", ""),
                    "benchmark_run_id": (event.get("benchmark_run_id") or "")[:8],
                    "case_id": event.get("case_id", ""),
                    "retrieval_calls": 0,
                    "retrieved_fragments": 0,
                }
            retrieval_by_run[run_id]["retrieval_calls"] += 1
            retrieval_by_run[run_id]["retrieved_fragments"] += event.get("retrieved_fragment_count") or 0

        retrieval_rows = list(retrieval_by_run.values())
        retrieval_rows.sort(key=lambda row: row["retrieval_calls"], reverse=True)
        st.dataframe(retrieval_rows, use_container_width=True, hide_index=True)

        fig = px.bar(
            retrieval_rows,
            x="run_id",
            y="retrieval_calls",
            title="LTM retrieval calls per run",
            labels={"run_id": "Run", "retrieval_calls": "Retrieval calls"},
            color="source",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=280)
        st.plotly_chart(fig, use_container_width=True)

    if store_events:
        st.subheader("Saved long-term memory fragments")
        saved_rows = []
        for event in store_events:
            saved_rows.append({
                "timestamp": (event.get("timestamp") or "")[:19].replace("T", " "),
                "run_id": (event.get("run_id") or "")[:8],
                "session_id": event.get("session_id", ""),
                "source": event.get("source", ""),
                "case_id": event.get("case_id", ""),
                "namespace": event.get("namespace", "default"),
                "fragment_content": event.get("fragment_content", ""),
            })
        st.dataframe(saved_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No store_memory calls have been logged yet.")

    st.subheader("Memory event log")
    memory_rows = []
    for event in memory_events:
        memory_rows.append({
            "timestamp": (event.get("timestamp") or "")[:19].replace("T", " "),
            "event_type": event.get("event_type", ""),
            "run_id": (event.get("run_id") or "")[:8],
            "session_id": event.get("session_id", ""),
            "source": event.get("source", ""),
            "case_id": event.get("case_id", ""),
            "namespace": event.get("namespace", ""),
            "retrieved_fragment_count": event.get("retrieved_fragment_count"),
            "fragment_content": event.get("fragment_content", ""),
            "question": event.get("question", ""),
        })
    memory_rows.sort(key=lambda row: row["timestamp"], reverse=True)
    st.dataframe(memory_rows, use_container_width=True, hide_index=True)


def main():
    st.set_page_config(page_title="UdaPlay Dashboard", layout="wide")
    st.title("UdaPlay Agent Dashboard")

    agent_runs = load_jsonl(AGENT_RUNS_FILE)
    eval_cases = load_jsonl(EVAL_CASES_FILE)
    eval_summaries = load_jsonl(EVAL_SUMMARIES_FILE)
    memory_events = load_jsonl(MEMORY_EVENTS_FILE)

    page = st.sidebar.radio(
        "Page",
        ["Overview", "Agent runs", "Evaluations", "Memory Metrics"],
        index=0,
    )

    if page == "Overview":
        page_overview(agent_runs, eval_summaries, eval_cases)
    elif page == "Agent runs":
        page_agent_runs(agent_runs)
    elif page == "Evaluations":
        page_evaluations(eval_summaries, eval_cases)
    else:
        page_memory_metrics(memory_events)


if __name__ == "__main__":
    main()
