# How-to guides

> A how-to guide is a recipe; it serves a reader who **already has enough context to understand the problem and the solution**.
>
> — [diataxis.fr/how-to-guides](https://diataxis.fr/how-to-guides/)

How-to guides are **task-oriented**. The reader has a specific goal in mind and wants the shortest path to it. They are not beginners — they understand the
building blocks; they just need a recipe.

## Authoring guidance

When adding a how-to guide to this section:

- **State the goal in the title.** ("How to authenticate against the GameSheet WebUI", not "Authentication".)
- **Skip pedagogy.** Assume the reader already understands the SDK's building blocks. Cross-link {doc}`../explanation/index` when context is essential.
- **Stay focused.** The guide solves _one_ problem. If you find yourself branching, split the guide.
- **Pick sensible defaults and move on.** Walking through alternative configurations is the job of a {doc}`tutorial <../tutorials/index>`.

## Available guides

```{toctree}
:maxdepth: 1

development-setup
install-in-github-actions
configure-release-token
cut-a-release
release-process
```

## Planned guides

The following how-to guides are planned for future releases based on common SDK workflows:

- **How to authenticate with the GameSheet WebUI** — Using the `login` command to save session tokens
- **How to configure environment variables** — Setting `GAMESHEET_*` env vars for authentication and base URL
- **How to use the Python API directly** — Importing and using SDK modules in your own Python code
- **How to customize output formats** — Using `--format` and `--columns` options for JSON, YAML, CSV, and table outputs
- **How to enable shell completion** — Installing bash/zsh/fish tab-completion for the CLI
- **How to configure headless vs headed mode** — Using `--no-headless` for debugging browser flows
- **How to troubleshoot authentication issues** — Common auth failures and resolution steps
- **How to retrieve season data** — Using `seasons get` and `seasons list` commands
- **How to manage iPad/Scoring Access Keys** — Using `ipad-keys` commands to retrieve scoring credentials
