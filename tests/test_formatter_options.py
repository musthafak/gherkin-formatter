"""Tests for GherkinFormatter options (tab_width, use_tabs, alignment, etc.)."""

from typing import Any

from gherkin_formatter.parser_writer import GherkinFormatter


def test_formatter_indent_str_use_tabs() -> None:
    """Test GherkinFormatter.indent_str is correctly set with use_tabs."""
    ast: dict[str, Any] = {"feature": None, "comments": []}
    formatter_tabs: GherkinFormatter = GherkinFormatter(ast, use_tabs=True, tab_width=4)
    assert formatter_tabs.indent_str == "\t"

    formatter_spaces: GherkinFormatter = GherkinFormatter(
        ast,
        use_tabs=False,
        tab_width=3,
    )
    assert formatter_spaces.indent_str == "   "


def test_format_steps_alignment_options() -> None:
    """Test step alignment options directly via GherkinFormatter."""
    steps_ast_nodes = [
        {"keyword": "Given ", "text": "short", "location": {"line": 1}},
        {"keyword": "When ", "text": "a longer keyword step", "location": {"line": 2}},
        {"keyword": "Then ", "text": "medium", "location": {"line": 3}},
    ]
    # Max keyword length: "Given " (6), "When " (5), "Then " (5)
    # Stripped: "Given"(5), "When"(4), "Then"(4). Max is 5.

    # Left alignment (default)
    formatter_left = GherkinFormatter(
        {"feature": None, "comments": []},
        alignment="left",
    )
    formatted_left = formatter_left._format_steps_block(steps_ast_nodes, 0)  # noqa: SLF001
    # Keywords are ljust(max_len).rstrip()
    # "Given".ljust(5).rstrip() -> "Given"
    # "When".ljust(5).rstrip()  -> "When"
    # "Then".ljust(5).rstrip()  -> "Then"
    expected_left = [
        "Given short",
        "When a longer keyword step",
        "Then medium",
    ]
    assert formatted_left == expected_left

    # Right alignment
    formatter_right = GherkinFormatter(
        {"feature": None, "comments": []},
        alignment="right",
    )
    formatted_right = formatter_right._format_steps_block(steps_ast_nodes, 0)  # noqa: SLF001
    # Keywords are rjust(max_len).rstrip()
    # "Given".rjust(5).rstrip() -> "Given"
    # "When".rjust(5).rstrip()  -> " When" (leading space)
    # "Then".rjust(5).rstrip()  -> " Then" (leading space)
    expected_right = [
        "Given short",
        " When a longer keyword step",  # Note the space before When
        " Then medium",  # Note the space before Then
    ]
    assert formatted_right == expected_right


def test_format_multi_line_tags_direct() -> None:
    """Test _format_tags with multi_line_tags=True directly."""
    tags_ast = [{"name": "@tag1"}, {"name": "@tag2"}, {"name": "@long_tag3"}]
    formatter = GherkinFormatter(
        {"feature": None, "comments": []},
        multi_line_tags=True,
    )

    # Test with indent level 0
    formatted_tags_indent0 = formatter._format_tags(tags_ast, 0)  # noqa: SLF001
    expected_tags_indent0 = ["@tag1", "@tag2", "@long_tag3"]
    assert formatted_tags_indent0 == expected_tags_indent0

    # Test with indent level 1 (2 spaces)
    formatter.indent_str = "  "  # Explicitly set for clarity, normally from init
    formatted_tags_indent1 = formatter._format_tags(tags_ast, 1)  # noqa: SLF001
    expected_tags_indent1 = ["  @tag1", "  @tag2", "  @long_tag3"]
    assert formatted_tags_indent1 == expected_tags_indent1
