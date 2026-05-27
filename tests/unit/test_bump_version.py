import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bump_version.py"
spec = importlib.util.spec_from_file_location("bump_version", SCRIPT)
bump_version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_version)


def _write_project(root, version):
    (root / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
    (root / "action.yml").write_text(
        "runs:\n"
        "  steps:\n"
        f"    - uses: docker://dnastack/wdl-ci:v{version}\n"
        f"    - uses: docker://dnastack/wdl-ci:v{version}\n"
        "    - uses: actions/checkout@abc123 # v4\n"
    )
    (root / "README.md").write_text(f"- uses: dnastack/wdl-ci@v{version}\n")


def test_bump_updates_version_in_all_three_files(tmp_path, monkeypatch):
    _write_project(tmp_path, "2.1.0")
    monkeypatch.chdir(tmp_path)

    assert bump_version.bump("2.2.0") == 0

    assert 'version = "2.2.0"' in (tmp_path / "pyproject.toml").read_text()
    action = (tmp_path / "action.yml").read_text()
    assert "docker://dnastack/wdl-ci:v2.2.0" in action
    assert "docker://dnastack/wdl-ci:v2.1.0" not in action
    assert "dnastack/wdl-ci@v2.2.0" in (tmp_path / "README.md").read_text()


def test_bump_leaves_third_party_pinned_actions_untouched(tmp_path, monkeypatch):
    _write_project(tmp_path, "2.1.0")
    monkeypatch.chdir(tmp_path)

    assert bump_version.bump("2.2.0") == 0

    assert "actions/checkout@abc123 # v4" in (tmp_path / "action.yml").read_text()


def test_check_returns_zero_when_versions_match(tmp_path, monkeypatch):
    _write_project(tmp_path, "2.1.0")
    monkeypatch.chdir(tmp_path)

    assert bump_version.check() == 0


def test_check_returns_nonzero_when_versions_differ(tmp_path, monkeypatch):
    _write_project(tmp_path, "2.1.0")
    (tmp_path / "README.md").write_text("- uses: dnastack/wdl-ci@v9.9.9\n")
    monkeypatch.chdir(tmp_path)

    assert bump_version.check() == 1


def test_bump_returns_nonzero_when_no_version_reference_found(tmp_path, monkeypatch):
    _write_project(tmp_path, "2.1.0")
    # Replace action.yml with content that has no docker://dnastack/wdl-ci:v reference
    (tmp_path / "action.yml").write_text(
        "runs:\n  steps:\n    - uses: actions/checkout@abc123 # v4\n"
    )
    monkeypatch.chdir(tmp_path)

    assert bump_version.bump("2.2.0") == 1
