"""Tests for the Gherkin Formatter CLI."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator  # TC003

    # Type alias for the feature file factory
    FeatureFileFactory = Callable[[str, str, str | None], Path]


@pytest.fixture
def feature_file_factory() -> Iterator[FeatureFileFactory]:
    """
    Pytest fixture to create temporary .feature files for CLI testing.

    Yields a factory function that can be called to create a feature file.
    The factory takes content, name, and an optional base_dir.
    Cleans up all created temporary directories after the test.

    :yield: A factory function for creating feature files.
    :rtype: Iterator[FeatureFileFactory]
    """
    created_dirs: list[str] = []

    def _create_file(
        content: str,
        name: str = "test.feature",
        base_dir: str | None = None,
    ) -> Path:
        """
        Inner factory function to create a single temporary .feature file.

        :param content: The string content to write to the file.
        :type content: str
        :param name: The desired name for the feature file (default: "test.feature").
        :type name: str
        :param base_dir: Optional. If provided, the file is created in this directory.
                         If None, a new temporary directory is created.
        :type base_dir: Optional[str]
        :return: Path object to the created temporary file.
        :rtype: Path
        """
        temp_dir_path: Path
        if base_dir:
            temp_dir_path = Path(base_dir)
        else:
            # Create a unique temporary directory for each call if no base_dir
            temp_dir_str = tempfile.mkdtemp()
            created_dirs.append(temp_dir_str)
            temp_dir_path = Path(temp_dir_str)

        file_path: Path = temp_dir_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    yield _create_file

    for d_str in created_dirs:
        shutil.rmtree(d_str)


def test_cli_help_output() -> None:
    """Test that the CLI runs and shows help output with expected arguments."""
    result: subprocess.CompletedProcess = subprocess.run(
        ["python", "-m", "gherkin_formatter.formatter", "--help"],
        capture_output=True,
        text=True,
        check=False,  # Do not check for non-zero exit, assert manually
    )
    assert result.returncode == 0, f"CLI --help failed: {result.stderr}"
    assert "formatter.py" in result.stdout
    assert "usage:" in result.stdout
    assert "FILES_OR_DIRECTORIES" in result.stdout
    assert "--tab-width" in result.stdout
    assert "--use-tabs" in result.stdout
    assert "--alignment" in result.stdout
    assert "--multi-line-tags" in result.stdout
    assert "--version" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--check" in result.stdout


def run_cli_with_content(
    cli_args: list[str],
    input_content: str,
    temp_dir: Path,
    filename: str = "test.feature",
) -> subprocess.CompletedProcess:
    """
    Run the gherkin-formatter CLI with specified arguments and input content.

    Creates a temporary feature file in `temp_dir`, runs the formatter,
    and returns the result.

    :param cli_args: List of command-line arguments for the formatter.
    :type cli_args: list[str]
    :param input_content: The Gherkin content to write to the temporary file.
    :type input_content: str
    :param temp_dir: The Path object for the temporary directory (from pytest fixture).
    :type temp_dir: Path
    :param filename: The name for the temporary feature file (default: "test.feature").
    :type filename: str
    :return: The CompletedProcess object from subprocess.run.
    :rtype: subprocess.CompletedProcess
    """
    feature_file: Path = temp_dir / filename
    feature_file.write_text(input_content, encoding="utf-8")

    cmd_base: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        str(feature_file),
    ]
    cmd: list[str] = [*cmd_base, *cli_args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_formats_single_file_default_tab_width(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """
    Test formatting a single file with default CLI tab-width (2 spaces).

    :param feature_file_factory: Fixture to create temporary feature files.
    :type feature_file_factory: FeatureFileFactory
    """
    raw_content: str = "Feature: Test\nScenario: A\nGiven B"
    expected_formatted_content: str = "Feature: Test\n\n  Scenario: A\n    Given B\n"

    # Call factory with positional arguments: content, name, base_dir
    feature_file: Path = feature_file_factory(
        raw_content,
        "format_me_default.feature",
        None,
    )

    result: subprocess.CompletedProcess = subprocess.run(
        ["python", "-m", "gherkin_formatter.formatter", str(feature_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    assert "Reformatted" in result.stdout
    assert str(feature_file) in result.stdout

    formatted_content_on_disk: str = feature_file.read_text(encoding="utf-8")
    assert formatted_content_on_disk == expected_formatted_content


def test_cli_check_mode_formatted_file_default_tab_width(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """
    Test --check mode on an already well-formatted file (default tab-width 2).

    :param feature_file_factory: Fixture to create temporary feature files.
    :type feature_file_factory: FeatureFileFactory
    """
    formatted_content: str = "Feature: Test\n\n  Scenario: A\n    Given B\n"
    # Call factory with positional arguments
    feature_file: Path = feature_file_factory(
        formatted_content,
        "check_formatted_default.feature",
        None,
    )

    result: subprocess.CompletedProcess = subprocess.run(
        ["python", "-m", "gherkin_formatter.formatter", "--check", str(feature_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "is already well-formatted" in result.stdout
    assert str(feature_file) in result.stdout


def test_cli_check_mode_unformatted_file_default_tab_width(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """
    Test --check mode on a file that needs formatting (default tab-width 2).

    :param feature_file_factory: Fixture to create temporary feature files.
    :type feature_file_factory: FeatureFileFactory
    """
    raw_content: str = "Feature: Test\nScenario: A\nGiven B"
    # Call factory with positional arguments
    feature_file: Path = feature_file_factory(
        raw_content,
        "check_unformatted_default.feature",
        None,
    )

    result: subprocess.CompletedProcess = subprocess.run(
        ["python", "-m", "gherkin_formatter.formatter", "--check", str(feature_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "needs formatting" in result.stdout
    assert str(feature_file) in result.stdout
    assert "file(s) that need formatting" in result.stderr


def test_cli_non_existent_file() -> None:
    """Test CLI behavior when a non-existent file is provided."""
    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        "non_existent_file.feature",
    ]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    # _discover_feature_files prints to stderr and continues.
    # If no files are found at all, it prints "No .feature files found" and exits 0.
    assert result.returncode == 0
    captured = result.stderr  # capfd does not capture subprocess stderr
    assert (
        "Warning: Path 'non_existent_file.feature' does not exist. Skipping."
        in captured
    )
    assert "No .feature files found to process." in result.stdout


def test_cli_non_feature_file(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """Test CLI behavior when a non-.feature file is provided."""
    non_feature_file: Path = feature_file_factory(
        "This is not a feature file.",
        "test.txt",
        None,
    )
    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        str(non_feature_file),
    ]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0
    captured = result.stderr
    assert (
        f"Warning: File '{non_feature_file}' is not a .feature file. Skipping."
        in captured
    )
    assert "No .feature files found to process." in result.stdout


def test_cli_directory_with_mixed_files(
    feature_file_factory: FeatureFileFactory,
    tmp_path: Path,
) -> None:
    """Test CLI processing of a directory with mixed .feature and non-.feature files."""
    feature_content_raw = "Feature: Test\nScenario: A\nGiven B"
    expected_formatted_content = "Feature: Test\n\n  Scenario: A\n    Given B\n"
    feature_file_factory(feature_content_raw, "actual.feature", str(tmp_path))
    feature_file_factory("This is a text file", "other.txt", str(tmp_path))

    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        str(tmp_path),
    ]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0
    assert f"Processing {tmp_path / 'actual.feature'}..." in result.stdout
    assert "Reformatted" in result.stdout
    assert "other.txt" not in result.stdout  # Should not attempt to process

    formatted_on_disk = (tmp_path / "actual.feature").read_text(encoding="utf-8")
    assert formatted_on_disk == expected_formatted_content


def test_cli_error_exit_code_for_parsing_error(
    feature_file_factory: FeatureFileFactory,
    tmp_path: Path,
) -> None:
    """Test CLI exits with 123 if a file has a parsing error."""
    valid_content = "Feature: Valid\nScenario: S\nGiven G"
    invalid_content = "This is not valid Gherkin content at all."  # Should fail parsing

    feature_file_factory(valid_content, "valid.feature", str(tmp_path))
    parsing_error_file = feature_file_factory(
        invalid_content,
        "invalid.feature",
        str(tmp_path),
    )

    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        str(tmp_path / "valid.feature"),
        str(parsing_error_file),
    ]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 123
    assert f"Error parsing file: {parsing_error_file}" in result.stderr
    assert (
        "Processing completed with file-specific or internal errors." in result.stderr
    )
    # Check that the valid file was still processed if it came first
    # (or if processing continues). Current behavior: formatter.py processes
    # file by file, an error in one marks overall error.
    assert f"Processing {tmp_path / 'valid.feature'}..." in result.stdout


def test_cli_check_and_dry_run_interaction(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """Test that --check takes precedence if both --check and --dry-run are used."""
    raw_content: str = "Feature: Test\nScenario: A\nGiven B"
    feature_file: Path = feature_file_factory(
        raw_content,
        "check_dry_interaction.feature",
        None,
    )

    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        "--check",
        "--dry-run",
        str(feature_file),
    ]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 1  # Needs formatting
    assert "needs formatting" in result.stdout
    assert "Would reformat" not in result.stdout  # --dry-run output should not appear
    assert "--- Formatted content (dry-run) ---" not in result.stdout


def test_cli_dry_run_mode_unformatted_file_default_tab_width(
    feature_file_factory: FeatureFileFactory,
) -> None:
    """
    Test --dry-run mode on a file that needs formatting (default tab-width 2).

    :param feature_file_factory: Fixture to create temporary feature files.
    :type feature_file_factory: FeatureFileFactory
    """
    raw_content: str = "Feature: Test\nScenario: A\nGiven B"
    # Call factory with positional arguments
    feature_file: Path = feature_file_factory(
        raw_content,
        "dry_run_unformatted_default.feature",
        None,
    )
    original_content_on_disk: str = feature_file.read_text(encoding="utf-8")
    expected_dry_run_output_part: str = "Feature: Test\n\n  Scenario: A\n    Given B"

    result: subprocess.CompletedProcess = subprocess.run(
        ["python", "-m", "gherkin_formatter.formatter", "--dry-run", str(feature_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Would reformat" in result.stdout
    assert str(feature_file) in result.stdout
    assert "--- Formatted content (dry-run) ---" in result.stdout
    assert feature_file.read_text(encoding="utf-8") == original_content_on_disk
    assert expected_dry_run_output_part in result.stdout


def test_cli_custom_tab_width(tmp_path: Path) -> None:
    """
    Test CLI formatting with a custom --tab-width value.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    raw_content: str = "Feature: Test\nScenario: A\nGiven B"
    expected_formatted_content: str = (
        "Feature: Test\n\n    Scenario: A\n        Given B\n"
    )

    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--tab-width", "4"],
        raw_content,
        tmp_path,
    )

    assert result.returncode == 0
    assert "Reformatted" in result.stdout
    assert "test.feature" in result.stdout

    formatted_content_on_disk: str = (tmp_path / "test.feature").read_text(
        encoding="utf-8",
    )
    assert formatted_content_on_disk == expected_formatted_content


def test_cli_version() -> None:
    """Test the --version flag."""
    cmd: list[str] = ["python", "-m", "gherkin_formatter.formatter", "--version"]
    result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0
    assert "formatter.py" in result.stdout
    # A basic check for version format like X.Y.Z
    # assert __version__ in result.stdout # More robust check
    assert "." in result.stdout


def test_cli_alignment_left(tmp_path: Path) -> None:
    """
    Test --alignment left (default).

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = """Feature: Alignment Test
  Scenario: Left aligned keywords
    Given this is a short step
    When this is a much much much longer step keyword
    Then this step is medium
"""
    # Expected output based on formatter logic (default tab-width 2)
    # Keywords: Given (5), When (4), Then (4). Max is 5.
    # The formatter logic for `_format_step` is:
    # `f"{aligned_keyword.rstrip()} {text}"`
    # If `aligned_keyword` is `keyword.ljust(max_keyword_len)`:
    # "Given".ljust(5) -> "Given" -> rstrip() -> "Given"
    # "When".ljust(5)  -> "When " -> rstrip() -> "When"
    # "Then".ljust(5)  -> "Then " -> rstrip() -> "Then"
    # This means all keywords will be left-aligned without extra padding
    expected_output: str = """Feature: Alignment Test

  Scenario: Left aligned keywords
    Given this is a short step
    When this is a much much much longer step keyword
    Then this step is medium
"""
    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--alignment", "left"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content.strip() == expected_output.strip()


def test_cli_alignment_right(tmp_path: Path) -> None:
    """
    Test --alignment right.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = """Feature: Alignment Test
  Scenario: Right aligned keywords
    Given this is a short step
    When this is a much much much longer step keyword
    Then this step is medium
"""
    # Keywords: "Given", "When", "Then". Lengths: 5, 4, 4. Max = 5.
    # "Given".rjust(5).rstrip() -> "Given"
    # " When".rjust(5).rstrip() -> " When"
    # " Then".rjust(5).rstrip() -> " Then"
    expected_output: str = """Feature: Alignment Test

  Scenario: Right aligned keywords
    Given this is a short step
     When this is a much much much longer step keyword
     Then this step is medium
"""
    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--alignment", "right"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content.strip() == expected_output.strip()


def test_cli_tags_single_line(tmp_path: Path) -> None:
    """
    Test default single-line tag formatting.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = "@tag1 @tag2\nFeature: Tag Test"
    expected_output: str = "@tag1 @tag2\nFeature: Tag Test\n"

    result: subprocess.CompletedProcess = run_cli_with_content(
        [],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content == expected_output


def test_cli_tags_multi_line(tmp_path: Path) -> None:
    """
    Test --multi-line-tags formatting.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = "@tag1 @tag2\nFeature: Tag Test"
    expected_output: str = "@tag1\n@tag2\nFeature: Tag Test\n"

    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--multi-line-tags"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content == expected_output


def test_cli_use_tabs(tmp_path: Path) -> None:
    """
    Test --use-tabs for indentation.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = (
        "Feature: Tab Test\n  Scenario: Test with tabs\n    Given a step"
    )
    expected_output: str = (
        "Feature: Tab Test\n\n\tScenario: Test with tabs\n\t\tGiven a step\n"
    )

    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--use-tabs"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content == expected_output


def test_cli_check_mode_formatted_file_custom_options(tmp_path: Path) -> None:
    """
    Test --check on a file already formatted with specific custom options.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    # This content is already formatted with tabs and right alignment
    input_gherkin: str = (
        "Feature: Test\n\n\tScenario: Test\n\t\tGiven short\n\t\t When longer\n"
    )
    feature_filename: str = "custom_formatted.feature"
    feature_file_path: Path = tmp_path / feature_filename

    # First, format the file with custom options to ensure it's "perfect"
    initial_format_result: subprocess.CompletedProcess = run_cli_with_content(
        ["--use-tabs", "--alignment", "right"],
        input_gherkin,
        tmp_path,
        filename=feature_filename,
    )
    assert initial_format_result.returncode == 0, (
        "Initial formatting run failed:\nStdout:"
        f" {initial_format_result.stdout}\nStderr: {initial_format_result.stderr}"
    )

    # Now, check this custom-formatted file
    cmd: list[str] = [
        "python",
        "-m",
        "gherkin_formatter.formatter",
        "--check",
        "--use-tabs",
        "--alignment",
        "right",
        str(feature_file_path),
    ]
    check_result: subprocess.CompletedProcess = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert check_result.returncode == 0, (
        f"Check mode failed. Stderr: {check_result.stderr}\nStdout:"
        f" {check_result.stdout}"
    )
    assert "is already well-formatted" in check_result.stdout


def test_cli_check_mode_needs_reformatting_custom_options(tmp_path: Path) -> None:
    """
    Test --check on a file that needs reformatting against custom options.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = """Feature: Test
  Scenario: Test
    Given short
    When longer
"""  # Default spaces, left alignment

    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--check", "--use-tabs", "--alignment", "right"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 1, (
        "CLI should indicate reformatting needed.\n"
        f"Stdout: {result.stdout}\nStderr: {result.stderr}"
    )
    assert "needs formatting" in result.stdout
    assert "file(s) that need formatting" in result.stderr


def test_cli_skip_docstrings_option(tmp_path: Path) -> None:
    """
    Test --skip-docstrings option preserves docstring content as-is.

    :param tmp_path: Pytest fixture for temporary path.
    :type tmp_path: Path
    """
    input_gherkin: str = '''
Feature: DocString Test

  Scenario: Test with docstring
    Given a step with a docstring
      """
      {

          "a": "This should not be formatted"


      }
      """
    When another step
'''.strip()

    result: subprocess.CompletedProcess = run_cli_with_content(
        ["--skip-docstrings"],
        input_gherkin,
        tmp_path,
    )
    assert result.returncode == 0
    formatted_content: str = (tmp_path / "test.feature").read_text(encoding="utf-8")
    assert formatted_content.strip() == input_gherkin.strip()
