
"""
FHIR Patient Data Pipeline Orchestration

This module coordinates the entire pipeline: fetching FHIR Patient data from
a remote endpoint, saving it to disk, and computing summary statistics.
"""

import json

from fhir_loader import FHIRPatientLoader
from fhir_analyzer import FHIRPatientAnalyzer


def run_pipeline() -> None:
    """
    Execute the complete FHIR data pipeline.

    Steps:
        1. Fetch FHIR Patient data from remote endpoint
        2. Save raw JSON to disk
        3. Load saved data
        4. Compute statistics
        5. Print results as formatted JSON
    """
    # Configuration constants
    FHIR_ENDPOINT = "https://r4.smarthealthit.org/Patient?_count=100"
    OUTPUT_FILE_PATH = "data/patients.json"

    # Step 1 & 2: Fetch and save FHIR data
    loader = FHIRPatientLoader(
        endpoint_url=FHIR_ENDPOINT,
        output_path=OUTPUT_FILE_PATH
    )
    loader.load_and_save()

    # Step 3: Read the saved data back from disk
    with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as file:
        bundle_data = json.load(file)

    # Step 4: Analyze the FHIR data
    analyzer = FHIRPatientAnalyzer(bundle=bundle_data)
    statistics = analyzer.compute_statistics()

    # Step 5: Print results as formatted JSON
    print(json.dumps(statistics, indent=2))


if __name__ == "__main__":
    run_pipeline()