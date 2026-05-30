from conftest import read_fixture
from pipeline.detect import detect_versions

def test_detect_versions_extracts_goldengate_labels():
    found = detect_versions(read_fixture("docs_index.html"))
    assert found == ["23ai", "21c", "19c"]
