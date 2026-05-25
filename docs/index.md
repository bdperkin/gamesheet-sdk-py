# gamesheet-sdk-py

```{warning}
This project is **not affiliated with, endorsed by, or sponsored by GameSheet Inc.**
See the [README disclaimer](https://github.com/bdperkin/gamesheet-sdk-py#%EF%B8%8F-disclaimer)
for the full caveat: this library automates the GameSheet WebUI where a public API
is absent, and may break without warning when the UI changes.
```

Unofficial Python SDK and command-line interface for the
[GameSheet Inc.](https://gamesheet.com) platform.

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 📦 Installation
:link: https://github.com/bdperkin/gamesheet-sdk-py#installation
`pip install gamesheet-sdk-py` and `python -m playwright install chromium` for
browser-driven flows.
:::

:::{grid-item-card} 🐍 API reference
:link: api
:link-type: doc
Browse every public module, class, and function in the {mod}`gamesheet_sdk`
package. Generated from source by `sphinx.ext.autosummary`.
:::

:::{grid-item-card} 🖥 CLI reference
:link: cli
:link-type: doc
Every option of the `gamesheet-sdk-py` command, rendered from the live
`argparse` parser by `sphinx-argparse`.
:::

:::{grid-item-card} 🔗 Cross-references
:link: https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
Links to {py:class}`requests.Session`, {py:mod}`json`, and other dependencies
resolve automatically via Sphinx intersphinx.
:::
::::

## Contents

```{toctree}
:maxdepth: 2

api
cli
```

## Indices

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
