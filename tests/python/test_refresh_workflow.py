def _line_index(lines, expected):
    matching_indexes = [
        index
        for index, line in enumerate(lines)
        if line.strip() == expected
    ]
    assert matching_indexes, f"Expected workflow line not found: {expected}"
    return matching_indexes[0]


def _contains_line(lines, expected):
    return any(line.strip() == expected for line in lines)


def _contains_line_starting_with(lines, expected):
    return any(line.strip().startswith(expected) for line in lines)


def test_refresh_workflow_uses_all_product_copy(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert "name: Refresh Oracle Release Delta data" in workflow
    assert "data: refresh Oracle Release Delta data" in workflow
    assert "Data refresh: Oracle Release Delta" in workflow
    assert "GoldenGate comparison" not in workflow
    assert _contains_line_starting_with(lines, "workflow_dispatch:")
    assert any(line.strip().startswith("- cron:") and "0 6 * * 1" in line for line in lines)
    assert _contains_line(lines, "contents: write")
    assert _contains_line(lines, "pull-requests: write")

    test_index = _line_index(lines, "run: .venv/bin/python -m pytest tests/python/ -q")
    build_index = _line_index(lines, "run: python -m pipeline.build")
    assert test_index < build_index

    assert _contains_line(lines, "uses: peter-evans/create-pull-request@v6")
    assert _contains_line(lines, "branch: data/refresh")
    assert _contains_line(lines, "labels: data-refresh")


def test_refresh_workflow_does_not_commit_virtualenv(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "refresh-data.yml").read_text()
    gitignore = (repo_root / ".gitignore").read_text().splitlines()

    assert ".venv/" in gitignore
    assert "add-paths: |" in workflow
    assert "data/" in workflow
    assert ".venv" not in workflow.split("add-paths: |", 1)[1]


def test_docs_describe_all_product_periodic_refresh(repo_root):
    readme = (repo_root / "README.md").read_text()
    handover = (repo_root / "docs" / "HANDOVER.md").read_text()

    assert "all registered products" in readme
    assert "Database and WebLogic" in readme
    assert "pipeline/curated_sources/oracle-database.json" in readme
    assert "pipeline/curated_sources/oracle-weblogic-server.json" in readme
    assert "seed records live under" not in readme
    assert "all registered products" in handover
    assert "not yet crawler-backed" not in readme
