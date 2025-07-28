# Gherkin Formatter

A Python command-line utility to format Gherkin (`.feature`) files, similar to how `black` formats Python files. This tool helps maintain consistent styling in your BDD feature specifications, ensuring readability and uniformity across your projects.

## Features

*   **Consistent Indentation:** Applies uniform indentation for all Gherkin keywords (e.g., `Feature`, `Scenario`, `Given`, `When`, `Then`).
*   **Keyword Alignment:** Aligns keywords within step blocks (Given/When/Then) for improved readability.
*   **Flexible Tag Formatting:** Supports single-line or multi-line tag styles.
*   **Data Table Formatting:** Automatically aligns columns in Data Tables.
*   **DocString Formatting:** Pretty-prints JSON and YAML content within DocStrings.
*   **Comprehensive Gherkin Support:** Handles `Rule`, `Background`, `Scenario Outline`, `Examples`, and comments.
*   **Non-Destructive:** Preserves all your data; only formatting is changed.

## Installation

Install the Gherkin Formatter using pip:

```bash
pip install gherkin-formatter
```

## Usage

To format your Gherkin files, run:

```bash
gherkin-formatter [OPTIONS] [FILES_OR_DIRECTORIES...]
```

**Arguments:**

*   `FILES_OR_DIRECTORIES...`: One or more `.feature` files or directories containing `.feature` files to format. The tool will recursively search for `.feature` files in directories.

**Options:**

*   `--tab-width INTEGER`: Number of spaces for indentation if not using tabs (default: `2`).
*   `--use-tabs`: Indent using tabs instead of spaces. If set, `--tab-width` is generally ignored for the indentation character.
*   `-a, --alignment [left|right]`: Alignment for Gherkin keywords (e.g., `Given`, `When`, `Then`) within a block of steps.
    *   `left`: Left-aligns keywords (default).
    *   `right`: Right-aligns keywords based on the longest keyword in the current block, providing a visually structured layout.
*   `--multi-line-tags`: Formats each tag on a new line, indented under the associated element. Default is single-line formatting where all tags appear on one line.
*   `--skip-docstrings`: Skip docstrings formatting - useful if using custom code on it
*   `--dry-run`: Preview the changes that would be made without modifying the actual files. The formatted output (if different) will be printed to the console.
*   `--check`: Check if files are formatted correctly according to the specified options. No files are changed.
    *   Exits with code `0` if all files are well-formatted.
    *   Exits with code `1` if one or more files would be reformatted or had file-specific processing issues (e.g., parsing errors).
    *   Exits with code `123` if an internal error occurred in the formatter.
*   `--version`: Show the program's version number and exit.
*   `--help`: Show this help message and exit.

**Examples:**

1.  Format a single file with 4 spaces for indentation:
    ```bash
    gherkin-formatter --tab-width 4 my_feature.feature
    ```

2.  Check if all `.feature` files in the `features/` directory are formatted correctly:
    ```bash
    gherkin-formatter --check features/
    ```

3.  Preview formatting for `my_feature.feature`, aligning keywords to the right:
    ```bash
    gherkin-formatter --dry-run --alignment right my_feature.feature
    ```

4.  Format a file using tabs for indentation and multi-line tags:
    ```bash
    gherkin-formatter --use-tabs --multi-line-tags my_feature.feature
    ```

### Using Gherkin Formatter as a pre-commit hook

You can use `gherkin-formatter` to automatically format your `.feature` files in your projects using [pre-commit](https://pre-commit.com/).

1. **Install pre-commit**
   If not already installed, you can install it with pip:
   ```bash
   pip install pre-commit
   ```

2. **Configure the pre-commit hook**
   In your own project's repository, create or update the `.pre-commit-config.yaml` file with the following:

   ```yaml
   # .pre-commit-config.yaml
   repos:
   -   repo: https://github.com/musthafak/gherkin-formatter
       rev: <tag-or-sha>  # e.g., v0.1.1 or a specific commit SHA
       hooks:
       -   id: format-feature-files
           # You can override or add arguments here if needed:
           # args: [--tab-width, "4"]
   ```
   Replace `<tag-or-sha>` with the latest version tag from this repository or a specific commit SHA.

3. **Install the git hooks**
   Navigate to your project's root directory and run:
   ```bash
   pre-commit install
   ```

Now, `gherkin-formatter` will automatically run on your `.feature` files each time you make a commit, ensuring they are consistently formatted.


## Development

This project uses `pytest` for running tests and [pre-commit](https://pre-commit.com/) for code quality checks.

**Setup:**

After cloning the repository, it's recommended to use a virtual environment:

```bash
# Clone the repository (if you haven't already)
# git clone git@github.com:musthafak/gherkin-formatter.git
# cd gherkin-formatter

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
pre-commit install # Installs pre-commit hooks for auto formatting and linting
```

**Running Tests:**

To execute the test suite:

```bash
pytest
```

**Code Style & Linting:**

This project uses `ruff` and `pyrefly` for formatting and linting, managed via [pre-commit](https://pre-commit.com/) hooks.

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these general steps:

1.  **Fork the repository** and clone it to your local machine.
2.  **Create a new branch** for your feature or bug fix: `git checkout -b my-new-feature`.
3.  **Make your changes** and ensure they are well-tested.
4.  **Ensure pre-commit checks pass**: `pre-commit run --all-files`.
5.  **Run tests** using `pytest` to confirm everything passes.
6.  **Commit your changes**: `git commit -am 'Add some feature'`.
7.  **Push to the branch**: `git push origin my-new-feature`.
8.  **Open a Pull Request** on GitHub.

Please ensure your code adheres to existing styling and that any new functionality is covered by tests.

## License

This project is licensed under the [MIT License](./LICENSE).
