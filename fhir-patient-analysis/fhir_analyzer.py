
"""
FHIR Patient Data Analyzer

This module provides the FHIRPatientAnalyzer class, which computes summary
statistics from a FHIR R4 Patient Bundle, including gender distribution and
age-related metrics.
"""

import datetime
import logging
from typing import Dict, List, Optional, Tuple

# Configure module-level logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FHIRPatientAnalyzer:
    """
    Extracts and computes statistics from a FHIR R4 Patient Bundle.

    This class analyzes patient demographics including gender distribution
    and age statistics derived from birthdates.
    """

    def __init__(self, bundle: Dict):
        """
        Initialize the FHIR Patient Analyzer.

        Args:
            bundle: A parsed FHIR Bundle as a Python dictionary
        """
        self.bundle = bundle

    def compute_statistics(self) -> Dict:
        """
        Compute comprehensive statistics from the FHIR Patient Bundle.

        Returns:
            A dictionary containing:
                - total_patients: Total count of Patient resources
                - gender_distribution: Dict mapping gender values to counts
                - patients_missing_gender: Count of patients without gender field
                - patients_with_birthdate: Count of patients with birthDate field
                - age_statistics: Dict with min_age, max_age, mean_age (or None)
        """
        logger.info("Starting statistics computation")

        # Extract all Patient resources from the bundle
        patients = self._extract_patients()

        # Compute total patient count
        total_patients = len(patients)

        # Compute gender distribution and missing gender count
        gender_distribution, patients_missing_gender = self._compute_gender_distribution(patients)

        # Compute age statistics and count of patients with birthdate
        patients_with_birthdate, age_statistics = self._compute_age_statistics(patients)

        statistics = {
            "total_patients": total_patients,
            "gender_distribution": gender_distribution,
            "patients_missing_gender": patients_missing_gender,
            "patients_with_birthdate": patients_with_birthdate,
            "age_statistics": age_statistics
        }

        logger.info("Statistics computation completed")
        return statistics

    def _extract_patients(self) -> List[Dict]:
        """
        Extract Patient resources from the FHIR Bundle.

        Safely navigates the bundle structure and filters for Patient resources.

        Returns:
            List of Patient resource dictionaries
        """
        # Check if 'entry' key exists and is a list
        if "entry" not in self.bundle:
            logger.warning("Bundle does not contain 'entry' key - treating as empty")
            return []

        entries = self.bundle["entry"]
        if not isinstance(entries, list):
            logger.warning("Bundle 'entry' is not a list - treating as empty")
            return []

        # Extract resources that are Patient types
        patients = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patients.append(resource)

        logger.info(f"Extracted {len(patients)} Patient resources from bundle")
        return patients

    def _compute_gender_distribution(self, patients: List[Dict]) -> Tuple[Dict[str, int], int]:
        """
        Compute gender distribution and count patients missing gender field.

        Args:
            patients: List of Patient resource dictionaries

        Returns:
            Tuple of (gender_counts_dict, missing_gender_count)
        """
        gender_counts = {}
        missing_gender_count = 0

        for patient in patients:
            if "gender" in patient:
                gender_value = patient["gender"]
                gender_counts[gender_value] = gender_counts.get(gender_value, 0) + 1
            else:
                missing_gender_count += 1

        logger.info(f"Gender distribution: {gender_counts}, Missing: {missing_gender_count}")
        return gender_counts, missing_gender_count

    def _compute_age_statistics(self, patients: List[Dict]) -> Tuple[int, Optional[Dict]]:
        """
        Compute age statistics from patient birthdates.

        Args:
            patients: List of Patient resource dictionaries

        Returns:
            Tuple of (count_with_birthdate, age_statistics_dict_or_None)
        """
        valid_ages = []
        patients_with_birthdate = 0

        for patient in patients:
            if "birthDate" not in patient:
                continue

            patients_with_birthdate += 1
            birthdate_string = patient["birthDate"]

            # Attempt to calculate age from the birthdate
            age = self._calculate_age_from_birthdate(birthdate_string)
            if age is not None:
                valid_ages.append(age)

        # If no valid ages found, return None for age statistics
        if not valid_ages:
            logger.info("No valid birthdates found for age calculation")
            return patients_with_birthdate, None

        # Calculate min, max, and mean age
        min_age = min(valid_ages)
        max_age = max(valid_ages)
        mean_age = sum(valid_ages) // len(valid_ages)  # Integer division for whole years

        age_statistics = {
            "min_age": min_age,
            "max_age": max_age,
            "mean_age": mean_age
        }

        logger.info(f"Age statistics: {age_statistics}")
        return patients_with_birthdate, age_statistics

    def _calculate_age_from_birthdate(self, birthdate_string: str) -> Optional[int]:
        """
        Calculate age in whole years from an ISO date string.

        Args:
            birthdate_string: ISO format date string (YYYY-MM-DD)

        Returns:
            Age in whole years, or None if parsing fails
        """
        try:
            # Parse the ISO date string
            birthdate = datetime.datetime.strptime(birthdate_string, "%Y-%m-%d").date()

            # Calculate age in days, then convert to whole years
            today = datetime.date.today()
            age_in_days = (today - birthdate).days
            age_in_years = age_in_days // 365  # Simple integer division

            return age_in_years

        except ValueError as error:
            logger.warning(f"Failed to parse birthdate '{birthdate_string}': {error}")
            return None