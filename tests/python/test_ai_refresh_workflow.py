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


def _top_level_keys_after(lines, parent_key):
    parent_index = _line_index(lines, parent_key)
    keys = []

    for line in lines[parent_index + 1:]:
        if not line.strip():
            continue

        indentation = len(line) - len(line.lstrip(" "))
        if indentation == 0:
            break
        if indentation == 2 and line.strip().endswith(":"):
            keys.append(line.strip()[:-1])

    return keys


def _step_lines(lines, step_name):
    step_index = _line_index(lines, f"- name: {step_name}")
    step_lines = []

    for line in lines[step_index + 1:]:
        if line.startswith("      - "):
            break
        step_lines.append(line)

    return step_lines


def _step_names_with_line(lines, expected):
    matching_step_names = []
    current_step_name = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- name: "):
            current_step_name = stripped.removeprefix("- name: ")
        elif stripped == expected and current_step_name:
            matching_step_names.append(current_step_name)

    return matching_step_names


def test_ai_refresh_workflow_is_manual_only(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()

    assert "name: AI Assist Oracle Release Delta data" in workflow
    assert _top_level_keys_after(lines, "on:") == ["workflow_dispatch"]


def test_ai_refresh_workflow_uses_required_dependencies_permissions_and_secret(repo_root):
    workflow = (repo_root / ".github" / "workflows" / "ai-refresh-data.yml").read_text()
    lines = workflow.splitlines()
    lines_before_steps = lines[:_line_index(lines, "steps:")]

    assert _contains_line(lines, "python -m pip install -r pipeline/requirements.txt")
    assert _contains_line(lines, "python -m venv --system-site-packages .venv")
    assert _contains_line(lines, "test -n \"$OPENAI_API_KEY\"")
    assert _contains_line(lines, "contents: write")
    assert _contains_line(lines, "pull-requests: write")
    assert not _contains_line(lines_before_steps, "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}")
    assert _contains_line(
        _step_lines(lines, "Verify OpenAI API key"),
        "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}",
    )
    assert _contains_line(
        _step_lines(lines, "Run AI-assisted source refresh"),
        "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}",
    )
    assert _step_names_with_line(
        lines,
        "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}",
    ) == [
        "Verify OpenAI API key",
        "Run AI-assisted source refresh",
    ]


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
