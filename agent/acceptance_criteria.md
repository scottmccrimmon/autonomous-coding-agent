# Completion Criteria

Version: 2.0

The task is complete when ALL of the following criteria are satisfied.
These criteria are evaluated by the PAR agent during the Reflect phase
and enforced by the harness. Every item must be true for `done: true`.

---

## Functional Criteria

1. **Pytest passes with zero failures or errors.**
   Running `pytest tests/` produces a clean result. This is a hard gate —
   any test failure means the task is not complete, regardless of the
   state of other criteria.

2. **End-to-end execution succeeds.**
   `main.py` runs without raising an exception. The loader fetches and
   persists patient data, the analyzer computes statistics, and the
   output is printed as formatted JSON.

3. **Summary statistics are produced.**
   The output includes at minimum: total patient count, gender
   distribution, count of patients missing gender, count of patients
   with a birthDate, and age statistics where birthDate is available.

4. **Project structure matches the specification exactly.**
   All required files are present and correctly located:
   `fhir_loader.py`, `fhir_analyzer.py`, `main.py`, `data/.gitkeep`,
   `tests/test_loader.py`, `tests/test_analyzer.py`,
   `requirements.txt`, `README.md`, `.gitignore`.

5. **GitHub repository has been created and committed.**
   The harness has successfully created the repository and committed
   all project files. This is handled by the harness — the agent does
   not need to verify it directly.

---

## Quality Criteria

6. **Code is immediately readable by an experienced human engineer.**
   All public functions and classes have docstrings. Variable and
   function names are descriptive. No function exceeds 40 lines.
   Explicit logic is used in preference to terse or clever expressions.
   This criterion reflects the Critical Design Principle of the task
   specification and is a hard gate equivalent to the pytest criterion.

7. **Tests are meaningful and properly isolated.**
   All HTTP calls in `test_loader.py` are mocked. Retry logic and
   exhaustion are explicitly tested. `test_analyzer.py` uses only
   static fixture data. Edge cases are covered.

8. **README is accurate and complete.**
   All six required sections are present: description, architecture,
   setup, run, test, and sample output. Instructions match the actual
   implementation — the README describes the code that exists, not an
   idealized version.

---

## Summary

| Criterion | Type | Hard Gate |
|---|---|---|
| Pytest passes | Functional | Yes |
| End-to-end runs | Functional | No |
| Statistics produced | Functional | No |
| Project structure correct | Functional | No |
| GitHub commit created | Functional | No |
| Human readability | Quality | Yes |
| Test quality | Quality | No |
| README accuracy | Quality | No |

A "hard gate" criterion sets `done: false` unconditionally if not met,
regardless of scores on other criteria.