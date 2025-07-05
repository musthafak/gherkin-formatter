"""Tests for formatting of complex Gherkin structures like DataTables and DocStrings."""

from __future__ import annotations

from typing import Any

from gherkin_formatter.parser_writer import GherkinFormatter


# Helper function to create a minimal AST for testing docstring formatting.
def create_docstring_step_ast(
    content: str,
    media_type: str | None = None,
) -> dict[str, Any]:
    """Create a minimal AST for a step with a DocString."""
    docstring_node: dict[str, Any] = {"content": content, "delimiter": '"""'}
    if media_type:
        docstring_node["mediaType"] = media_type

    step_node: dict[str, Any] = {
        "keyword": "Given ",
        "text": "a step with a docstring",
        "docString": docstring_node,
    }
    feature_ast: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Test Feature",
            "language": "en",
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Test Scenario",
                        "steps": [step_node],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [],
    }
    return feature_ast


# Helper function to create a minimal AST for testing data table formatting.
def create_datatable_step_ast(rows: list[list[str]]) -> dict[str, Any]:
    """Create a minimal AST for a step with a DataTable."""
    table_header = {"cells": [{"value": cell} for cell in rows[0]]}
    table_body = [
        {"cells": [{"value": cell} for cell in row_data]} for row_data in rows[1:]
    ]
    data_table_node: dict[str, Any] = {"rows": [table_header, *table_body]}
    step_node: dict[str, Any] = {
        "keyword": "Given ",
        "text": "a step with a data table",
        "dataTable": data_table_node,
    }
    feature_ast: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Data Table Test Feature",
            "language": "en",
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Test Scenario",
                        "steps": [step_node],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [],
    }
    return feature_ast


def test_format_json_docstring_without_mediatype_scenario_from_issue_4spaces() -> None:
    """
    Test JSON docstring formatting (no mediaType) with 4-space indent.

    Matches a scenario from an issue.
    """
    json_content: str = '{\n"hello": "world",\n"greeting": "Hello, World!"\n}'
    ast: dict[str, Any] = create_docstring_step_ast(json_content)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=4)

    expected_lines: list[str] = [
        "Feature: Test Feature",
        "",
        "    Scenario: Test Scenario",
        "        Given a step with a docstring",
        '            """',
        "            {",
        '                "hello": "world",',
        '                "greeting": "Hello, World!"',
        "            }",
        '            """',
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_docstring_empty_or_whitespace() -> None:
    """Test formatting of docstrings that are empty or contain only whitespace."""
    empty_doc_ast: dict[str, Any] = create_docstring_step_ast("")
    formatter_empty: GherkinFormatter = GherkinFormatter(empty_doc_ast, tab_width=2)
    expected_empty_lines: list[str] = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        # No extra line for empty content,
        '      """',
    ]
    assert formatter_empty.format().strip() == "\n".join(expected_empty_lines)

    # Whitespace-only docstring
    whitespace_doc_ast: dict[str, Any] = create_docstring_step_ast("   \n  \t  \n ")
    formatter_ws: GherkinFormatter = GherkinFormatter(whitespace_doc_ast, tab_width=2)
    expected_ws_lines_derived_from_diff: list[str] = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        "      " + "   ",
        "      " + "  \t  ",
        "      " + " ",
        '      """',
    ]
    assert formatter_ws.format().strip() == "\n".join(
        expected_ws_lines_derived_from_diff,
    )


def test_format_data_table_empty_or_whitespace_cells() -> None:
    """Test data tables with empty cells or cells containing only whitespace."""
    table_data: list[list[str]] = [
        ["Header1", "Header2", "Header3"],
        ["value1", "", "  "],
        ["", "value2", "value3"],
    ]
    ast: dict[str, Any] = create_datatable_step_ast(table_data)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)
    expected_lines: list[str] = [
        "Feature: Data Table Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a data table",
        "      | Header1 | Header2 | Header3 |",
        "      | value1  |         |         |",
        "      |         | value2  | value3  |",
    ]
    actual_output = formatter.format().strip()
    assert actual_output == "\n".join(expected_lines)


def test_format_data_table_wide_content_and_columns() -> None:
    """Test data table with wide content and many columns for alignment."""
    table_data: list[list[str]] = [
        ["Short", "This is a very very very long header", "Col3", "Col4", "Col5"],
        [
            "Value 1 is quite long too",
            "Tiny",
            "MediumVal",
            "X",
            "Another longish value",
        ],
        [
            "V2",
            "Another very very long cell content here to test padding",
            "S",
            "LongValAbc",
            "Y",
        ],
    ]
    ast: dict[str, Any] = create_datatable_step_ast(table_data)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)
    expected_lines: list[str] = [
        "Feature: Data Table Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a data table",
        "      | Short                     | This is a very very very long header"
        "                     | Col3      | Col4       | Col5                  |",
        "      | Value 1 is quite long too | Tiny                               "
        "                      | MediumVal | X          | Another longish value |",
        "      | V2                        | Another very very long cell content"
        " here to test padding | S         | LongValAbc | Y                     |",
    ]
    actual_output: str = formatter.format().strip()
    assert actual_output == "\n".join(expected_lines)


def test_format_data_table_misaligned_input_pipes() -> None:
    """Test that formatter correctly aligns tables even if input AST implies misaligned pipes."""
    table_data: list[list[str]] = [
        ["Name", "Age"],
        ["Alice", "30"],
        ["Bob", "24"],
        ["Charlie Oscar", "45"],
    ]
    ast: dict[str, Any] = create_datatable_step_ast(table_data)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)
    expected_lines: list[str] = [
        "Feature: Data Table Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a data table",
        "      | Name          | Age |",
        "      | Alice         | 30  |",
        "      | Bob           | 24  |",
        "      | Charlie Oscar | 45  |",
    ]
    actual_output: str = formatter.format().strip()
    assert actual_output == "\n".join(expected_lines)


def test_format_invalid_json_docstring_as_plain_text() -> None:
    """Test that invalid JSON content in a docstring is treated as plain text."""
    invalid_json_content: str = (
        '{\n"key": "value",\n"anotherkey": "anothervalue",trailingcomma\n}'
    )
    ast: dict[str, Any] = create_docstring_step_ast(invalid_json_content)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)

    expected_lines: list[str] = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        '      {"key": "value", "anotherkey": "anothervalue", trailingcomma: null}',
        '      """',
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_simple_string_not_mistaken_as_json() -> None:
    """
    Test that a simple plain string in a docstring is not mistaken for JSON.

    It should be formatted correctly as plain text.
    """
    plain_content: str = "This is just a simple string.\nWith two lines."
    ast: dict[str, Any] = create_docstring_step_ast(plain_content)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)

    expected_lines: list[str] = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        "      This is just a simple string.",
        "      With two lines.",
        '      """',
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_json_docstring_already_formatted_different_indent() -> None:
    """
    Test that a JSON docstring, already formatted but with different indentation.

    It should be re-formatted according to the formatter's settings.
    """
    json_content_already_formatted: str = (
        '{\n    "key": "value",\n        "number": 123\n}'
    )
    ast: dict[str, Any] = create_docstring_step_ast(json_content_already_formatted)
    formatter: GherkinFormatter = GherkinFormatter(ast, tab_width=2)

    expected_lines: list[str] = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        "      {",
        '        "key": "value",',
        '        "number": 123',
        "      }",
        '      """',
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_docstring_plain_text_internal_structure() -> None:
    """Test plain text docstring with leading/trailing blank lines and indentation."""
    plain_content = (
        "\n  Line 1 (indented in source)\n\nLine 3 (no indent in source)\n  "
    )
    ast = create_docstring_step_ast(plain_content)
    formatter = GherkinFormatter(ast, tab_width=2)
    expected_lines = [
        "Feature: Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a docstring",
        '      """',
        "      ",
        "        Line 1 (indented in source)",
        "      ",
        "      Line 3 (no indent in source)",
        "        ",
        '      """',
    ]
    expected_output = "\n".join(expected_lines)
    actual_output = formatter.format().strip()
    assert actual_output == expected_output


def test_format_datatable_cell_with_pipe() -> None:
    """Test formatting a data table where a cell contains a pipe character."""
    table_data = [
        ["Header"],
        ["Value | with pipe"],
    ]
    ast = create_datatable_step_ast(table_data)
    formatter = GherkinFormatter(ast, tab_width=2)
    expected_lines = [
        "Feature: Data Table Test Feature",
        "",
        "  Scenario: Test Scenario",
        "    Given a step with a data table",
        "      | Header            |",
        "      | Value | with pipe |",
    ]
    expected_output = "\n".join(expected_lines)
    actual_output = formatter.format().strip()
    assert actual_output == expected_output
