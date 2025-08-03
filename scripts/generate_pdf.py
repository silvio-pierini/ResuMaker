import yaml
from jinja2 import Environment, FileSystemLoader
import subprocess
import os
import re
from typing import Any, Dict, List, Union

# ==============================
# Global Variables
# ==============================

LATEX_REPLACEMENTS: Dict[str, str] = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\\textasciitilde{}',
    '^': r'\\textasciicircum{}',
}

BACKSLASH_TOKEN: str = "<<<UNIQUE-BACKSLASH-TOKEN>>>"

# ==============================
# Functions
# ==============================

def latex_escape(text: str) -> str:
    """
    Escape LaTeX special characters (except backslash) in a string.
    Uses negative lookbehind to avoid double escaping.

    Args:
        text: Input string to be escaped.

    Returns:
        A string with LaTeX special characters escaped.
    """
    if not isinstance(text, str):
        return text

    for char, replacement in LATEX_REPLACEMENTS.items():
        # Avoid escaping already escaped characters by negative lookbehind
        text = re.sub(rf'(?<!\\){re.escape(char)}', replacement, text)
    return text


def backslash_escape(data: Any) -> Any:
    """
    Recursively replace backslash tokens with LaTeX escaped backslash.

    Args:
        data: Input data (str, list, dict, or other) to process.

    Returns:
        Data with backslash tokens replaced by LaTeX backslash escape sequences.
    """
    if isinstance(data, dict):
        return {k: backslash_escape(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [backslash_escape(i) for i in data]
    elif isinstance(data, str):
        return data.replace(BACKSLASH_TOKEN, r'\textbackslash{}')
    else:
        return data


def escape_yaml(data: Any) -> Any:
    """
    Recursively escape YAML data for LaTeX output:
    - Replace backslashes with a unique token in strings.
    - Escape other LaTeX special characters.
    - Finally, replace backslash tokens with LaTeX backslash escapes.

    Args:
        data: Input YAML loaded data (could be nested dict/list/str).

    Returns:
        The escaped data structure ready for LaTeX rendering.
    """
    if isinstance(data, dict):
        tmp_data = {k: escape_yaml(v) for k, v in data.items()}
        return backslash_escape(tmp_data)
    elif isinstance(data, list):
        tmp_data = [escape_yaml(i) for i in data]
        return backslash_escape(tmp_data)
    elif isinstance(data, str):
        text = data.replace("\\", BACKSLASH_TOKEN)
        return latex_escape(text)
    else:
        return data

# ==============================
# Main Script
# ==============================

def main() -> None:
    """
    Main function that:
    - Loads the YAML file with CV data.
    - Escapes all necessary LaTeX characters.
    - Renders the LaTeX template using Jinja2.
    - Writes the output .tex file.
    - Calls pdflatex to generate the PDF.
    """
    # Load YAML data
    with open("data/example.yaml", "r", encoding="utf-8") as f:
        cv_data = yaml.safe_load(f)

    # Escape all special characters for LaTeX
    cv_data = escape_yaml(cv_data)

    # Setup Jinja2 environment and load template
    env = Environment(loader=FileSystemLoader("templates/pdf"))
    template = env.get_template("resumaker.tex.j2")

    # Render LaTeX template with escaped data
    output_tex = template.render(cv_data)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    tex_path = "output/resumaker.tex"

    # Write rendered LaTeX to file
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(output_tex)

    # Compile LaTeX file to PDF with pdflatex
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-output-directory=output", tex_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("LaTeX compilation failed:\n")
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()