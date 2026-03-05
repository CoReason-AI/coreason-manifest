from coreason_manifest.spec.clinical import ObservationRecord


def test_clinical_observation_record() -> None:
    p = ObservationRecord(patient_id="123", date="2025-01-01", semantic_value="healthy")
    assert p.patient_id == "123"
