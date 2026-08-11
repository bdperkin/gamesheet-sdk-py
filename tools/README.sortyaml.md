# sortyaml

<!--TOC-->

______________________________________________________________________

- [1. Overview](#1-overview)
- [2. Prerequisites](#2-prerequisites)
- [3. Usage](#3-usage)
  - [3.1. Basic Usage](#31-basic-usage)
  - [3.2. Schema-Specific Sorting](#32-schema-specific-sorting)
  - [3.3. Command-Line Options](#33-command-line-options)
  - [3.4. Exit Codes](#34-exit-codes)
- [4. Sorting Behavior](#4-sorting-behavior)
  - [4.1. Default (No Schema)](#41-default-no-schema)
  - [4.2. Schema-Aware Sorting](#42-schema-aware-sorting)
  - [4.3. Long String Folding](#43-long-string-folding)
  - [4.4. Indent Detection](#44-indent-detection)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Related Tools](#6-related-tools)
- [7. Files](#7-files)

______________________________________________________________________

<!--TOC-->

Sort YAML file keys alphabetically while preserving comments, quoting style, and indentation.

## 1. Overview

`sortyaml` sorts the keys of YAML mappings in place, recursively. It auto-detects the file's indentation style, preserves attached comments and scalar quoting,
and optionally folds long quoted strings into block scalars. When no file argument is given it reads from stdin and writes to stdout, making it usable as a pipe
filter or a pre-commit hook.

For well-known configuration formats the tool ships built-in schema-aware sorting rules so that keys appear in their canonical order (e.g., `repo` before `rev`
before `hooks` in a pre-commit config).

## 2. Prerequisites

- Python 3.11+
- Python packages: `rich-click`, `ruamel.yaml`

These are included transitively via `gamesheet-sdk-py[dev]`.

## 3. Usage

### 3.1. Basic Usage

```bash
# Sort a YAML file in place
./tools/sortyaml config.yaml

# Read from stdin, write to stdout
cat config.yaml | ./tools/sortyaml

# Preview changes without modifying
./tools/sortyaml --diff config.yaml

# Check if already sorted (exit 1 if not — useful for CI)
./tools/sortyaml --check config.yaml

# Create a .bak backup before modifying
./tools/sortyaml --backup config.yaml
```

### 3.2. Schema-Specific Sorting

Use `--type` to apply canonical key ordering for known configuration formats:

```bash
./tools/sortyaml --type gitlab-ci .gitlab-ci.yml
./tools/sortyaml --type pre-commit-config .pre-commit-config.yaml
./tools/sortyaml --type genprecommitconfig .genprecommitconfig.yaml
./tools/sortyaml --type dependabot .github/dependabot.yml
./tools/sortyaml --type github-workflow .github/workflows/ci.yml
./tools/sortyaml --type codecov codecov.yml
./tools/sortyaml --type trivyignore .trivyignore.yaml
./tools/sortyaml --type syncdepsoverrides .syncdepsoverrides.yaml
```

`syncdepsoverrides` orders each entry as the argument it is making — what is overridden (`package`, `pinned_by`), which versions are acceptable (`floor`,
`ceiling`), why (`reason`), how that is proven (`verify`), and when to look again (`review`). `review` sits last for the same reason `expired_at` does under
`trivyignore`: it is the entry's expiry metadata rather than part of its substance.

### 3.3. Command-Line Options

| Option            | Default | Description                                           |
| ----------------- | ------- | ----------------------------------------------------- |
| `FILE`            | stdin   | YAML file to sort (positional argument)               |
| `-t`, `--type`    | —       | Schema type for canonical key ordering (see above)    |
| `-s`, `--strict`  | off     | Disable identity-key-first sorting in sequence items  |
| `-d`, `--diff`    | off     | Show unified diff of changes                          |
| `-c`, `--check`   | off     | Exit 1 if file is not already sorted                  |
| `-b`, `--backup`  | off     | Create a `.bak` backup before modifying               |
| `-v`, `--verbose` | off     | Enable verbose output (detected indentation, actions) |
| `-V`, `--version` | —       | Show version and exit                                 |
| `-h`, `--help`    | —       | Show help and exit                                    |

### 3.4. Exit Codes

| Code | Meaning                                         |
| ---- | ----------------------------------------------- |
| 0    | Success (file sorted, already sorted, or stdin) |
| 1    | `--check` mode: file is not sorted              |
| 2    | Error (invalid YAML, invalid flag combination)  |

## 4. Sorting Behavior

### 4.1. Default (No Schema)

All mapping keys are sorted lexicographically. Inside sequences, **identity keys** (`name`, `id`, `uses`, `repo`) are floated to the top of each mapping element
so the most informative field appears first.

### 4.2. Schema-Aware Sorting

With `--type`, keys at each depth level are ordered according to a built-in priority list that matches the format's conventions. Keys not in the priority list
sort lexicographically after the known keys.

| Schema               | Example file               | Key ordering highlights                                                      |
| -------------------- | -------------------------- | ---------------------------------------------------------------------------- |
| `gitlab-ci`          | `.gitlab-ci.yml`           | `include` → `variables` → `stages` → templates → jobs; job keys by lifecycle |
| `pre-commit-config`  | `.pre-commit-config.yaml`  | Top-level globals → `repos`; hook keys by spec                               |
| `genprecommitconfig` | `.genprecommitconfig.yaml` | `globals` → `ci` → `categories`; repo/hook keys                              |
| `dependabot`         | `.github/dependabot.yml`   | `version` → `registries` → `updates`                                         |
| `github-workflow`    | `.github/workflows/*.yml`  | `name` → `on` → `jobs`; job/step keys by spec                                |
| `codecov`            | `codecov.yml`              | Canonical codecov section ordering                                           |
| `trivyignore`        | `.trivyignore.yaml`        | `version` → vulnerability/rule fields by priority                            |
| `syncdepsoverrides`  | `.syncdepsoverrides.yaml`  | `package` → `pinned_by` → bounds → `reason` → `verify` → `review`            |

### 4.3. Long String Folding

After sorting, quoted strings whose rendered inline length would exceed the file's line width (default 110 columns) are automatically converted to YAML block
scalars (`>-` folded style).

### 4.4. Indent Detection

The tool detects the mapping indent, sequence indent, and dash offset from the parsed YAML data and preserves them on output, so files formatted with 2-space or
4-space indentation stay consistent.

## 5. Troubleshooting

| Problem                     | Solution                                                 |
| --------------------------- | -------------------------------------------------------- |
| `--backup` with stdin       | Not supported — use a file argument instead              |
| Keys reorder unexpectedly   | Use `--type` to apply schema-aware ordering              |
| Comments move to wrong keys | ruamel.yaml attaches comments to adjacent keys; re-check |
| `--check` exits 1 in CI     | Run `./tools/sortyaml --diff` to see what would change   |

## 6. Related Tools

- [`tools/genprecommitconfig`](README.genprecommitconfig.md) — Generates `.pre-commit-config.yaml` (sortyaml can sort the input config)
- [`tools/syncdeps`](README.syncdeps.md) — Dependency convergence (operates on the same YAML files)

## 7. Files

| File             | Purpose           |
| ---------------- | ----------------- |
| `tools/sortyaml` | Executable script |
