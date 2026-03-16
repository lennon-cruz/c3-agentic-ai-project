# Agent Evaluation for AI Agents

This document explains the concepts behind **agent evaluation** and shows how they connect to the abstractions already present in this project.

When you build an agent, getting it to produce an answer is only the beginning. You also need a way to answer questions like:

- Did the agent actually solve the task?
- Did it use the right tool?
- Did it take too many steps?
- Did it waste tokens or time?
- Would the same agent still perform well after a future code or prompt change?

Agent evaluation gives you a repeatable way to measure those things. It is the feedback loop that helps you improve quality, catch regressions, and build confidence in your system.

---

## 1. Why Agent Evaluation Matters

A normal software test often checks a fixed input against a fixed output. Agents are more complicated:

- They may call tools.
- They may use memory.
- They may follow different paths to reach the same result.
- They may succeed sometimes and fail other times on similar tasks.

Because of that, agent quality is not just about whether the final answer "looks okay." We want to understand:

- **Reliability**: does the agent complete tasks consistently?
- **Safety**: does it avoid harmful or incorrect actions?
- **Efficiency**: does it use a reasonable number of steps, tokens, and tool calls?
- **Debuggability**: if it fails, can we see why?

For example, imagine a game research agent is asked:

> "Was Mortal Kombat X released for PlayStation 5?"

A poor agent might:

- use the wrong tool,
- search irrelevant documents,
- produce an overconfident but incorrect answer,
- or take many unnecessary steps before responding.

Without evaluation, those problems can hide inside a result that sounds fluent. With evaluation, you can measure the failure, compare versions, and improve the system deliberately.

---

## 2. Mental Model: What We Are Evaluating

An agent run usually has several parts:

1. A **user query**
2. A set of **instructions**
3. Optional **memory or retrieved context**
4. One or more **LLM decisions**
5. Optional **tool calls**
6. A **final response**

That means we can evaluate the agent at more than one level.

### Final outcome

This asks: **did the user get a good answer?**

Example:

- User asks for the first 3D Mario platformer.
- The agent answers "Super Mario 64."
- We evaluate whether that answer is correct, useful, and well-formatted.

This is the simplest view because it treats the agent like a black box.

### Individual decisions

This asks: **did the agent make the right local choice at a specific step?**

Example:

- The user asks about a game in the local dataset.
- The agent should use the retrieval tool, not a web search tool.
- We evaluate whether it picked the right tool and passed valid arguments.

This is useful for debugging.

### Full trajectory

This asks: **how did the agent get to the answer?**

Example:

- Did it retrieve local information first?
- Did it call a web tool only when needed?
- Did it loop too many times?
- Did it produce a final answer after tool use?

Trajectory evaluation is the richest view because it measures the full run instead of just the end.

So the basic mental model is:

- **Final response evaluation** tells you whether the outcome is good.
- **Single-step evaluation** tells you whether a decision was good.
- **Trajectory evaluation** tells you whether the whole workflow was good.

You usually want all three, because each one reveals a different kind of failure.

---

## 3. Four Evaluation Dimensions

This project already organizes evaluation around four important dimensions in `lib/evaluation.py`.

### 3.1 Task Completion

This is the most fundamental question:

**Did the agent complete the task successfully?**

Examples:

- Did it answer the user question?
- Did it stay within an acceptable number of steps?
- Did it require intervention or get stuck?

An agent can sound polished while still failing the actual task. That is why task completion should come first.

### 3.2 Quality Control

This focuses on whether the output is appropriate, not just whether it exists.

Examples:

- Was the answer in the expected format?
- Did it follow the prompt instructions?
- Did it use the provided context properly?
- Did it avoid unsupported claims?

A response can be factually close but still low quality if it ignores instructions or produces the wrong structure.

### 3.3 Tool Interaction

Agents often fail because of tool usage problems rather than language problems.

Examples:

- Did the agent choose the correct tool?
- Were the arguments valid JSON?
- Did the tool call return something useful?
- Did the agent use the tool result correctly afterward?

This dimension is especially important in multi-step systems, because one bad tool call can derail the rest of the run.

### 3.4 System Metrics

This dimension measures operational efficiency.

Examples:

- How many tokens were used?
- How long did the run take?
- How much latency came from tools?
- What was the approximate cost?

These metrics matter because two agents can achieve the same quality but with very different cost and speed.

In practice, a strong agent is not only correct. It is also efficient and consistent.

---

## 4. Three Evaluation Strategies

There is no single best evaluation method for every situation. Instead, different strategies answer different questions.

### 4.1 Final Response Evaluation

This strategy evaluates only the final answer.

It is useful when you want a quick, high-level check of end-to-end behavior:

- Did the user get a good response?
- Did the answer appear complete?
- Was the output formatted correctly?

This can be done with:

- exact-match style checks for simple tasks,
- heuristic checks,
- or an **LLM-as-judge** that scores the answer against the task and an optional reference answer.

Benefits:

- Simple to run
- Good for benchmark comparisons
- Great for regression testing

Limitations:

- It does not explain *why* the agent succeeded or failed.
- A correct-looking final answer may hide poor tool use or wasted steps.

### 4.2 Single-Step Evaluation

This strategy evaluates one local decision at a time.

Typical questions:

- Did the agent choose retrieval when retrieval was expected?
- Did it send valid tool arguments?
- Did it call a tool when no tool was needed?

Benefits:

- Fast to inspect
- Helpful for debugging tool selection
- Useful when improving prompts or tool descriptions

Limitations:

- It does not capture the full quality of the run.
- A locally correct decision does not guarantee a globally good answer.

### 4.3 Trajectory Evaluation

This strategy evaluates the entire run, including the path the agent took through the system.

Typical questions:

- How many steps did the agent take?
- Which tools were used?
- Did the run stay within expected limits?
- Did the agent produce a final answer after tool execution?

Benefits:

- Best view of workflow quality
- Helps diagnose looping, unnecessary tool usage, and weak planning
- Especially valuable for agents with tools, memory, and routing

Limitations:

- Requires richer execution traces
- More setup than a simple final-answer check

In practice, trajectory evaluation is often the most informative strategy for real agents, while final-response evaluation is the easiest place to start.

---

## 5. What an Evaluation System Needs

No matter which strategy you use, a useful evaluation system needs four core ingredients.

### 5.1 Inputs

These are the things the agent receives:

- the user query,
- instructions,
- available tools,
- retrieved documents,
- memory,
- and any other context.

If the inputs change, the evaluation outcome may change too. That is why consistency matters.

### 5.2 Outputs

These are the things the agent produces:

- final responses,
- tool calls,
- intermediate messages,
- and execution traces.

For a simple chatbot, the output may just be text. For an agent, it is usually much more than that.

### 5.3 Reference Data

This is the benchmark you compare against.

Examples:

- a reference answer,
- an expected tool,
- an expected number of steps,
- or a known-good action sequence.

Sometimes you have exact ground truth. Sometimes you only have approximate expectations. Both can still be useful if applied consistently.

### 5.4 Evaluators

These are the mechanisms that score the run.

Examples:

- deterministic rules,
- heuristics,
- exact comparisons,
- or an LLM-as-judge.

An LLM judge is flexible, especially for open-ended outputs, but it should not be your only evaluator. Pairing model-based judgment with deterministic checks gives you a stronger signal.

For example:

- Use a deterministic check to verify that a tool call used valid JSON.
- Use an LLM judge to assess whether the final written answer is complete and helpful.

That combination is usually better than either method alone.

---

## 6. Common Pitfalls and Best Practices

Agent evaluation is powerful, but it is easy to misuse if the benchmark or metrics are too narrow.

### Common pitfalls

#### Measuring only final correctness

If you only judge the final answer, you may miss:

- poor tool choices,
- excessive cost,
- unnecessary retries,
- or brittle internal behavior.

#### Overfitting to a tiny benchmark

If you tune the agent against just a few hand-picked examples, it may look better without actually becoming more robust.

#### Using only subjective judging

An LLM judge can be helpful, but relying on it alone can make your scores noisy and hard to compare.

#### Ignoring efficiency

An answer that is correct but uses twice the tokens and five times the latency may not be the better system.

### Best practices

#### Separate objective and subjective checks

Use deterministic checks for things like:

- valid tool arguments,
- expected tool selection,
- step counts,
- and token usage.

Use LLM judging for things like:

- completeness,
- clarity,
- and overall usefulness.

#### Keep a stable benchmark set

Create a small but representative suite of tasks and reuse it when comparing versions. That is how you detect regressions.

#### Measure both quality and cost

Track correctness and instruction-following, but also measure runtime, tokens, and cost. A practical agent needs both.

#### Evaluate over time

The goal is not to get a perfect score once. The goal is to make reliable improvements and prevent backsliding as prompts, tools, or memory systems change.

#### Use evaluation to drive design

Evaluation should help you answer questions like:

- Are tool descriptions unclear?
- Is retrieval too weak?
- Is the agent looping?
- Is memory helping or distracting?

That is what makes evaluation useful in engineering, not just interesting in theory.

---

## 7. How This Maps to This Project

This repository already has most of the pieces needed for a useful agent evaluation workflow.

### `lib/evaluation.py`

This file is the central evaluation layer.

It already defines:

- `TaskCompletionMetrics`
- `QualityControlMetrics`
- `ToolInteractionMetrics`
- `SystemMetrics`
- `EvaluationResult`
- `TestCase`
- `JudgeEvaluation`
- `AgentEvaluator`

It also already supports three important evaluation methods:

- `evaluate_final_response(...)`
- `evaluate_single_step(...)`
- `evaluate_trajectory(...)`

That means the project already has a clean place to represent benchmarks, run evaluations, and return structured results.

### `lib/agents.py`

This file provides the execution loop for the agent.

It is important for evaluation because it already manages:

- the user query,
- the system instructions,
- message history,
- tool calls,
- tool results,
- and cumulative token tracking in the agent state.

Those are exactly the ingredients needed to evaluate both decisions and full runs.

### `lib/state_machine.py`

This file provides the execution trace.

Its `Run` and `Snapshot` abstractions are especially valuable because they let you inspect:

- which steps executed,
- in what order,
- what the state looked like at each step,
- and how the final state was produced.

That is what makes trajectory evaluation possible.

### `lib/memory.py`

This file already separates short-term and long-term memory concepts.

For evaluation, it can become useful in a few ways later:

- storing past evaluation runs,
- keeping benchmark histories by session,
- comparing previous and current behavior,
- or saving notes about failure patterns.

It is not required for a first evaluation system, but it can support historical analysis over time.

### `lib/vector_db.py`

This file manages vector storage and semantic retrieval.

Although it is mainly used for document retrieval, it could also support future evaluation workflows such as:

- storing benchmark examples,
- retrieving similar past failure cases,
- archiving evaluation artifacts,
- or building retrieval-focused test datasets.

Again, this is optional for the first version, but it fits naturally with the project’s architecture.

---

## Project Implementation

Below is a practical plan for implementing agent evaluation in this project using the existing `/lib` modules.

### 1. Define benchmark cases

Start by creating a small suite of representative `TestCase` objects from `lib/evaluation.py`.

The suite should include:

- **Direct retrieval cases** where the answer should come from the local game dataset
- **Web-search-needed cases** where local knowledge is not enough
- **Ambiguous cases** where the agent must choose carefully or ask for more information
- **Failure or edge cases** where the agent may not have enough information and should respond cautiously

For each test case, include:

- an `id`,
- a short `description`,
- the `user_query`,
- the `expected_tools`,
- an optional `reference_answer`,
- and an optional `max_steps`.

This benchmark suite becomes the stable foundation for all future comparisons.

### 2. Evaluate end-to-end behavior first

Begin with the simplest evaluation method: the final answer.

For each benchmark query:

1. Run the current agent
2. Capture the final response
3. Measure execution time and token usage
4. Pass that information into `AgentEvaluator.evaluate_final_response(...)`

This gives you an initial black-box score for:

- task completion,
- format correctness,
- instruction following,
- token usage,
- runtime,
- and approximate cost.

This is the easiest place to start because it tells you whether the system is useful before you worry about deeper debugging.

### 3. Add step-level debugging for tool use

Once end-to-end results exist, start inspecting local decisions.

Use the completed run’s message history to identify cases where the agent:

- picked the wrong tool,
- skipped a tool it should have used,
- or produced malformed tool arguments.

Then use `AgentEvaluator.evaluate_single_step(...)` to score those decisions.

This is especially useful when diagnosing:

- weak retrieval behavior,
- unnecessary web searches,
- invalid tool arguments,
- or confusion caused by tool descriptions.

In other words, this stage helps explain *why* an end-to-end result was weak.

### 4. Use trajectory evaluation for full workflow quality

After that, move to the full run analysis.

Take the `Run` object returned by the state machine and pass it to `AgentEvaluator.evaluate_trajectory(...)`.

This lets you measure:

- the total number of steps,
- which tools were used,
- whether the run stayed within expected limits,
- whether expected tools appeared in the trajectory,
- and whether a final answer was produced.

For a multi-step agent, this should become the main evaluation strategy, because it balances quality, behavior, and efficiency.

### 5. Improve instrumentation where needed

As you evaluate more runs, you may discover places where richer instrumentation would help.

One immediate improvement is to make sure `total_tokens` is consistently present in the agent state throughout all runs.

From there, you can add optional instrumentation such as:

- per-tool latency,
- tool execution errors,
- retrieval confidence or similarity scores,
- or richer run metadata.

These should be **additive extensions**, not architectural rewrites. The goal is to improve measurement without changing the core behavior of the agent.

### 6. Report and compare results

Once the benchmark and evaluations exist, summarize the results in a notebook or small reporting helper.

Use the same benchmark set each time and compare results across changes such as:

- prompt revisions,
- tool description changes,
- retrieval improvements,
- memory integration,
- or model swaps.

This is where evaluation becomes most valuable: not as a one-time score, but as a way to compare versions and catch regressions.

### 7. Optional future enhancements

After the basic evaluation workflow is stable, you can expand it carefully.

Good next steps include:

- persisting benchmark results for historical comparison,
- adding deterministic checks for known-answer queries,
- adding human review for subjective qualities like helpfulness or tone,
- or storing evaluation artifacts in memory or a vector store for later analysis.

These enhancements are valuable, but they should come after the core benchmark and evaluation loop is already working.

---

## Public Interfaces and Types to Reuse

This implementation should continue to center on the existing abstractions:

- `TestCase` as the benchmark definition format
- `EvaluationResult` as the structured output of an evaluation
- `Run` and `Snapshot` as the source of trajectory data

If you extend the system later, keep those changes additive. Good examples include:

- optional latency or error fields in system metrics,
- or helper utilities for benchmark execution and reporting outside the core agent runtime.

That keeps the evaluation system aligned with the current architecture while leaving room for richer analysis later.

