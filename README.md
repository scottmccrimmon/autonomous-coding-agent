# Reflective Execution Loop Demo

## Overview

This repository demonstrates a **Reflective Execution Loop**, also referred to here as a **Plan–Act–Reflect (PAR) loop**, for autonomous AI coding agents.

The core idea is simple but powerful:

> An agent plans its work, acts on a real codebase, and then reflects on the quality of its own output before deciding whether further iteration is necessary.

While the loop structure itself is not new, it has deep roots across multiple disciplines that long predate large language models. Variants of the Plan–Act–Reflect pattern appear in control theory and cybernetics (closed-loop feedback systems), quality and process improvement methodologies (e.g., Deming’s Plan–Do–Check–Act cycle), reinforcement learning (policy → action → reward → update), and cognitive science (metacognition and self-monitoring).

What is novel today is not the structure of the loop, but the capability of modern large language models to perform all phases of the loop within a single system at a level sufficient for real engineering work. Increasing context windows, improved reasoning, and the ability to critique prior outputs make reflective execution both practical and surprisingly effective.

This implementation is inspired by, and builds upon, ideas discussed publicly by practitioners and researchers exploring long-running and self-reflective agents. In particular, it draws conceptual inspiration from blog posts by Graham Huntley on autonomous coding loops, from Anthropic’s engineering work on effective harnesses for long-running agents, and from broader community discussions around reflective and iterative agent architectures. This repository does not claim originality of the underlying ideas; rather, it aims to provide a clear, minimal, and inspectable reference implementation that makes these concepts concrete.

---

## What This Repository Demonstrates

This project shows how to:

* Build an **autonomous coding agent** with clear safety boundaries
* Encode **engineering judgment** into prompts and evaluation criteria
* Avoid uncontrolled or opaque “agent magic”
* Achieve convergence through reflection rather than brute-force iteration
* Keep humans accountable for goals, constraints, and outcomes

The emphasis is on **clarity, control, and correctness**, not maximal automation.

---

## The Reflective Execution Loop (PAR)

The agent operates using a simple, explicit loop:

1. **Plan**
   The agent analyzes the task, constraints, and existing codebase and produces a concrete implementation plan.

2. **Act**
   The agent carries out the plan by creating or modifying files within strictly defined boundaries.

3. **Reflect**
   The agent evaluates its own work against predefined acceptance criteria and a reflection rubric, then decides whether the task is complete or further iteration is required.

This loop repeats until either:

* the acceptance criteria are met, or
* a maximum iteration limit is reached.

Importantly, **iteration only happens when reflection identifies specific deficiencies**. Well-scoped tasks often converge in a single cycle.

---

## Why This Matters

Traditional software automation struggles with tasks that require judgment, trade-offs, and context awareness. Historically, those gaps were filled by human engineers.

This project demonstrates that:

* Modern LLMs can perform meaningful **self-evaluation**
* Reflection loops dramatically reduce unnecessary rework
* Autonomous agents can be **predictable and inspectable**, not opaque
* Engineering quality improves when autonomy is paired with constraints

The result is not “AI replacing engineers,” but **AI amplifying engineering capability** while preserving human responsibility.

---

## Example Task: MNIST CNN Dockerization

As a concrete demonstration, the agent is tasked with Dockerizing a small MNIST CNN training project.

Constraints include:

* No modification of model or training source code
* CPU-only, headless execution
* Minimal Docker artifacts
* Clear documentation
* No orchestration or production hardening

The agent:

* Plans the Dockerization approach
* Creates Docker artifacts and documentation
* Reflects on correctness, clarity, and scope
* Terminates when the task is complete

This task is intentionally modest so that the agent’s behavior can be closely inspected.

---

## Repository Structure

```
agent/
  ├── task_spec.md              # What the agent is asked to do
  ├── acceptance_criteria.md    # Definition of "done"
  ├── reflection_rubric.md      # How the agent evaluates its own work
  └── prompts/
       ├── plan.md
       ├── act.md
       └── reflect.md

harness/
  └── loop.py                   # Minimal agent loop implementation

mnist-cnn/
  ├── src/                      # Existing training code (read-only to agent)
  ├── docker/                   # Agent-generated Docker artifacts
  └── README.md                 # Agent-updated documentation
```

---

## Design Principles

This implementation intentionally prioritizes:

* **Explicitness over cleverness**
* **Constraints over implicit trust**
* **Reflection over trial-and-error**
* **Human accountability over full autonomy**

All agent actions are mediated by a Python harness that enforces:

* file-system boundaries
* iteration limits
* structured reflection output

The LLM never executes code or mutates the environment directly.

---

## What This Is (and Is Not)

**This is:**

* A reference implementation
* A learning and experimentation scaffold
* A demonstration of reflective autonomy

**This is not:**

* A production-ready agent framework
* A claim of general intelligence
* A replacement for human engineers

---

## Next Steps

Possible extensions include:

* Adding automated test execution during reflection
* Introducing structured tool use
* Evaluating agent behavior on larger or messier codebases
* Studying convergence behavior across task types

All of these should be approached with the same emphasis on transparency and control.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
