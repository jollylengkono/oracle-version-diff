import json
from conftest import read_fixture
from pipeline.build import build_record, write_outputs

def fake_fetch_factory():
    pages = {
        "cert": read_fixture("certification.html"),
        "feat": read_fixture("whats_new.html"),
    }
    def fetch(url):
        return pages["cert"] if "cert" in url else pages["feat"]
    return fetch

def _sources_one():
    return {
        "23ai": {
            "release_label": "Oracle GoldenGate 23ai",
            "urls": {
                "certification": "https://docs.oracle.com/cert",
                "whats_new": "https://docs.oracle.com/feat",
                "behavior_changes": "https://docs.oracle.com/feat",
                "deprecated": "https://docs.oracle.com/feat",
                "desupported": "https://docs.oracle.com/feat",
            },
        }
    }

def test_build_record_produces_valid_structure():
    rec = build_record("23ai", _sources_one()["23ai"], fetch=fake_fetch_factory(), today="2026-05-30")
    assert rec["product"] == "oracle-goldengate"
    assert rec["version"] == "23ai"
    assert rec["last_updated"] == "2026-05-30"
    assert len(rec["sections"]["certification"]) == 2
    assert rec["sections"]["whats_new"][0]["title"] == "AI vector replication"

def test_write_outputs_writes_records_and_index(tmp_path):
    sources = _sources_one()
    write_outputs(sources, ["23ai"], fetch=fake_fetch_factory(), data_dir=tmp_path, today="2026-05-30")
    rec_file = tmp_path / "oracle-goldengate" / "23ai.json"
    index_file = tmp_path / "index.json"
    assert rec_file.exists()
    index = json.loads(index_file.read_text())
    versions = index["products"][0]["versions"]
    assert versions[0]["version"] == "23ai"
    assert versions[0]["order"] == 0
    assert versions[0]["file"] == "oracle-goldengate/23ai.json"
