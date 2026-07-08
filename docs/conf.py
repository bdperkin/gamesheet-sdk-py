# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Sphinx configuration for the gamesheet-sdk-py documentation."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

# -- Project information -----------------------------------------------------
project = "gamesheet-sdk-py"
author = "bdperkin"
# pylint: disable-next=redefined-builtin
copyright = f"2026, {author}"  # noqa: A001
release = metadata.version("gamesheet-sdk-py")
version = ".".join(release.split(".")[:2])
# -- General configuration ---------------------------------------------------
extensions = [
    # API documentation
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    # Cross-referencing
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    # Quality
    "sphinx.ext.doctest",
    "sphinx.ext.coverage",
    "sphinx.ext.todo",
    "sphinx.ext.duration",
    # Markdown + UI
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    # CLI documentation
    "sphinx_click",
]
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"
# 1. Define your base/fallback exclusions that Sphinx should always ignore
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "_autosummary"]
# 2. Look for .gitignore at the project root (usually one level up from /docs)
# Adjust the path if your conf.py location is structured differently
project_root = Path(__file__).parent.parent
gitignore_path = Path(project_root, ".gitignore")
if Path(gitignore_path).exists():
    with gitignore_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, comments, or negation rules
            if not line or line.startswith(("#", "!")):
                continue
            # Sphinx expect patterns, strip leading/trailing slashes for safety
            # e.g., "/.tox/" becomes ".tox"
            clean_pattern = line.strip("/")
            if clean_pattern and clean_pattern not in exclude_patterns:
                exclude_patterns.append(clean_pattern)
templates_path = ["_templates"]
# -- Automatic API documentation --------------------------------------------
autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False
autosummary_ignore_module_all = False
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "inherited-members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented_params"
autodoc_class_signature = "separated"
autoclass_content = "both"
autodoc_member_order = "bysource"
# -- Napoleon (Google / NumPy docstrings) -----------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_rtype = False
# -- Cross-referencing ------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "click": ("https://click.palletsprojects.com/en/stable/", None),
}
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3
# -- MyST (Markdown) --------------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
    "linkify",
    "substitution",
    "attrs_inline",
    "attrs_block",
]
myst_heading_anchors = 3
# -- TODOs ------------------------------------------------------------------
todo_include_todos = True
# -- HTML output (Furo theme) -----------------------------------------------
html_theme = "furo"
html_title = f"{project} {release}"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/bdperkin/gamesheet-sdk-py/",
    "source_branch": "main",
    "source_directory": "docs/",
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
}
html_show_sourcelink = True
html_copy_source = True
# -- EPUB output ------------------------------------------------------------
epub_show_urls = "footnote"
epub_basename = project
# -- Man-page output --------------------------------------------------------
man_pages = [
    (
        "cli",
        "gamesheet-sdk-py",
        "Unofficial CLI for the GameSheet Inc. platform",
        [author],
        1,
    ),
]
# -- LaTeX / PDF output -----------------------------------------------------
latex_engine = "xelatex"  # Use XeLaTeX for better Unicode support
latex_documents = [
    (
        master_doc,
        f"{project}.tex",
        f"{project} Documentation",
        author,
        "manual",
    ),
]
# LaTeX preamble for Unicode support and better formatting
# fmt: off
latex_elements = {
    # Override Sphinx's default font settings with Latin Modern
    "fontpkg": (
        r"""\usepackage{fontspec}"""
        r"""\defaultfontfeatures{Ligatures=TeX}"""
        r"""\setmainfont{Latin Modern Roman}"""
        r"""\setsansfont{Latin Modern Sans}"""
        r"""\setmonofont{Latin Modern Mono}"""

    ),
    "preamble":
    r"""\usepackage{newunicodechar}

                % --- Status & Emojis ---
                \newunicodechar{🎉}{[CELEBRATE]}  % U+1F389 Party Popper
                \newunicodechar{✅}{[OK]}
                \newunicodechar{✓}{[OK]}
                \newunicodechar{✗}{[X]}
                \newunicodechar{❌}{[X]}
                \newunicodechar{⚠}{[!]}
                \newunicodechar{ℹ}{[INFO]}
                \newunicodechar{💡}{[TIP]}
                \newunicodechar{📝}{[NOTE]}
                \newunicodechar{🚀}{[LAUNCH]}

                % --- Arrows & Directions ---
                \newunicodechar{→}{->}
                \newunicodechar{←}{<-}
                \newunicodechar{↑}{^}
                \newunicodechar{↓}{v}
                \newunicodechar{▼}{v}
                \newunicodechar{▲}{^}
                \newunicodechar{▶}{>}
                \newunicodechar{◀}{<}

                % --- Typography & Bullets ---
                \newunicodechar{•}{*}
                \newunicodechar{°}{\textdegree}
                \newunicodechar{…}{...}
                \newunicodechar{–}{--}  % En-dash
                \newunicodechar{—}{---} % Em-dash

                % --- Box-drawing characters (for architecture diagrams) ---
                \newunicodechar{┌}{+}
                \newunicodechar{┐}{+}
                \newunicodechar{└}{+}
                \newunicodechar{┘}{+}
                \newunicodechar{─}{-}
                \newunicodechar{│}{|}
                \newunicodechar{├}{+}
                \newunicodechar{┤}{+}
                \newunicodechar{┬}{+}
                \newunicodechar{┴}{+}
                \newunicodechar{┼}{+}
                """

    ,
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "figure_align": "htbp",
}
# fmt: on
# -- Link-check options -----------------------------------------------------
linkcheck_retries = 2
linkcheck_timeout = 15
linkcheck_ignore = [
    # Anchors on third-party sites we don't control:
    r"^https?://github\.com/.*#",
]
