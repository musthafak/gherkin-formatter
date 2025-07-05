"""Tests for the Gherkin parser function `parse_gherkin_file`."""

from pathlib import Path

import pytest

from gherkin_formatter.parser_writer import parse_gherkin_file


def test_parse_gherkin_file_not_found(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test parse_gherkin_file with a non-existent file."""
    non_existent_file = tmp_path / "does_not_exist.feature"
    result = parse_gherkin_file(non_existent_file)
    assert result is None
    captured = capsys.readouterr()
    assert f"Error: File not found at {non_existent_file}" in captured.err


def test_parse_gherkin_file_invalid_syntax(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test parse_gherkin_file with invalid Gherkin syntax."""
    invalid_feature_file = tmp_path / "invalid.feature"
    invalid_feature_file.write_text(
        "This is not valid Gherkin content at all.",
        encoding="utf-8",
    )
    result = parse_gherkin_file(invalid_feature_file)
    assert result is None
    captured = capsys.readouterr()
    assert f"Error parsing file: {invalid_feature_file}" in captured.err
    assert (
        "Parser errors" in captured.err
    )  # Part of CompositeParserException's string representation
