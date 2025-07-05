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

Or, for development, clone the repository and install editable with development dependencies:
```bash
git clone <repository-url>
cd gherkin-formatter
pip install -e .[dev]
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

## Development

This project uses `pytest` for running tests and `pre-commit` for code quality checks.

**Setup:**

After cloning the repository, it's recommended to use a virtual environment:

```bash
# Clone the repository (if you haven't already)
# git clone <repository-url>
# cd gherkin-formatter

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
pre-commit install # Installs pre-commit hooks
```

**Running Tests:**

To execute the test suite:

```bash
pytest
```

**Code Style & Linting:**

This project uses `black`, `isort`, and `ruff` for formatting and linting, managed via `pre-commit` hooks. Ensure hooks are installed and run them before committing:

```bash
pre-commit run --all-files
```

### Using Gherkin Formatter as a pre-commit hook in your projects

You can use `gherkin-formatter` to automatically format your `.feature` files in your own Gherkin-based projects using `pre-commit`.

1.  **Ensure `pre-commit` is installed.** If not, install it:
    ```bash
    pip install pre-commit
    ```

2.  **Create a `pre-commit-hooks.yaml` file in this repository (or ensure it exists).**
    This file tells `pre-commit` about the hook provided by `gherkin-formatter`. If you are developing `gherkin-formatter` itself, this file should already be present.
    ```yaml
    # pre-commit-hooks.yaml
    -   id: format-feature-files
        name: Format feature files
        entry: gherkin-formatter # This assumes gherkin-formatter is in the PATH
        language: python
        types: [gherkin]
        args: [] # Add any default arguments for gherkin-formatter here
        description: "Formats Gherkin feature files using gherkin-formatter."
    ```
    *Note: The `entry` point might need to be adjusted depending on how `gherkin-formatter` is installed in the environment where the pre-commit hook runs. If it's installed as a system script, `gherkin-formatter` should work. If you're pointing to a local development version, you might use `entry: path/to/dev/gherkin-formatter-script.py` or similar.*

3.  **In your own Gherkin project's repository, create or update `.pre-commit-config.yaml`:**
    Add the following to your `.pre-commit-config.yaml` to use the hook from this `gherkin-formatter` repository. Replace `<url-to-this-gherkin-formatter-repo>` with the actual URL (e.g., GitHub URL) and `<tag-or-sha>` with a specific tag, commit SHA, or branch from the `gherkin-formatter` repository (e.g., `main` or a version tag like `v1.0.0`).

    ```yaml
    # .pre-commit-config.yaml in your project
    repos:
    -   repo: <url-to-this-gherkin-formatter-repo> # e.g., https://github.com/yourusername/gherkin-formatter
        rev: <tag-or-sha> # e.g., main or v0.1.0
        hooks:
        -   id: format-feature-files
            # You can override or add arguments here if needed:
            # args: [--tab-width, "4"]
    ```

4.  **Install the git hooks in your project:**
    Navigate to your project's root directory and run:
    ```bash
    pre-commit install
    ```

Now, `gherkin-formatter` will automatically run on your `.feature` files each time you make a commit, ensuring they are consistently formatted.

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
