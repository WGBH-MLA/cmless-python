import json

import pytest
from typer.testing import CliRunner

from cmless.cli import app

runner = CliRunner()


@pytest.fixture
def content(tmp_path):
    collections = tmp_path / "collections"
    collections.mkdir()
    (collections / "good.md").write_text("# Good\n\n## Summary\nHello\n")
    (collections / "bad.md").write_text("# Bad\n\n## Nonsense\nx\n")

    exhibits = tmp_path / "exhibits"
    (exhibits / "tour").mkdir(parents=True)
    (exhibits / "tour.md").write_text("# Tour\n\n## Summary\nIntro\n")
    (exhibits / "tour" / "second.md").write_text("# Second\n2\n")
    (exhibits / "tour" / "first.md").write_text("# First\n1\n")
    return tmp_path


def test_parse_validates_and_uses_aliases(content):
    result = runner.invoke(
        app, ["parse", str(content / "collections" / "good.md"), "-m", "collection"]
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "Title": "Good",
        "Slug": "good",
        "Summary": "Hello",
    }


def test_parse_reports_invalid_files(tmp_path):
    path = tmp_path / "plain.md"
    path.write_text("no heading here")
    result = runner.invoke(app, ["parse", str(path)])
    assert result.exit_code == 1
    assert "not a valid cmless file" in result.stderr
    assert result.stdout == ""


def test_collections_keeps_stdout_as_json(content):
    result = runner.invoke(app, ["collections", str(content / "collections")])
    assert result.exit_code == 0
    assert [c["Slug"] for c in json.loads(result.stdout)] == ["good"]
    assert "Error parsing bad.md" in result.stderr


def test_exhibits_nest_children_by_page(content):
    result = runner.invoke(app, ["exhibits", str(content / "exhibits"), "--compact"])
    assert result.exit_code == 0
    (tour,) = json.loads(result.stdout)
    assert [child["Slug"] for child in tour["children"]] == ["first", "second"]
    assert "Parsing exhibit directory: tour" in result.stderr


def test_snippet_commands_read_stdin_and_write_files(tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(
        app,
        ["records", "-", "-o", str(out)],
        input="- [A](/catalog/cpb-aacip-12-abc)\n",
    )
    assert result.exit_code == 0
    assert json.loads(out.read_text()) == ["cpb-aacip-12-abc"]
