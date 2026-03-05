
"""
Unit tests for FHIRPatientLoader

Tests the loader's retry logic, timeout handling, and file saving capabilities
using mocked HTTP requests. No live network calls are made.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from fhir_loader import FHIRPatientLoader


# Sample FHIR Bundle data for testing
SAMPLE_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 2,
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "1",
                "gender": "male"
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "2",
                "gender": "female"
            }
        }
    ]
}


def test_successful_fetch_and_save(tmp_path):
    """
    Test successful data fetch and save on first attempt.

    Verifies that the loader correctly fetches data and writes it to disk
    when the HTTP request succeeds immediately.
    """
    # Setup: define output path in temporary directory
    output_file = tmp_path / "patients.json"
    endpoint_url = "https://example.com/Patient"

    # Mock the requests.get call to return successful response
    with patch('fhir_loader.requests.get') as mock_get:
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BUNDLE
        mock_get.return_value = mock_response

        # Execute: create loader and run the process
        loader = FHIRPatientLoader(
            endpoint_url=endpoint_url,
            output_path=str(output_file)
        )
        loader.load_and_save()

    # Assert: verify the file was created with correct content
    assert output_file.exists()

    with open(output_file, 'r', encoding='utf-8') as file:
        saved_data = json.load(file)

    assert saved_data == SAMPLE_BUNDLE


def test_retry_on_http_error_then_success(tmp_path):
    """
    Test retry logic when initial requests fail but eventually succeed.

    Verifies that the loader retries after failures and succeeds on the
    third attempt.
    """
    # Setup
    output_file = tmp_path / "patients.json"
    endpoint_url = "https://example.com/Patient"

    # Mock requests.get to fail twice, then succeed
    with patch('fhir_loader.requests.get') as mock_get:
        # Configure mock to fail twice with Timeout, then succeed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BUNDLE

        mock_get.side_effect = [
            requests.exceptions.Timeout("Connection timeout"),
            requests.exceptions.Timeout("Connection timeout"),
            mock_response
        ]

        # Execute
        loader = FHIRPatientLoader(
            endpoint_url=endpoint_url,
            output_path=str(output_file)
        )
        loader.load_and_save()

        # Assert: verify requests.get was called exactly 3 times
        assert mock_get.call_count == 3

    # Assert: verify the file was created with correct content
    assert output_file.exists()

    with open(output_file, 'r', encoding='utf-8') as file:
        saved_data = json.load(file)

    assert saved_data == SAMPLE_BUNDLE


def test_raises_error_after_all_retries_exhausted(tmp_path):
    """
    Test that RuntimeError is raised when all retry attempts fail.

    Verifies that the loader raises a descriptive error after exhausting
    all retry attempts.
    """
    # Setup
    output_file = tmp_path / "patients.json"
    endpoint_url = "https://example.com/Patient"

    # Mock requests.get to fail all attempts
    with patch('fhir_loader.requests.get') as mock_get:
        # Configure mock to always raise ConnectionError
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Execute and assert: expect RuntimeError
        loader = FHIRPatientLoader(
            endpoint_url=endpoint_url,
            output_path=str(output_file)
        )

        with pytest.raises(RuntimeError) as exc_info:
            loader.load_and_save()

        # Verify error message contains endpoint URL and attempt count
        error_message = str(exc_info.value)
        assert endpoint_url in error_message
        assert "3 attempts" in error_message
        assert "ConnectionError" in error_message


def test_timeout_respected(tmp_path):
    """
    Test that the timeout parameter is correctly passed to requests.get.

    Verifies that each HTTP request is made with the configured timeout value.
    """
    # Setup
    output_file = tmp_path / "patients.json"
    endpoint_url = "https://example.com/Patient"

    # Mock requests.get to check timeout parameter
    with patch('fhir_loader.requests.get') as mock_get:
        # Configure mock to return successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_BUNDLE
        mock_get.return_value = mock_response

        # Execute
        loader = FHIRPatientLoader(
            endpoint_url=endpoint_url,
            output_path=str(output_file)
        )
        loader.load_and_save()

        # Assert: verify timeout parameter was passed correctly
        mock_get.assert_called_once_with(endpoint_url, timeout=10)