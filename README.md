# UdaPlay

UdaPlay is an agentic AI project for researching the video game industry. It combines a local ChromaDB-backed RAG pipeline, a stateful tool-using agent, long-term memory, benchmark-style evaluation, and a Streamlit dashboard for inspecting runs, evaluations, and memory usage.

## Features

- Local RAG over a curated video game dataset stored in ChromaDB
- Stateful agent workflow with retrieval, retrieval evaluation, and web-search fallback
- Long-term memory for user-specific preferences and durable facts
- Notebook-based demos and benchmark evaluations
- Streamlit dashboard for run metrics, evaluation metrics, and memory metrics
- Supporting project docs for RAG, memory, and agent evaluation

## Repository Contents

```text
.
├── games/                              # Source game JSON files used to build the vector store
├── chromadb/                           # Persistent ChromaDB files created after running Part 1
├── logs/                               # JSONL logs used by the dashboard
├── lib/                                # Core project abstractions and helpers
│   ├── agents.py                       # Agent loop and session handling
│   ├── evaluation.py                   # Evaluation models and evaluator logic
│   ├── memory.py                       # Long-term memory abstractions
│   ├── state_machine.py                # State machine runtime
│   ├── vector_db.py                    # ChromaDB management helpers
│   └── dashboard_logs.py               # Logging helpers for dashboard data
├── docs/
│   ├── chromadb_rag_explanation.md     # RAG concepts and project mapping
│   ├── long_term_memory.md             # Memory concepts and project mapping
│   ├── agent_evaluation.md             # Evaluation concepts and implementation plan
│   └── PROJECTT_RUBRIC.md              # Project rubric reference
├── Udaplay_01_solution_project.ipynb   # Part 1: build and query the local vector store
├── Udaplay_02_solution_project.ipynb   # Part 2: run the agent, evaluation, and logging
├── dashboard.py                        # Streamlit dashboard entrypoint
├── PROJECT_REQUIREMENTS.MD             # Original project requirements README
├── requirements.txt                    # pip-friendly dependency list
└── pyproject.toml                      # uv / project metadata and dependencies
```

## Requirements

- Python 3.12+
- OpenAI API key
- Tavily API key

## Environment Variables

Create a `.env` file in the project root with:

```env
OPENAI_API_KEY=your_openai_key
CHROMA_OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

`OPENAI_API_KEY` is used by the agent and evaluation workflows. `CHROMA_OPENAI_API_KEY` is used for Chroma embeddings. In many setups these can be the same key.

## Installation

### Option 1: `uv` (recommended)

```bash
uv sync
```

### Option 2: `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How To Run

### 1. Build the local vector store

Open and run [`Udaplay_01_solution_project.ipynb`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/Udaplay_01_solution_project.ipynb).

This notebook:
- loads the local game JSON files from `games/`
- formats and embeds the records
- stores them in the persistent `chromadb/` directory
- demonstrates semantic retrieval over the local dataset

### 2. Run the agent

Open and run [`Udaplay_02_solution_project.ipynb`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/Udaplay_02_solution_project.ipynb).

This notebook:
- connects to the persistent ChromaDB store from Part 1
- defines the agent tools
- runs example interactive queries
- logs interactive and evaluation runs
- benchmarks the agent on a fixed evaluation set

### 3. Launch the dashboard

If you are using `uv`, run:

```bash
uv run streamlit run dashboard.py
```

If you are using an activated virtual environment, run:

```bash
streamlit run dashboard.py
```

The dashboard reads data from `logs/` and includes:
- agent run metrics
- evaluation summaries and case-level results
- memory metrics showing saved fragments and retrieval usage

## Typical Workflow

1. Set your environment variables in `.env`.
2. Run `Udaplay_01_solution_project.ipynb` to build the vector store.
3. Run `Udaplay_02_solution_project.ipynb` to exercise the agent and generate logs.
4. Start the Streamlit dashboard to inspect the results.

## Dependencies

Main project dependencies are defined in [`pyproject.toml`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/pyproject.toml) and mirrored in [`requirements.txt`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/requirements.txt).

Core packages:
- `chromadb`
- `openai`
- `tavily-python`
- `python-dotenv`
- `pydantic`
- `streamlit`
- `plotly`
- `pdfplumber`

## Outputs and Artifacts

- `chromadb/`: persistent vector store files created after Part 1
- `logs/agent_runs.jsonl`: interactive and evaluation run logs
- `logs/eval_cases.jsonl`: case-level evaluation logs
- `logs/eval_summaries.jsonl`: batch evaluation summaries
- `logs/memory_events.jsonl`: long-term memory retrieval/store events

## Documentation

Additional project docs live in [`docs/`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/docs):

- [`docs/chromadb_rag_explanation.md`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/docs/chromadb_rag_explanation.md)
- [`docs/long_term_memory.md`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/docs/long_term_memory.md)
- [`docs/agent_evaluation.md`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/docs/agent_evaluation.md)
- [`docs/PROJECTT_RUBRIC.md`](/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/docs/PROJECTT_RUBRIC.md)

## Troubleshooting

- If `streamlit run dashboard.py` cannot find `plotly`, use `uv run streamlit run dashboard.py` so Streamlit runs inside the same environment where dependencies were installed.
- If retrieval returns poor results, rerun Part 1 to rebuild the ChromaDB store before rerunning Part 2.
- If the dashboard is empty, rerun the notebook demo and evaluation cells so new JSONL logs are written to `logs/`.

## License

This project is for educational use as part of the UdaPlay / Agentic AI coursework.
