import json
import pathlib
from jsonschema import Draft7Validator, FormatChecker

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[1] / "schema" / "version-record.schema.json"

class ValidationFailed(Exception):
    pass

def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def validate_record(record):
    validator = Draft7Validator(_load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
    if errors:
        messages = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
        raise ValidationFailed(messages)
