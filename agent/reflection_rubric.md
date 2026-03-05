# PAR Reflection Rubric

Version: 2.0

This rubric is used by the PAR agent during the Reflect phase to
evaluate its own output. Each dimension must be scored 1–5. Any score
below 4 requires the agent to set `done: false` and describe the
specific deficiency in `issues`.

The scores must be returned as a JSON object with the exact dimension
names listed below. See reflect.md for the required output format.

---

## Scoring Dimensions

### 1. `end_to_end_runs`
**Does the system run end-to-end without errors?**

- 5 — main.py executes cleanly; loader, analyzer, and output all work
- 4 — minor warnings present but execution completes successfully
- 3 — execution completes with workarounds or partial output
- 2 — execution fails in one component but others work
- 1 — system does not run at all

Evaluate based on code logic and structure. If you cannot verify
execution directly, reason carefully from the implementation.

---

### 2. `tests_pass`
**Do all pytest tests pass?**

- 5 — all tests pass with zero failures or errors
- 3 — some tests pass; failures are minor or isolated
- 1 — any test failure or error is present

**This dimension is binary in practice:** the harness injects actual
pytest output into your prompt. If pytest reports any failure, score
must be 1 and `done` must be false, regardless of other scores.

---

### 3. `project_structure`
**Does the project structure match the specification exactly?**

- 5 — all required files present, correctly named, correctly located
- 4 — one minor deviation (e.g. an extra helper file)
- 3 — a required file is missing or misnamed
- 2 — multiple required files missing or structure significantly wrong
- 1 — structure bears little resemblance to specification

Required structure:
```
fhir-patient-analysis/
├── fhir_loader.py
├── fhir_analyzer.py
├── main.py
├── conftest.py
├── data/.gitkeep
├── tests/test_loader.py
├── tests/test_analyzer.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

### 4. `human_readability`
**Is the code immediately understandable by an experienced engineer
who did not write it?**

- 5 — all names are descriptive; all functions have docstrings; logic
      is explicit; no function exceeds 40 lines; no clever tricks
- 4 — mostly readable with one or two minor lapses in naming or clarity
- 3 — readable overall but contains sections requiring careful study
- 2 — multiple functions that are dense, terse, or poorly named
- 1 — code is correct but requires significant effort to understand

Evaluate specifically:
- Are variable and function names self-explanatory?
- Does every public function and class have a docstring?
- Is explicit logic preferred over terse or implicit expressions?
- Could a senior engineer understand any function in 30 seconds?

This dimension enforces the Critical Design Principle from the task
specification. It must score 4 or higher for the task to be complete.

---

### 5. `test_quality`
**Are the tests meaningful, well-structured, and properly isolated?**

- 5 — tests cover all specified cases; HTTP calls fully mocked;
      fixture data is clear; test names are descriptive
- 4 — good coverage with one minor gap or a slightly unclear fixture
- 3 — tests pass but coverage is thin or mocking is inconsistent
- 2 — tests exist but miss important cases or make live network calls
- 1 — tests are present but provide little confidence in correctness

Evaluate specifically:
- Are all HTTP calls mocked in test_loader.py?
- Do tests cover the retry and exhaustion scenarios?
- Does test_analyzer.py use static fixture data only?
- Are edge cases tested (empty bundle, missing fields)?

---

### 6. `readme_accuracy`
**Is the README accurate and sufficient for a human engineer to
set up and run the project without assistance?**

- 5 — all sections present; instructions are correct and complete;
      sample output is representative
- 4 — all sections present with one minor inaccuracy or omission
- 3 — README exists but is missing a required section or has
      instructions that do not match the actual implementation
- 2 — README is present but substantially incomplete or misleading
- 1 — README is missing or describes a different project

Required sections: description, architecture, setup, run, test,
sample output.

---

## Completion Threshold

The task is complete (`done: true`) only when ALL of the following
are true:

- Every dimension scores 4 or higher
- `tests_pass` reflects zero pytest failures (score of 5)
- `acceptance_met` is true
- `human_readability` scores 4 or higher

If any condition is not met, set `done: false`, populate `issues`
with specific, actionable descriptions of what needs to improve,
and set `confidence` honestly based on how close the output is
to meeting all criteria.

