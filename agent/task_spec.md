# Plan-Act-Reflect (PAR) Task Specification: FHIR Patient Data Loader and Analyzer

Version: 2.0
Status: Active

---

## 1. Objective

Design, implement, test, and commit a working FHIR data pipeline that:

1. Downloads public HL7 FHIR R4 Patient data from a real open endpoint
2. Persists the downloaded data to disk
3. Computes meaningful summary statistics from the Patient bundle
4. Is fully covered by automated unit tests with mocked external calls
5. Is committed to a new GitHub repository via the PAR harness

The PAR system must complete this autonomously using planning, acting,
testing, and reflection.

**Critical Design Principle — Human Readability First:**
All code produced by this task must be immediately understandable and
maintainable by an experienced human software engineer who did not write
it. This is a non-negotiable requirement and takes precedence over
performance optimization, conciseness, or any "clever" implementation
choices. Code that is technically correct but difficult to read or reason
about is considered incomplete. Adoption of AI-assisted development
depends on human engineers trusting and understanding the output.

Specifically:
- Use clear, descriptive names for all variables, functions, and classes
- Prefer explicit logic over implicit or terse expressions
- Include docstrings on all public functions and classes
- Avoid one-liners, nested comprehensions, or lambda expressions where
  a named function would be clearer
- Structure code so a senior engineer can understand any function's
  purpose within 30 seconds of reading it

---

## 2. Functional Requirements

### A. FHIR Data Loader (fhir_loader.py)

Must implement a `FHIRPatientLoader` class that:

- Fetches Patient resources from the SMART Health IT open R4 endpoint:

  ```
  https://r4.smarthealthit.org/Patient?_count=100
  ```

  This is an open endpoint requiring no authentication. It returns a
  standard FHIR R4 Bundle in JSON format with up to 100 Patient entries.

- Implements retry with exponential backoff:
  - Maximum 3 attempts per request
  - Wait times: 2 seconds, then 4 seconds (doubling each retry)
  - Per-attempt timeout: 10 seconds
  - On exhaustion: raise a descriptive `RuntimeError` stating the
    endpoint URL, number of attempts made, and the last error message.
    Never silently return empty or partial data.

- Persists the raw JSON Bundle response to `data/patients.json`

- Logs each operation clearly: fetch attempt number, success or failure,
  and file write confirmation

### B. FHIR Patient Analyzer (fhir_analyzer.py)

Must implement a `FHIRPatientAnalyzer` class that:

- Accepts a FHIR R4 Bundle (as a Python dict) on initialization
- Extracts Patient resources from `bundle["entry"]`
- Computes the following summary statistics:
  - Total number of Patient resources in the bundle
  - Gender distribution as a dict (e.g. `{"male": 52, "female": 48}`)
  - Count of patients missing a gender field
  - Count of patients with a `birthDate` field present
  - Age statistics if `birthDate` is available: min age, max age,
    and mean age (in whole years, calculated from today's date)
- Returns all statistics as a single well-structured Python dict
- Handles missing or malformed fields gracefully without raising
  exceptions — use sensible defaults and log a warning instead

### C. Orchestrator (main.py)

Must implement a `run_pipeline()` function that:

- Instantiates `FHIRPatientLoader` and calls `load_and_save()`
- Reads `data/patients.json` back from disk
- Instantiates `FHIRPatientAnalyzer` with the loaded bundle
- Calls `compute_statistics()` and prints the result as formatted JSON
- Is callable as both an import and a `__main__` entry point

The orchestrator must be thin — it delegates all logic to the loader
and analyzer. No business logic belongs in main.py.

### D. Automated Tests

Must include:

**tests/test_loader.py**
- Test that a successful HTTP response is parsed and saved correctly
- Test that retry logic is triggered on HTTP errors (mock 3 failures
  then a success)
- Test that `RuntimeError` is raised after all retries are exhausted
- All HTTP calls must be mocked using `unittest.mock.patch` —
  no test may make a live network request

**tests/test_analyzer.py**
- Test gender distribution computation with a known fixture bundle
- Test age calculation with patients with known birth dates
- Test graceful handling of missing `gender` and `birthDate` fields
- Test behavior with an empty bundle (zero patients)
- All tests use static fixture data — no file I/O, no network

Use `pytest`. All tests must pass before the PAR loop marks the
task complete.

---

## 3. Project Structure

The agent must produce exactly this structure:

```
fhir-patient-analysis/
│
├── fhir_loader.py
├── fhir_analyzer.py
├── main.py
├── conftest.py
├── data/
│   └── .gitkeep
├── tests/
│   ├── test_loader.py
│   └── test_analyzer.py
├── requirements.txt
├── README.md
└── .gitignore
```

Note: `data/patients.json` is excluded from version control via
`.gitignore`. The `data/` directory itself is tracked via `.gitkeep`.

---

## 4. Supporting Files

### requirements.txt
Must include only what is actually used:
- `requests` — HTTP client for FHIR endpoint
- `pytest` — test runner

No other dependencies are permitted unless strictly necessary and
justified in a code comment.

### .gitignore
Must include at minimum:
- `__pycache__/`
- `.venv/`
- `data/*.json`
- `*.pyc`
- `.env`

### README.md
Must include:
- A plain-English description of what the project does (2–3 sentences)
- Architecture section: brief description of each module's role
- Setup instructions: how to create a virtualenv and install dependencies
- Run instructions: how to execute `main.py`
- Test instructions: how to run `pytest`
- Sample output: a representative example of the statistics JSON

The README must be accurate — it describes the code that was actually
produced, not a hypothetical ideal version.

---

## 5. Non-Functional Requirements

- All modules must have a module-level docstring explaining their purpose
- All public classes and functions must have docstrings
- No function should exceed 40 lines — decompose if needed
- No use of frameworks beyond the standard library and `requests`
- All external HTTP calls must be isolated in `fhir_loader.py` —
  no other module may make network calls
- Retry logic lives exclusively in `fhir_loader.py`

---

## 6. Harness Guarantees

The PAR harness handles the following on your behalf — do not
implement these yourself:

- Running `pytest` after each Act phase and capturing the results
- Injecting pytest output into the Reflect prompt as `{{PYTEST_RESULTS}}`
- Creating the GitHub repository and committing all generated files
  after a successful reflection cycle

Focus entirely on producing correct, readable, tested Python code.

---

## 7. Commit Message

When the harness commits the completed project, it will use:

```
feat: initial FHIR patient data loader and analyzer
```
