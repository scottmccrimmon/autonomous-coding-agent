# Reflective Execution Loop Demo

## Overview

This repository demonstrates a **Reflective Execution Loop**, also referred to here as a **Plan–Act–Reflect (PAR) loop**, for autonomous AI coding agents.

The core idea is simple but powerful:

> An agent plans its work, acts on a real codebase, and then reflects on the quality of its own output before deciding whether further iteration is necessary.

While the loop structure itself is not new, it has deep roots across multiple disciplines that long predate large language models. Variants of the Plan–Act–Reflect pattern appear in control theory and cybernetics (closed-loop feedback systems), quality and process improvement methodologies (e.g., Deming's Plan–Do–Check–Act cycle), reinforcement learning (policy → action → reward → update), and cognitive science (metacognition and self-monitoring).

What is novel today is not the structure of the loop, but the capability of modern large language models to perform all phases of the loop within a single system at a level sufficient for real engineering work. Increasing context windows, improved reasoning, and the ability to critique prior outputs make reflective execution both practical and surprisingly effective.

This implementation is inspired by, and builds upon, ideas discussed publicly by practitioners and researchers exploring long-running and self-reflective agents. In particular, it draws conceptual inspiration from blog posts by Graham Huntley on autonomous coding loops, from Anthropic's engineering work on effective harnesses for long-running agents, and from broader community discussions around reflective and iterative agent architectures. This repository does not claim originality of the underlying ideas; rather, it aims to provide a clear, minimal, and inspectable reference implementation that makes these concepts concrete.

---

## What This Repository Demonstrates

This project shows how to:

* Build an **autonomous coding agent** with clear safety boundaries
* Encode **engineering judgment** into prompts and evaluation criteria
* Avoid uncontrolled or opaque "agent magic"
* Achieve convergence through reflection rather than brute-force iteration
* Keep humans accountable for goals, constraints, and outcomes
* Extend agent capabilities through a **composable skills registry**
* Integrate with external systems (e.g., GitHub) through structured, auditable side effects

The emphasis is on **clarity, control, and correctness**, not maximal automation.

---

## The Reflective Execution Loop (PAR)

The agent operates using a simple, explicit loop driven by **three distinct LLM calls per iteration**:

1. **Plan**
   The agent analyzes the task specification, constraints, and any prior reflection output, and produces a concrete implementation plan.

2. **Act**
   The agent carries out the plan by creating or modifying files within strictly defined filesystem boundaries. Token limits are tuned per phase to balance output completeness with cost efficiency (`MAX_TOKENS_PLAN=4096`, `MAX_TOKENS_ACT=16000`, `MAX_TOKENS_REFLECT=1024`).

3. **Reflect**
   The agent evaluates its own work against predefined acceptance criteria and a reflection rubric — including the results of real `pytest` test execution — and returns a structured JSON verdict that determines whether to iterate or exit.

This loop repeats until either:

* the acceptance criteria are met and the agent returns `done=true`, or
* a maximum iteration limit is reached.

Importantly, **iteration only happens when reflection identifies specific deficiencies**. Well-scoped tasks often converge in a single cycle. When issues are identified, they are fed back explicitly into the next Act prompt — creating a genuinely closed remediation loop rather than stateless retry.

The harness enforces all iteration logic, filesystem boundaries, test execution, and GitHub commits. **The LLM never executes code or mutates the environment directly.**

---

## Architecture

The codebase is organized into clearly separated modules with distinct responsibilities:

```
harness/
  ├── agent.py            # All LLM interaction and prompt I/O (Anthropic Messages API)
  ├── filesystem.py       # Write boundary enforcement; reads generated artifacts for reflection
  ├── loop.py             # Minimal agent loop implementation
  └── skills/
       ├── __init__.py    # Extensible skills registry
       ├── base.py        # BaseSkill abstract class
       ├── shell.py       # Shell execution skill (runs pytest, etc.)
       └── github.py      # GitHub API skill (automated commits on convergence)

agent/
  ├── task_spec.md              # What the agent is asked to do
  ├── acceptance_criteria.md    # Definition of "done"
  ├── reflection_rubric.md      # How the agent evaluates its own work
  └── prompts/
       ├── plan.md
       ├── act.md
       └── reflect.md
```

### Module Responsibilities

**`agent.py`** owns all LLM interaction. It constructs phase-specific prompts, calls the Anthropic Messages API (`claude-sonnet-4-5`), and parses structured responses. It has no awareness of the filesystem or side-effecting tools.

**`filesystem.py`** enforces the write boundary — the agent may only create or modify files within the designated output directory. It also reads generated artifacts back into the reflection prompt, ensuring the agent evaluates what was actually written.

**`skills/`** is an extensible registry of side-effecting capabilities. Adding a new skill means subclassing `BaseSkill`, implementing an availability check, and registering it. The loop itself requires no changes.

---

## Skills Registry

The skills architecture decouples capability extension from loop logic. Currently registered skills:

| Skill | Purpose |
|---|---|
| `ShellSkill` | Executes `pytest` via `sys.executable -m pytest` and returns structured test results |
| `GitHubSkill` | Commits generated artifacts to a target repository when `done=true` is returned |

Availability checks ensure skills degrade gracefully when dependencies are absent (e.g., missing GitHub credentials).

---

## Design Principles

This implementation intentionally prioritizes:

* **Explicitness over cleverness** — every prompt, boundary, and decision point is inspectable
* **Constraints over implicit trust** — the harness controls all side effects; the agent only generates
* **Reflection over trial-and-error** — iteration is driven by structured self-evaluation, not random retry
* **Closed-loop remediation** — identified issues are explicitly fed back into the next iteration
* **Human accountability over full autonomy** — goals, rubrics, and exit criteria are human-defined

---

## Example Task: FHIR Patient Data Pipeline (V2)

The current demonstration task produces a production-quality FHIR Patient Data Pipeline, generated end-to-end by the PAR loop. The agent autonomously produces:

* **`fhir_loader.py`** — A FHIR R4 patient resource loader with retry/backoff logic
* **`fhir_analyzer.py`** — A statistical analyzer for loaded patient data
* **`test_fhir_pipeline.py`** — A complete `pytest` suite (13/13 tests passing at convergence)
* **`README.md`** — Documentation for the generated project

All artifacts are committed to a [separate GitHub repository](https://github.com/scottmccrimmon/autonomous-coding-agent) via the `GitHubSkill` upon loop convergence.

The V2 task demonstrates that the PAR loop can handle non-trivial, multi-file engineering deliverables with real quality gates — not just toy examples.

*(V1 demonstrated Dockerization of a small MNIST CNN training project — see git history for reference.)*

---

## What This Is (and Is Not)

**This is:**

* A reference implementation of a PAR-based autonomous coding agent
* A learning and experimentation scaffold with inspectable internals
* A demonstration that reflective autonomy can be both capable and auditable
* A foundation for extending agent capabilities through composable skills

**This is not:**

* A production-ready agent framework
* A claim of general intelligence
* A replacement for human engineers

---

## Next Steps

Active areas of exploration:

* **Runtime configurability** — making task spec, output target, and acceptance criteria fully configurable without harness changes
* **Persistent agent memory / scratchpad** — giving the agent access to prior iteration state beyond what fits in the Reflect prompt
* **Native tool use** — integrating Claude's API-level tool-use for richer agent–harness interaction
* **Multi-task generalization** — evaluating convergence behavior across task types and complexity levels
* **Claude Code / Vertex AI integration** — exploring harness deployment within GCP-aligned infrastructure

All extensions should preserve the core principles: transparency, constraint, and human accountability.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
