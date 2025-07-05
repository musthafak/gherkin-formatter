"""Gherkin parsing and formatting."""

from __future__ import annotations

import json
import sys
from io import StringIO
from typing import TYPE_CHECKING, Any

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scanner import ScannerError

if TYPE_CHECKING:
    from pathlib import Path  # TC003

    from gherkin.parser_types import GherkinDocument  # TC002

__all__ = ["GherkinFormatter", "parse_gherkin_file"]


def parse_gherkin_file(file_path: Path) -> GherkinDocument | None:
    """
    Parse a Gherkin .feature file and return its Abstract Syntax Tree (AST).

    The AST structure is typically a dictionary-like object (gherkin.GherkinDocument)
    representing the Gherkin document, with a top-level 'feature' key.
    Using `Any` for now as `GherkinDocument` type is not easily importable for hinting.

    :param file_path: The path to the .feature file.
    :type file_path: Path
    :return: The GherkinDocument, or None if parsing fails.
    :rtype: Optional[GherkinDocument]
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            file_content: str = f.read()

        return Parser().parse(file_content)
    except CompositeParserException as e:
        # Consider logging this error instead of just printing if this were a library
        print(f"Error parsing file: {file_path}\n{e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}", file=sys.stderr)
        return None
    except Exception as e:  # pylint: disable=broad-exception-caught # noqa: BLE001
        print(
            f"An unexpected error occurred while parsing {file_path}: {e}",
            file=sys.stderr,
        )
        return None


# pylint: disable-next=too-many-instance-attributes, too-few-public-methods
class GherkinFormatter:
    """
    Formats a Gherkin Abstract Syntax Tree (AST) into a consistently styled string.

    This class takes a Gherkin AST (as produced by `gherkin.parser.Parser`)
    and applies formatting rules for indentation, spacing, and alignment
    to generate a standardized string representation of the feature file.
    """

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        ast: GherkinDocument | dict[str, Any],
        *,
        tab_width: int = 2,
        use_tabs: bool = False,
        alignment: str = "left",
        multi_line_tags: bool = False,
    ) -> None:
        """
        Initialize the GherkinFormatter.

        :param ast: The Gherkin Abstract Syntax Tree (GherkinDocument).
        :type ast: GherkinDocument | dict[str, Any]
        :param tab_width: Spaces for indentation if not using tabs (default: 2).
        :type tab_width: int
        :param use_tabs: Whether to use tabs for indentation (default: False).
        :type use_tabs: bool
        :param alignment: Table cell content alignment ('left'/'right').
        :type alignment: str
        :param multi_line_tags: Format tags over multiple lines (default: False).
        :type multi_line_tags: bool
        """
        self.ast: Any = ast
        self.tab_width: int = tab_width
        self.use_tabs: bool = use_tabs
        self.alignment: str = alignment
        self.multi_line_tags: bool = multi_line_tags
        self.indent_str = "\t" if self.use_tabs else " " * self.tab_width
        self.comments_to_process: list[dict[str, Any]] = sorted(  # type: ignore[misc]
            self.ast.get("comments", []),
            key=lambda c: c.get("location", {}).get("line", float("inf")),
        )

    def _format_comments_up_to_line(
        self,
        target_line_number: int,
        current_indent_level: int,
    ) -> list[str]:
        """
        Format comments that appear before a specific line number.

        :param target_line_number: The line number before which comments should be
            formatted.
        :type target_line_number: int
        :param current_indent_level: The current indentation level for these comments.
        :type current_indent_level: int
        :return: A list of formatted comment lines.
        :rtype: List[str]
        """
        comment_lines: list[str] = []
        comments_processed_this_call: list[dict[str, Any]] = []

        for comment_node in self.comments_to_process:
            comment_location = comment_node.get("location")
            if (
                comment_location
                and comment_location.get("line", float("inf")) < target_line_number
            ):
                text = comment_node.get("text", "").strip()
                comment_lines.append(self._indent_line(text, current_indent_level))
                comments_processed_this_call.append(comment_node)
            else:
                # Since comments are sorted by line, we can stop early
                break

        # Remove processed comments from the main list
        for comment_node in comments_processed_this_call:
            self.comments_to_process.remove(comment_node)

        return comment_lines

    def _indent_line(self, text: str, level: int) -> str:
        """
        Apply indentation to a single line of text.

        :param text: The text to indent.
        :type text: str
        :param level: The indentation level (number of indent units).
        :type level: int
        :return: The indented string.
        :rtype: str
        """
        return f"{self.indent_str * level}{text}"

    def _format_description(
        self,
        description: str | None,
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a multi-line description string with appropriate indentation.

        :param description: The description text, possibly None or empty.
        :type description: str | None
        :param current_indent_level: The current indentation level for these lines.
        :type current_indent_level: int
        :return: A list of formatted description lines.
        :rtype: List[str]
        """
        lines: list[str] = []
        if description:
            lines.extend(
                self._indent_line(line.strip(), current_indent_level)
                for line in description.strip().split("\n")
            )
        return lines

    def _format_tags(
        self,
        tags_list: list[dict[str, str]],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a list of tags.

        Example AST for tags: `[{'name': '@tag1', ...}, {'name': '@tag2', ...}]`
        Can format as single line or multi-line based on `self.multi_line_tags`.

        :param tags_list: A list of tag dictionaries from the AST.
        :type tags_list: list[dict[str, str]]
        :param current_indent_level: The indentation level for the tag line(s).
        :type current_indent_level: int
        :return: A list containing formatted tag lines, or an empty list if no tags.
        :rtype: list[str]
        """
        if not tags_list:
            return []

        if self.multi_line_tags:
            return [
                self._indent_line(tag["name"], current_indent_level)
                for tag in tags_list
            ]
        tag_names: list[str] = [tag["name"] for tag in tags_list]
        return [self._indent_line(" ".join(tag_names), current_indent_level)]

    def _format_table(
        self,
        table_node_rows: list[dict[str, Any]],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a Gherkin data table with aligned columns.

        Assumes `table_node_rows` is a list of row dicts, each with a 'cells' key
        containing a list of cell dicts (each with a 'value').

        :param table_node_rows: List of row data from AST (tableHeader + tableBody).
        :type table_node_rows: list[dict[str, Any]]
        :param current_indent_level: Indentation level for each table line.
        :type current_indent_level: int
        :return: A list of formatted table lines.
        :rtype: list[str]
        """
        if not table_node_rows:
            return []

        num_columns: int = len(table_node_rows[0]["cells"]) if table_node_rows else 0
        if num_columns == 0:
            # Minimal representation for empty row
            return [
                self._indent_line("| |", current_indent_level) for _ in table_node_rows
            ]

        col_widths: list[int] = [0] * num_columns
        for row_data in table_node_rows:
            for i, cell in enumerate(row_data["cells"]):
                col_widths[i] = max(col_widths[i], len(cell["value"]))

        formatted_lines: list[str] = []
        for row_data in table_node_rows:
            formatted_cells: list[str] = [
                cell["value"].ljust(col_widths[i])
                for i, cell in enumerate(row_data["cells"])
            ]
            formatted_lines.append(
                self._indent_line(
                    f"| {' | '.join(formatted_cells)} |",
                    current_indent_level,
                ),
            )
        return formatted_lines

    def _format_docstring(
        self,
        docstring_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a Gherkin DocString.

        Attempts to parse content as JSON and formats it; otherwise,
        treats as plain text.

        :param docstring_node: The DocString node from the AST.
        :type docstring_node: dict[str, Any]
        :param current_indent_level: Indentation level for the DocString.
        :type current_indent_level: int
        :return: A list of formatted DocString lines.
        :rtype: list[str]
        """
        lines: list[str] = []
        delimiter: str = docstring_node.get("delimiter", '"""')
        lines.append(self._indent_line(delimiter, current_indent_level))

        content: str = docstring_node.get("content", "")

        try:
            json_obj: Any = json.loads(content)
            # If successful, format with indentation.
            # json.dumps indent parameter expects int for spaces.
            # If using tabs for Gherkin, JSON will use spaces for simplicity.
            json_indent_size = self.tab_width
            json_formatted_str: str = json.dumps(json_obj, indent=json_indent_size)

            lines.extend(
                self._indent_line(line, current_indent_level)
                for line in json_formatted_str.split("\n")
            )
        except json.JSONDecodeError:
            # If not JSON, try to parse as YAML.
            try:
                self._parse_and_format_yaml_docstring(
                    content,
                    lines,
                    current_indent_level,
                )
            except (ValueError, TypeError, YAMLError, ScannerError):
                # If not JSON or structured YAML, treat as plain text.
                if content:  # Only process if content is not empty
                    lines.extend(
                        self._indent_line(line, current_indent_level)
                        for line in content.splitlines()
                    )
        lines.append(self._indent_line(delimiter, current_indent_level))
        return lines

    def _raise_if_empty_yaml_content(self, content: str) -> None:
        if not content.strip():
            # Use a more specific exception or handle appropriately
            msg = "Empty content, treat as plain text"
            raise ValueError(msg) from None

    def _raise_if_unstructured_yaml(self, yaml_obj: Any) -> None:  # noqa: ANN401
        if not isinstance(yaml_obj, (dict, list)):
            msg = "Not a structured YAML document (map or list)"
            raise TypeError(msg) from None

    def _parse_and_format_yaml_docstring(
        self,
        content: str,
        lines: list[str],
        current_indent_level: int,
    ) -> None:
        """
        Parse and format YAML content for docstrings.

        :param content: docstring content
        :type content: str
        :param lines: docstring lines
        :type lines: list[str]
        :param current_indent_level: current indent level
        :type current_indent_level: int
        """
        self._raise_if_empty_yaml_content(content)
        ruamel_yaml_instance = YAML()
        ruamel_yaml_instance.indent(
            mapping=self.tab_width,
            sequence=self.tab_width,
            offset=self.tab_width,
        )
        ruamel_yaml_instance.preserve_quotes = True
        ruamel_yaml_instance.allow_unicode = True
        yaml_obj: Any = ruamel_yaml_instance.load(content)
        self._raise_if_unstructured_yaml(yaml_obj)

        string_stream = StringIO()
        ruamel_yaml_instance.dump(yaml_obj, string_stream)
        yaml_formatted_str = string_stream.getvalue().rstrip("\n")
        string_stream.close()

        lines.extend(
            self._indent_line(line, current_indent_level)
            for line in yaml_formatted_str.split("\n")
        )

    def _format_step(
        self,
        step_node: dict[str, Any],
        current_indent_level: int,
        max_keyword_len: int,
    ) -> list[str]:
        """
        Format a single Gherkin step, including DataTable or DocString.

        Keywords are aligned based on `max_keyword_len` and `self.alignment`.

        :param step_node: The step node from the AST.
        :type step_node: dict[str, Any]
        :param current_indent_level: Indentation level for the step.
        :type current_indent_level: int
        :param max_keyword_len: Max keyword length in the current block for alignment.
        :type max_keyword_len: int
        :return: A list of formatted step lines.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before this step
        step_line = step_node.get("location", {}).get("line", 1)
        lines.extend(self._format_comments_up_to_line(step_line, current_indent_level))

        keyword: str = step_node["keyword"].strip()
        text: str = step_node["text"].strip()

        if max_keyword_len > 0:
            aligned_keyword: str
            if self.alignment == "right":
                aligned_keyword = keyword.rjust(max_keyword_len)
            else:  # Default to left alignment
                aligned_keyword = keyword.ljust(max_keyword_len)
            lines.append(
                self._indent_line(
                    f"{aligned_keyword.rstrip()} {text}",
                    current_indent_level,
                ),
            )
        else:
            lines.append(self._indent_line(f"{keyword} {text}", current_indent_level))

        if step_node.get("dataTable"):
            lines.extend(
                self._format_table(
                    step_node["dataTable"]["rows"],
                    current_indent_level + 1,
                ),
            )
        if step_node.get("docString"):
            lines.extend(
                self._format_docstring(
                    step_node["docString"],
                    current_indent_level + 1,
                ),
            )
        return lines

    def _format_steps_block(
        self,
        steps_nodes: list[dict[str, Any]],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a block of steps, aligning keywords.

        :param steps_nodes: A list of step nodes.
        :param current_indent_level: The indentation level for this block.
        :return: A list of formatted step lines.
        """
        if not steps_nodes:
            return []

        max_keyword_len: int = 0
        for step_node in steps_nodes:
            keyword = step_node["keyword"].strip()
            max_keyword_len = max(max_keyword_len, len(keyword))

        formatted_steps_lines: list[str] = []
        for step_node in steps_nodes:
            formatted_steps_lines.extend(
                self._format_step(step_node, current_indent_level, max_keyword_len),
            )
        return formatted_steps_lines

    def _format_examples(
        self,
        examples_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format an Examples block, including tags, description, and table.

        :param examples_node: The Examples node from the AST.
        :type examples_node: dict[str, Any]
        :param current_indent_level: Indentation level for the Examples block.
        :type current_indent_level: int
        :return: A list of formatted Examples lines.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before this examples block
        examples_line = examples_node.get("location", {}).get("line", 1)
        lines.extend(
            self._format_comments_up_to_line(examples_line, current_indent_level),
        )

        lines.extend(
            self._format_tags(examples_node.get("tags", []), current_indent_level),
        )

        keyword: str = examples_node["keyword"].strip()
        name_part: str = (
            f" {examples_node['name']}" if examples_node.get("name") else ""
        )
        # Ensure colon after "Examples" keyword
        lines.append(self._indent_line(f"{keyword}:{name_part}", current_indent_level))

        lines.extend(
            self._format_description(
                examples_node.get("description"),
                current_indent_level + 1,
            ),
        )

        if examples_node.get("tableHeader"):
            header = examples_node["tableHeader"]
            body = examples_node.get("tableBody", [])
            all_rows_data: list[dict[str, Any]] = [header, *body]
            lines.extend(self._format_table(all_rows_data, current_indent_level + 1))
        return lines

    def _format_scenario_definition(
        self,
        scenario_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a Scenario or Scenario Outline definition.

        Includes tags, keyword, name, description, steps, and examples (for outlines).

        :param scenario_node: The Scenario/Scenario Outline node from the AST.
        :type scenario_node: dict[str, Any]
        :param current_indent_level: Indentation level for the definition.
        :type current_indent_level: int
        :return: A list of formatted lines for the scenario definition.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before this scenario definition
        scenario_line = scenario_node.get("location", {}).get("line", 1)
        lines.extend(
            self._format_comments_up_to_line(scenario_line, current_indent_level),
        )

        lines.extend(
            self._format_tags(scenario_node.get("tags", []), current_indent_level),
        )

        keyword: str = scenario_node["keyword"].strip()
        name_part: str = (
            f": {scenario_node['name']}" if scenario_node.get("name") else ""
        )
        lines.append(self._indent_line(f"{keyword}{name_part}", current_indent_level))

        lines.extend(
            self._format_description(
                scenario_node.get("description"),
                current_indent_level + 1,
            ),
        )

        lines.extend(
            self._format_steps_block(
                scenario_node.get("steps", []),
                current_indent_level + 1,
            ),
        )

        for examples_node in scenario_node.get("examples", []):
            lines.append("")  # Blank line before Examples section for readability
            lines.extend(self._format_examples(examples_node, current_indent_level + 1))
        return lines

    def _format_background(
        self,
        background_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a Background section.

        :param background_node: The Background node from the AST.
        :type background_node: dict[str, Any]
        :param current_indent_level: Indentation level for the Background.
        :type current_indent_level: int
        :return: A list of formatted lines for the Background.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before this background definition
        background_line = background_node.get("location", {}).get("line", 1)
        lines.extend(
            self._format_comments_up_to_line(background_line, current_indent_level),
        )

        keyword: str = background_node["keyword"].strip()
        name_part: str = (
            f" {background_node['name']}" if background_node.get("name") else ""
        )
        # Ensure colon after "Background" keyword
        lines.append(self._indent_line(f"{keyword}:{name_part}", current_indent_level))

        lines.extend(
            self._format_description(
                background_node.get("description"),
                current_indent_level + 1,
            ),
        )

        lines.extend(
            self._format_steps_block(
                background_node.get("steps", []),
                current_indent_level + 1,
            ),
        )
        return lines

    def _format_rule(
        self,
        rule_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format a Rule section.

        :param rule_node: The Rule node from the AST.
        :type rule_node: dict[str, Any]
        :param current_indent_level: Indentation level for the Rule.
        :type current_indent_level: int
        :return: A list of formatted lines for the Rule.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before this rule definition
        rule_line = rule_node.get("location", {}).get("line", 1)
        lines.extend(self._format_comments_up_to_line(rule_line, current_indent_level))

        lines.append(
            self._indent_line(
                f"{rule_node['keyword']}: {rule_node['name']}",
                current_indent_level,
            ),
        )

        lines.extend(
            self._format_description(
                rule_node.get("description"),
                current_indent_level + 1,
            ),
        )

        children_nodes: list[dict[str, Any]] = rule_node.get("children", [])
        if children_nodes:
            lines.append("")  # Ensure blank line before children block

        for i, child in enumerate(children_nodes):
            if i > 0:  # Add a blank line between children
                lines.append("")
            if "scenario" in child:
                lines.extend(
                    self._format_scenario_definition(
                        child["scenario"],
                        current_indent_level + 1,
                    ),
                )
            elif "background" in child:
                lines.extend(
                    self._format_background(
                        child["background"],
                        current_indent_level + 1,
                    ),
                )
            elif "rule" in child:  # Handle nested rules
                lines.extend(self._format_rule(child["rule"], current_indent_level + 1))
        return lines

    def _format_feature(
        self,
        feature_node: dict[str, Any],
        current_indent_level: int,
    ) -> list[str]:
        """
        Format the main Feature section of the Gherkin document.

        :param feature_node: The Feature node from the AST.
        :type feature_node: dict[str, Any]
        :param current_indent_level: The starting indentation level (usually 0).
        :type current_indent_level: int
        :return: A list of formatted lines for the Feature.
        :rtype: list[str]
        """
        lines: list[str] = []

        # Add comments that appear before the feature definition
        feature_line = feature_node.get("location", {}).get("line", 1)
        lines.extend(
            self._format_comments_up_to_line(feature_line, current_indent_level),
        )

        lines.extend(
            self._format_tags(feature_node.get("tags", []), current_indent_level),
        )

        keyword: str = feature_node["keyword"].strip()
        name_part: str = f": {feature_node['name']}" if feature_node.get("name") else ""
        lines.append(self._indent_line(f"{keyword}{name_part}", current_indent_level))

        if feature_node.get("description"):
            desc_lines: list[str] = feature_node["description"].strip().split("\n")
            for line in desc_lines:
                if line.strip():  # Only indent non-empty description lines
                    lines.append(
                        self._indent_line(line.strip(), current_indent_level + 1),
                    )
                else:  # Keep empty lines in description as they are, but without indent
                    lines.append("")

        children_nodes: list[dict[str, Any]] = feature_node.get("children", [])
        if children_nodes:
            lines.append("")  # Ensure blank line before children block

        for i, child in enumerate(children_nodes):
            if i > 0:  # Add a blank line between children (Scenarios, Rules, etc.)
                lines.append("")

            if "background" in child:
                lines.extend(
                    self._format_background(
                        child["background"],
                        current_indent_level + 1,
                    ),
                )
            elif "rule" in child:
                lines.extend(self._format_rule(child["rule"], current_indent_level + 1))
            elif "scenario" in child:
                lines.extend(
                    self._format_scenario_definition(
                        child["scenario"],
                        current_indent_level + 1,
                    ),
                )
        return lines

    def format(self) -> str:
        """
        Orchestrates the formatting of the entire Gherkin AST.

        :return: A single string representing the fully formatted Gherkin document.
        :rtype: str
        """
        output_lines: list[str] = []

        if not self.ast:
            return "\n"  # Empty line for an empty AST

        # Initialize comments_to_process if not already done
        # (e.g., if format is called multiple times).
        # Though typically, a new Formatter instance would be created.
        if not hasattr(self, "comments_to_process"):
            self.comments_to_process = sorted(
                self.ast.get("comments", []),
                key=lambda c: c.get("location", {}).get("line", float("inf")),
            )

        feature_node: dict[str, Any] | None = self.ast.get("feature")

        if feature_node:
            output_lines.extend(self._format_feature(feature_node, 0))

        # Add any remaining comments (e.g., comments at the end of the file).
        # These are typically unindented or should adopt the last known indent
        # if applicable. For simplicity, adding them with 0 indent.
        # A more sophisticated approach might try to determine the last
        # block's indent.
        if self.comments_to_process:
            # If there were feature lines, add a blank line before trailing
            # comments if not already blank.
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            for comment_node in self.comments_to_process:
                text = comment_node.get("text", "").strip()
                # Comments at the very end of the file are typically not indented,
                # or their indentation is relative to the last element,
                # which is complex to track here.
                # Defaulting to 0 indentation for trailing comments.
                output_lines.append(self._indent_line(text, 0))

        if not output_lines:
            return "\n"

        full_content: str = "\n".join(output_lines)
        return full_content.strip() + "\n"
