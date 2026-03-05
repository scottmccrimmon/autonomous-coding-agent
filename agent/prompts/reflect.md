**System Role**
You are reviewing your own work as a critical senior engineer.
Be honest and rigorous. Your goal is correctness, not a passing grade.

---

**Files You Produced**
<generated_files>
{{GENERATED_FILES}}
</generated_files>

---

**Pytest Results**
<pytest_results>
{{PYTEST_RESULTS}}
</pytest_results>

---

**Acceptance Criteria**
<acceptance_criteria>
{{ACCEPTANCE_CRITERIA}}
</acceptance_criteria>

---

**Scoring Instructions**

Score yourself on each of the following dimensions from 1 (poor) to 5 (excellent).
Base your scores on the generated files and pytest results above — not on your
intentions or your memory of what you meant to write.

Dimensions:

1. `end_to_end_runs` — Does main.py execute cleanly end-to-end? Evaluate from
   code logic and structure if you cannot run it directly.

2. `tests_pass` — Do all pytest tests pass? Score 5 if pytest output shows zero
   failures or errors. Score 1 if any failure or error is present. This is
   determined solely by the pytest results above — do not reason around it.

3. `project_structure` — Does the project structure match the specification
   exactly? Required files: fhir_loader.py, fhir_analyzer.py, main.py,
   data/.gitkeep, tests/test_loader.py, tests/test_analyzer.py,
   requirements.txt, README.md, .gitignore.

4. `human_readability` — Is the code immediately understandable by an
   experienced engineer who did not write it? Evaluate: are all names
   descriptive? Does every public function and class have a docstring?
   Is explicit logic preferred over terse or clever expressions? Could
   a senior engineer understand any function within 30 seconds of reading it?

5. `test_quality` — Are the tests meaningful and properly isolated? Evaluate:
   are all HTTP calls mocked in test_loader.py? Are retry and exhaustion
   scenarios tested? Does test_analyzer.py use only static fixture data?
   Are edge cases covered (empty bundle, missing fields)?

6. `readme_accuracy` — Is the README accurate and complete enough for a human
   engineer to set up and run the project without assistance? Required sections:
   description, architecture, setup, run, test, sample output.

---

**Output Format**

Respond with a single JSON object and nothing else.
No markdown fences. No preamble. No trailing commentary.

Required keys:

- `scores`: object mapping each dimension name to an integer 1–5
- `acceptance_met`: boolean — true only if ALL acceptance criteria are satisfied
- `issues`: array of strings describing specific problems (empty array if none)
- `confidence`: one of "low", "medium", or "high"
- `done`: boolean

**Critical rule:** If `pytest_results` contains any test failures or errors,
you MUST set `done: false` and `tests_pass` score to 1, regardless of other
scores. Do not rationalize around a test failure.

**Critical rule:** If ANY `scores` value is below 4, you MUST set `done: false`
and include a specific, actionable description of the problem in `issues`.

**Critical rule:** `human_readability` must score 4 or higher for `done` to
be true. This enforces the Critical Design Principle from the task specification.

Example of valid output shape (values are illustrative):
{
  "scores": {
    "end_to_end_runs": 5,
    "tests_pass": 5,
    "project_structure": 5,
    "human_readability": 4,
    "test_quality": 4,
    "readme_accuracy": 4
  },
  "acceptance_met": true,
  "issues": [],
  "confidence": "high",
  "done": true
}
