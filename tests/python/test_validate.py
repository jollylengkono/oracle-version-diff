import json
import pytest
from pipeline.validate import validate_record, ValidationFailed

def _good_record():
    return {
        "product": "oracle-goldengate",
        "version": "23ai",
        "release_label": "Oracle GoldenGate 23ai",
        "record_type": "release",
        "released": "2026-01-01",
        "last_updated": "2026-05-30",
        "sections": {
            "certification": [{"category": "DB", "value": "23ai", "source_url": "https://docs.oracle.com/x"}],
            "whats_new": [], "behavior_changes": [], "deprecated": [], "desupported": []
        },
    }

def test_valid_record_passes():
    validate_record(_good_record())  # must not raise

def test_missing_section_fails():
    rec = _good_record()
    del rec["sections"]["deprecated"]
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_bad_source_url_fails():
    rec = _good_record()
    rec["sections"]["certification"][0]["source_url"] = "not-a-url"
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_bad_released_date_fails():
    rec = _good_record()
    rec["released"] = "January 2026"
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_missing_record_type_fails():
    rec = _good_record()
    del rec["record_type"]
    with pytest.raises(ValidationFailed):
        validate_record(rec)

def test_bad_record_type_fails():
    rec = _good_record()
    rec["record_type"] = "snapshot"
    with pytest.raises(ValidationFailed):
        validate_record(rec)
