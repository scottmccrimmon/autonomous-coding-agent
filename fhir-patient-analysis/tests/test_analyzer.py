
"""
Unit tests for FHIRPatientAnalyzer

Tests the analyzer's statistical computation capabilities using static
fixture data. No file I/O or network calls are made.
"""

import datetime
from fhir_analyzer import FHIRPatientAnalyzer


# Fixture: Bundle with 3 patients (2 male, 1 female, all with birthdates)
SAMPLE_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 3,
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "1",
                "gender": "male",
                "birthDate": "1990-01-01"
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "2",
                "gender": "male",
                "birthDate": "2000-06-15"
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "3",
                "gender": "female",
                "birthDate": "1985-12-20"
            }
        }
    ]
}


# Fixture: Empty bundle with no entries
EMPTY_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 0
}


# Fixture: Bundle with patients missing gender and birthdate fields
INCOMPLETE_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 3,
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "1",
                "gender": "male",
                "birthDate": "1990-01-01"
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "2",
                "gender": "female"
                # Missing birthDate
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "3",
                "birthDate": "2000-06-15"
                # Missing gender
            }
        }
    ]
}


# Fixture: Bundle with malformed birthdate
MALFORMED_BIRTHDATE_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 2,
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "1",
                "gender": "male",
                "birthDate": "1990-01-01"
            }
        },
        {
            "resource": {
                "resourceType": "Patient",
                "id": "2",
                "gender": "female",
                "birthDate": "not-a-valid-date"
            }
        }
    ]
}


def test_gender_distribution_with_known_data():
    """
    Test gender distribution computation with known data.

    Verifies that gender counts are correct when all patients have
    valid gender fields.
    """
    analyzer = FHIRPatientAnalyzer(bundle=SAMPLE_BUNDLE)
    statistics = analyzer.compute_statistics()

    assert statistics["gender_distribution"] == {"male": 2, "female": 1}
    assert statistics["patients_missing_gender"] == 0
    assert statistics["total_patients"] == 3


def test_patients_missing_gender():
    """
    Test counting of patients missing the gender field.

    Verifies that patients without a gender field are correctly counted
    as missing.
    """
    analyzer = FHIRPatientAnalyzer(bundle=INCOMPLETE_BUNDLE)
    statistics = analyzer.compute_statistics()

    assert statistics["patients_missing_gender"] == 1
    assert statistics["gender_distribution"] == {"male": 1, "female": 1}


def test_age_calculation_with_known_birthdates():
    """
    Test age calculation with known birthdates.

    Verifies that min, max, and mean ages are computed correctly from
    known birthdate values.
    """
    analyzer = FHIRPatientAnalyzer(bundle=SAMPLE_BUNDLE)
    statistics = analyzer.compute_statistics()

    # Calculate expected ages based on birthdates in SAMPLE_BUNDLE
    today = datetime.date.today()

    birthdate_1990 = datetime.date(1990, 1, 1)
    age_1990 = (today - birthdate_1990).days // 365

    birthdate_2000 = datetime.date(2000, 6, 15)
    age_2000 = (today - birthdate_2000).days // 365

    birthdate_1985 = datetime.date(1985, 12, 20)
    age_1985 = (today - birthdate_1985).days // 365

    expected_min = min(age_1990, age_2000, age_1985)
    expected_max = max(age_1990, age_2000, age_1985)
    expected_mean = (age_1990 + age_2000 + age_1985) // 3

    age_stats = statistics["age_statistics"]
    assert age_stats is not None
    assert age_stats["min_age"] == expected_min
    assert age_stats["max_age"] == expected_max
    assert age_stats["mean_age"] == expected_mean


def test_patients_with_birthdate_count():
    """
    Test counting of patients with birthdate field.

    Verifies that patients with and without birthdates are counted correctly.
    """
    analyzer = FHIRPatientAnalyzer(bundle=INCOMPLETE_BUNDLE)
    statistics = analyzer.compute_statistics()

    # Two patients have birthDate in INCOMPLETE_BUNDLE
    assert statistics["patients_with_birthdate"] == 2


def test_empty_bundle():
    """
    Test analyzer behavior with an empty bundle.

    Verifies that all statistics are correctly computed as zero or empty
    when no patients are present.
    """
    analyzer = FHIRPatientAnalyzer(bundle=EMPTY_BUNDLE)
    statistics = analyzer.compute_statistics()

    assert statistics["total_patients"] == 0
    assert statistics["gender_distribution"] == {}
    assert statistics["patients_missing_gender"] == 0
    assert statistics["patients_with_birthdate"] == 0
    assert statistics["age_statistics"] is None


def test_malformed_birthdate_handled_gracefully():
    """
    Test that malformed birthdates are handled without raising exceptions.

    Verifies that invalid birthdate strings are skipped in age calculations
    but the patient count is still correct.
    """
    analyzer = FHIRPatientAnalyzer(bundle=MALFORMED_BIRTHDATE_BUNDLE)

    # Should not raise any exception
    statistics = analyzer.compute_statistics()

    # Two patients total, both have birthDate field
    assert statistics["total_patients"] == 2
    assert statistics["patients_with_birthdate"] == 2

    # But only one has a valid birthdate for age calculation
    age_stats = statistics["age_statistics"]
    assert age_stats is not None

    # Calculate expected age for the valid birthdate
    today = datetime.date.today()
    birthdate_1990 = datetime.date(1990, 1, 1)
    expected_age = (today - birthdate_1990).days // 365

    # All age statistics should be based on the single valid birthdate
    assert age_stats["min_age"] == expected_age
    assert age_stats["max_age"] == expected_age
    assert age_stats["mean_age"] == expected_age