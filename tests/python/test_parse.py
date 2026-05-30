from conftest import read_fixture
from pipeline.parse import parse_feature_list, parse_certification

SRC = "https://docs.oracle.com/x"

def test_parse_feature_list_extracts_title_and_description():
    items = parse_feature_list(read_fixture("whats_new.html"), source_url=SRC)
    assert items[0] == {
        "title": "AI vector replication",
        "description": "Support for replicating vector data types.",
        "source_url": SRC,
    }
    assert len(items) == 2

def test_parse_certification_extracts_category_value_rows():
    items = parse_certification(read_fixture("certification.html"), source_url=SRC)
    assert {"category": "Oracle Database", "value": "Oracle Database 23ai", "source_url": SRC} in items
    assert len(items) == 2
