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


def test_ai_refresh_workflow_is_manual_only(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert "name: AI Assist Oracle Release Delta data" in workflow
    assert _contains_line_starting_with(lines, "workflow_dispatch:")
    assert not _contains_line_starting_with(lines, "schedule:")


def test_ai_refresh_workflow_uses_required_permissions_and_secret(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert _contains_line(lines, "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}")
    assert _contains_line(lines, "contents: write")
    assert _contains_line(lines, "pull-requests: write")


def test_ai_refresh_runs_before_build_and_tests(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    ai_refresh_index = _line_index(
        lines,
        "run: .venv/bin/python -m pipeline.ai_refresh --products oracle-database oracle-weblogic-server",
    )
    build_index = _line_index(lines, "run: .venv/bin/python -m pipeline.build")
    python_test_index = _line_index(lines, "run: .venv/bin/python -m pytest tests/python/ -q")
    js_test_index = _line_index(lines, "run: npm test")

    assert ai_refresh_index < build_index
    assert ai_refresh_index < python_test_index
    assert ai_refresh_index < js_test_index


def test_ai_refresh_workflow_opens_review_pull_request(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert _contains_line(lines, "uses: peter-evans/create-pull-request@v6")
    assert _contains_line(lines, 'commit-message: "data: AI-assisted Oracle Release Delta refresh"')
    assert _contains_line(lines, "branch: data/ai-refresh")
    assert _contains_line(lines, 'title: "AI data refresh: Oracle Release Delta"')
    assert _contains_line(lines, "labels: data-refresh")
