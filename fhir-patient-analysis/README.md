
# FHIR Patient Data Loader and Analyzer

A Python application that fetches FHIR R4 Patient data from a remote endpoint, persists it to disk, and computes demographic summary statistics.

---

## Features

- **Robust HTTP fetching** with automatic retry logic and exponential backoff
- **Data persistence** of raw FHIR JSON bundles
- **Demographic analysis** including gender distribution and age statistics
- **Comprehensive test suite** with no external dependencies
- **Clear separation of concerns** between data loading and analysis

---

## Project Structure

```
fhir-patient-analysis/
├── fhir_loader.py          # HTTP fetching and retry logic
├── fhir_analyzer.py         # Statistical computation
├── main.py                  # Pipeline orchestration
├── conftest.py              # pytest configuration
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── .gitignore               # Git exclusions
├── data/
│   └── .gitkeep             # Ensures data/ is tracked
└── tests/
    ├── test_loader.py       # Unit tests for loader
    └── test_analyzer.py     # Unit tests for analyzer
```

---

## Setup

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

1. Clone or download this repository:

```bash
cd fhir-patient-analysis
```

2. (Optional but recommended) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Running the Pipeline

Execute the main pipeline to fetch data, save it, and compute statistics:

```bash
python main.py
```

**What happens:**

1. Fetches up to 100 Patient resources from `https://r4.smarthealthit.org/Patient?_count=100`
2. Saves the raw FHIR Bundle to `data/patients.json`
3. Analyzes the data and prints summary statistics as JSON to stdout

**Sample output:**

```json
{
  "total_patients": 100,
  "gender_distribution": {
    "male": 52,
    "female": 47,
    "other": 1
  },
  "patients_missing_gender": 0,
  "patients_with_birthdate": 98,
  "age_statistics": {
    "min_age": 18,
    "max_age": 89,
    "mean_age": 47
  }
}
```

**Note:** If no valid birthdates are found, `age_statistics` will be `null`.

---

## Running Tests

All tests use mocked data and network calls — no live HTTP requests are made.

### Run all tests:

```bash
pytest
```

### Run with verbose output:

```bash
pytest -v
```

### Run tests for a specific module:

```bash
pytest tests/test_loader.py
pytest tests/test_analyzer.py
```

### Test coverage:

- **`test_loader.py`**: Tests retry logic, timeout handling, error propagation, and file I/O
- **`test_analyzer.py`**: Tests gender distribution, age calculation, missing field handling, and edge cases

---

## Architecture

### Module Responsibilities

#### `fhir_loader.py` — Data Acquisition

- Fetches FHIR data from a remote endpoint
- Implements retry logic with exponential backoff (3 attempts: 0s, 2s, 4s waits)
- Each HTTP request times out after 10 seconds
- Persists raw JSON to disk with formatted indentation
- Raises `RuntimeError` if all retries are exhausted

#### `fhir_analyzer.py` — Statistical Computation

- Parses FHIR Bundle structure
- Computes total patient count
- Calculates gender distribution (counts all gender values as-is)
- Counts patients missing the `gender` field
- Computes age statistics (min, max, mean) from `birthDate` fields
- Handles missing or malformed data gracefully — never raises exceptions on bad patient data

#### `main.py` — Orchestration

- Coordinates the pipeline: load → save → analyze → print
- No business logic — purely sequential coordination
- Allows exceptions from loader and analyzer to propagate naturally

---

## Design Decisions

### Age Calculation

- Ages are calculated as whole years using `(today - birthdate).days // 365`
- No leap year adjustment (acceptable for summary statistics)
- Invalid or malformed birthdates are logged and excluded from age calculations

### Gender Handling

- All gender values are counted as-is (e.g., `"male"`, `"female"`, `"other"`, `"unknown"`)
- No normalization or filtering is applied
- FHIR spec allows multiple gender values; all are respected

### Missing Data

- Patients missing `gender` or `birthDate` fields are counted separately
- Analysis never fails due to incomplete patient records
- If no valid birthdates exist, `age_statistics` is `null`

### Retry Logic

- First attempt: immediate
- Second attempt: after 2-second wait
- Third attempt: after 4-second wait
- Each request has a 10-second timeout
- On exhaustion: descriptive `RuntimeError` with endpoint URL and error details

---

## Error Handling

### Network Failures

If the FHIR endpoint is unreachable or times out repeatedly, the loader will:

1. Log warnings for each failed attempt
2. Retry with exponential backoff
3. Raise `RuntimeError` after 3 failed attempts with a descriptive error message

### Malformed Data

The analyzer handles missing or invalid fields gracefully:

- Missing `entry` key → treated as empty bundle (0 patients)
- Missing `gender` field → counted in `patients_missing_gender`
- Missing `birthDate` field → excluded from age statistics
- Invalid `birthDate` format → logged as warning and excluded from age calculations

---

## Extending the Application

### Changing the FHIR Endpoint

Edit the `FHIR_ENDPOINT` constant in `main.py`:

```python
FHIR_ENDPOINT = "https://your-fhir-server.com/Patient?_count=200"
```

### Adding New Statistics

1. Add a private method to `FHIRPatientAnalyzer` (e.g., `_compute_name_statistics`)
2. Call it from `compute_statistics()` and add the result to the returned dictionary
3. Add corresponding unit tests in `tests/test_analyzer.py`

### Adjusting Retry Behavior

Modify constants at the top of `fhir_loader.py`:

```python
MAX_RETRIES = 5          # Number of attempts
INITIAL_BACKOFF = 1      # First retry wait time (seconds)
TIMEOUT_SECONDS = 15     # HTTP request timeout
```

---

## License

This project is provided as-is for educational and demonstration purposes.

---

## Author

Created as a demonstration of clean, maintainable Python code following best practices for separation of concerns, error handling, and testability.