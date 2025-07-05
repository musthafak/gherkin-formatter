"""Tests for Gherkin comment formatting."""

from typing import Any

from gherkin_formatter.parser_writer import GherkinFormatter


def test_format_feature_with_only_comments() -> None:
    """Test formatting a feature file that contains only comments."""
    feature_ast: dict[str, Any] = {
        "feature": None,  # No feature node if only comments
        "comments": [
            {
                "text": "# This is a comment line 1",
                "location": {"line": 1, "column": 1},
            },
            {
                "text": "# This is a comment line 2",
                "location": {"line": 2, "column": 1},
            },
        ],
    }
    formatter: GherkinFormatter = GherkinFormatter(feature_ast, tab_width=2)
    expected_lines: list[str] = [
        "# This is a comment line 1",
        "# This is a comment line 2",
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_multiple_consecutive_comments() -> None:
    """
    Test formatting of multiple comments on consecutive lines.

    Covers comments before feature, scenario, and step.
    """
    feature_ast: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Multi-comment Test",
            "language": "en",
            "location": {"line": 4, "column": 1},
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Scenario with multi-comments",
                        "location": {"line": 8, "column": 3},
                        "steps": [
                            {
                                "keyword": "Given ",
                                "text": "a step",
                                "location": {"line": 12, "column": 5},
                            },
                        ],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [
            {
                "text": "# Comment 1 before feature",
                "location": {"line": 1, "column": 1},
            },
            {
                "text": "# Comment 2 before feature",
                "location": {"line": 2, "column": 1},
            },
            {
                "text": "# Comment 3 before scenario",
                "location": {"line": 5, "column": 3},
            },
            {
                "text": "# Comment 4 before scenario",
                "location": {"line": 6, "column": 3},
            },
            {"text": "# Comment 5 before step", "location": {"line": 9, "column": 5}},
            {"text": "# Comment 6 before step", "location": {"line": 10, "column": 5}},
        ],
    }
    formatter: GherkinFormatter = GherkinFormatter(feature_ast, tab_width=2)
    expected_lines: list[str] = [
        "# Comment 1 before feature",
        "# Comment 2 before feature",
        "Feature: Multi-comment Test",
        "",
        "  # Comment 3 before scenario",
        "  # Comment 4 before scenario",
        "  Scenario: Scenario with multi-comments",
        "    # Comment 5 before step",
        "    # Comment 6 before step",
        "    Given a step",
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_comments_at_end_of_scenario_and_file() -> None:
    """Test formatting of comments at the end of a scenario and at the end of the file."""
    # Simpler test for end-of-file comments first:
    feature_ast_eof_only: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "EOF Comments",
            "language": "en",
            "location": {"line": 1, "column": 1},
            "children": [],
            "tags": [],
        },
        "comments": [
            {"text": "# EOF Comment 1", "location": {"line": 2, "column": 1}},
            {"text": "# EOF Comment 2", "location": {"line": 3, "column": 1}},
        ],
    }
    formatter_eof: GherkinFormatter = GherkinFormatter(
        feature_ast_eof_only,
        tab_width=2,
    )
    expected_eof_lines: list[str] = [
        "Feature: EOF Comments",
        "",
        "# EOF Comment 1",
        "# EOF Comment 2",
    ]
    expected_eof_output: str = "\n".join(expected_eof_lines)
    actual_eof_output: str = formatter_eof.format().strip()
    assert actual_eof_output == expected_eof_output

    # Test for comment after last step in a scenario
    feature_ast_scenario_end: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Scenario End Comment",
            "language": "en",
            "location": {"line": 1, "column": 1},
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Test Senario",
                        "location": {"line": 2, "column": 3},
                        "steps": [
                            {
                                "keyword": "Given ",
                                "text": "a final step",
                                "location": {"line": 3, "column": 5},
                            },
                        ],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [
            {"text": "# Comment after last step", "location": {"line": 4, "column": 5}},
            {
                "text": "# Comment after scenario block",
                "location": {"line": 5, "column": 1},
            },
        ],
    }
    formatter_scenario_end: GherkinFormatter = GherkinFormatter(
        feature_ast_scenario_end,
        tab_width=2,
    )
    expected_scenario_end_lines: list[str] = [
        "Feature: Scenario End Comment",
        "",
        "  Scenario: Test Senario",
        "    Given a final step",
        "",
        "# Comment after last step",
        "# Comment after scenario block",
    ]
    expected_scenario_end_output: str = "\n".join(expected_scenario_end_lines)
    actual_scenario_end_output: str = formatter_scenario_end.format().strip()
    assert actual_scenario_end_output == expected_scenario_end_output


def test_format_fully_commented_out_scenario() -> None:
    """Test how a fully commented-out scenario is handled."""
    feature_ast: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Commented Out Scenario Test",
            "language": "en",
            "location": {"line": 1, "column": 1},
            "children": [],
            "tags": [],
        },
        "comments": [
            {
                "text": "# Scenario: Commented out scenario",
                "location": {"line": 3, "column": 3},
            },
            {
                "text": "#   Given a commented step",
                "location": {"line": 4, "column": 5},
            },
            {
                "text": "#   When another commented step",
                "location": {"line": 5, "column": 5},
            },
        ],
    }
    formatter: GherkinFormatter = GherkinFormatter(feature_ast, tab_width=2)
    expected_lines: list[str] = [
        "Feature: Commented Out Scenario Test",
        "",
        "# Scenario: Commented out scenario",
        "#   Given a commented step",
        "#   When another commented step",
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output

    # More realistic: commented scenario followed by a real one
    feature_ast_followed_by_real: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Test",
            "language": "en",
            "location": {"line": 1, "column": 1},
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Real Scenario",
                        "location": {"line": 7, "column": 3},
                        "steps": [
                            {
                                "keyword": "Given ",
                                "text": "real step",
                                "location": {"line": 8, "column": 5},
                            },
                        ],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [
            {
                "text": "# Scenario: Commented out scenario",
                "location": {"line": 3, "column": 3},
            },
            {
                "text": "#   Given a commented step",
                "location": {"line": 4, "column": 3},
            },
            {
                "text": "#   When another commented step",
                "location": {"line": 5, "column": 3},
            },
        ],
    }
    formatter_2: GherkinFormatter = GherkinFormatter(
        feature_ast_followed_by_real,
        tab_width=2,
    )
    expected_lines_2: list[str] = [
        "Feature: Test",
        "",
        "  # Scenario: Commented out scenario",
        "  #   Given a commented step",
        "  #   When another commented step",
        "  Scenario: Real Scenario",
        "    Given real step",
    ]
    expected_output_2: str = "\n".join(expected_lines_2)
    actual_output_2: str = formatter_2.format().strip()
    assert actual_output_2 == expected_output_2


def test_comments_interspersed_with_tags() -> None:
    """Test comments appearing before, between, and after tags for a scenario."""
    feature_ast_final: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Tag Comment Test",
            "language": "en",
            "location": {"line": 3, "column": 1},
            "tags": [{"name": "@feature_tag", "location": {"line": 2, "column": 1}}],
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Tagged Scenario",
                        "location": {"line": 8, "column": 3},
                        "tags": [
                            {"name": "@tag1", "location": {"line": 5, "column": 3}},
                            {"name": "@tag2", "location": {"line": 7, "column": 3}},
                        ],
                        "steps": [
                            {
                                "keyword": "Given ",
                                "text": "a step",
                                "location": {"line": 9, "column": 5},
                            },
                        ],
                    },
                },
            ],
        },
        "comments": [
            {"text": "# C0 (before feature tag)", "location": {"line": 1, "column": 1}},
            {
                "text": "# C1 (before scenario tag1)",
                "location": {"line": 4, "column": 3},
            },
            {
                "text": "# C2 (between scenario tags)",
                "location": {"line": 6, "column": 3},
            },
        ],
    }

    formatter: GherkinFormatter = GherkinFormatter(feature_ast_final, tab_width=2)
    expected_lines: list[str] = [
        "# C0 (before feature tag)",
        "@feature_tag",
        "Feature: Tag Comment Test",
        "",
        "  # C1 (before scenario tag1)",
        "  # C2 (between scenario tags)",
        "  @tag1 @tag2",
        "  Scenario: Tagged Scenario",
        "    Given a step",
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output


def test_format_feature_with_comments() -> None:
    """Test formatting of a feature file with comments."""
    feature_ast: dict[str, Any] = {
        "feature": {
            "keyword": "Feature",
            "name": "Comments Test",
            "language": "en",
            "location": {"line": 3, "column": 1},
            "children": [
                {
                    "scenario": {
                        "keyword": "Scenario",
                        "name": "Scenario with comments",
                        "location": {"line": 5, "column": 3},
                        "steps": [
                            {
                                "keyword": "Given ",
                                "text": "a step",
                                "location": {"line": 7, "column": 5},
                            },
                        ],
                        "tags": [],
                    },
                },
            ],
            "tags": [],
        },
        "comments": [
            {"text": "# Comment before feature", "location": {"line": 1, "column": 1}},
            {"text": "# Comment before scenario", "location": {"line": 4, "column": 3}},
            {"text": "# Comment before step", "location": {"line": 6, "column": 5}},
        ],
    }
    formatter: GherkinFormatter = GherkinFormatter(feature_ast, tab_width=2)
    expected_lines: list[str] = [
        "# Comment before feature",
        "Feature: Comments Test",
        "",
        "  # Comment before scenario",
        "  Scenario: Scenario with comments",
        "    # Comment before step",
        "    Given a step",
    ]
    expected_output: str = "\n".join(expected_lines)
    actual_output: str = formatter.format().strip()
    assert actual_output == expected_output
