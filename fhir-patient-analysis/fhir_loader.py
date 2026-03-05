
"""
FHIR Patient Data Loader

This module provides the FHIRPatientLoader class, which fetches FHIR Patient
data from a remote endpoint with retry logic and persists the raw JSON response
to disk.
"""

import json
import logging
import os
import time
from typing import Dict

import requests

# Retry and timeout configuration constants
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds
TIMEOUT_SECONDS = 10

# Configure module-level logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FHIRPatientLoader:
    """
    Fetches FHIR Patient data from a remote endpoint and saves it to disk.

    This class handles HTTP requests with automatic retry logic and exponential
    backoff. It persists the retrieved FHIR Bundle as formatted JSON.
    """

    def __init__(self, endpoint_url: str, output_path: str):
        """
        Initialize the FHIR Patient Loader.

        Args:
            endpoint_url: The full URL to fetch FHIR data from
            output_path: File path where JSON will be saved
        """
        self.endpoint_url = endpoint_url
        self.output_path = output_path

    def load_and_save(self) -> None:
        """
        Orchestrate the fetch and save process.

        Fetches data from the FHIR endpoint with retry logic, then saves
        the response to disk as formatted JSON.

        Raises:
            RuntimeError: If all retry attempts are exhausted
        """
        logger.info("Starting FHIR data fetch and save process")

        # Fetch data with retry logic
        bundle_data = self._fetch_with_retry()

        # Save the fetched data to disk
        self._save_to_disk(bundle_data)

        logger.info("FHIR data fetch and save process completed successfully")

    def _fetch_with_retry(self) -> Dict:
        """
        Fetch data from the FHIR endpoint with retry logic.

        Implements exponential backoff: attempts at 0s, then waits 2s, then 4s.
        Each HTTP request has a 10-second timeout.

        Returns:
            The parsed JSON response as a dictionary

        Raises:
            RuntimeError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Attempt {attempt}/{MAX_RETRIES}: Fetching from {self.endpoint_url}"
                )

                response = requests.get(
                    self.endpoint_url,
                    timeout=TIMEOUT_SECONDS
                )

                # Raise an exception for HTTP error status codes
                response.raise_for_status()

                # Parse and return the JSON response
                data = response.json()
                logger.info(f"Successfully fetched data on attempt {attempt}")
                return data

            except (requests.exceptions.RequestException, ValueError) as error:
                last_error = error
                logger.warning(
                    f"Attempt {attempt}/{MAX_RETRIES} failed: {type(error).__name__}: {error}"
                )

                # If this was not the last attempt, wait before retrying
                if attempt < MAX_RETRIES:
                    # Calculate backoff: 2s for first retry, 4s for second retry
                    backoff_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(f"Waiting {backoff_time} seconds before retry...")
                    time.sleep(backoff_time)

        # All retries exhausted - raise RuntimeError
        error_message = (
            f"Failed to fetch data from {self.endpoint_url} after {MAX_RETRIES} attempts. "
            f"Last error: {type(last_error).__name__}: {last_error}"
        )
        logger.error(error_message)
        raise RuntimeError(error_message)

    def _save_to_disk(self, data: Dict) -> None:
        """
        Save the FHIR data to disk as formatted JSON.

        Creates the output directory if it does not exist.

        Args:
            data: The FHIR Bundle data to save
        """
        # Ensure the output directory exists
        output_dir = os.path.dirname(self.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Write the data as formatted JSON
        with open(self.output_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        logger.info(f"Data successfully saved to {self.output_path}")