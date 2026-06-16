# Spider Utility Files Overview

Complete reference for all files in the `scripts/` directory related to the GameSheet season spider.

## Core Implementation (2 scripts)

### spider_season.py (711 lines)

**Purpose**: Main spider implementation **Type**: Executable Python script **Dependencies**: `playwright`, `gamesheet_sdk`

**Key Features**:

- Queue-based web crawling
- Network request/response capture
- Mutation detection (POST/PATCH/DELETE)
- Human-like delays (2.5-5s randomized)
- Internal/external URL classification
- JSON output generation
- Custom browser executable support

**Entry Point**: `main(argv)` function **Classes**:

- `SpiderState`: Dataclass for crawl state
- `DiscoveredMutation`: Dataclass for mutation metadata
- `NetworkCapture`: Dataclass for network request metadata
- `SeasonSpider`: Main spider orchestrator

**Usage**:

```bash
./scripts/spider_season.py <season_id> [options]
```

### analyze_spider_output.py (305 lines)

**Purpose**: Analysis and reporting tool for spider output **Type**: Executable Python script **Dependencies**: Standard library only

**Key Features**:

- Summary statistics
- Mutation analysis by method/type
- Network analysis by resource type
- API endpoint extraction
- URL depth analysis
- Error categorization
- Data export (APIs, mutations)

**Entry Point**: `main(argv)` function **Functions**:

- `load_spider_output()`: Load and validate JSON
- `print_summary()`: Overview statistics
- `analyze_mutations()`: Mutation breakdown
- `analyze_network()`: Network captures breakdown
- `analyze_urls()`: URL pattern analysis
- `analyze_errors()`: Error categorization
- `export_api_endpoints()`: Export APIs to text file
- `export_mutations()`: Export mutations to JSON

**Usage**:

```bash
./scripts/analyze_spider_output.py <spider_output.json> [options]
```

## Wrapper Scripts (1 script)

### spider_example.sh (39 lines)

**Purpose**: Convenience wrapper demonstrating common patterns **Type**: Bash shell script **Dependencies**: `spider_season.py`

**Key Features**:

- Credential validation
- Output directory creation
- Environment variable support (`GAMESHEET_BROWSER`)
- Error handling
- Usage examples

**Usage**:

```bash
./scripts/spider_example.sh <season_id> [output_dir]
```

## Documentation (4 files)

### README.md (462 lines)

**Purpose**: Comprehensive technical documentation **Audience**: Developers, operators, contributors

**Sections**:

01. Features overview
02. Safety guarantees
03. Usage examples (basic and advanced)
04. All CLI options reference
05. Output format specification
06. How it works (architecture)
07. Mutation discovery heuristics
08. Limitations
09. Development notes
10. Troubleshooting guide
11. Future enhancements

### SPIDER_QUICK_START.md (371 lines)

**Purpose**: Quick reference guide **Audience**: End users

**Sections**:

1. Prerequisites
2. Common commands
3. Understanding the output
4. Safety features
5. Troubleshooting
6. Performance notes
7. Example workflow
8. Advanced usage (jq examples)

### TEST_PLAN.md (430 lines)

**Purpose**: Testing strategy and checklists **Audience**: QA engineers, contributors

**Sections**:

01. Unit testing strategy
02. Mock testing approach
03. Integration test scenarios
04. Manual testing checklist (comprehensive)
05. Automated testing TODO
06. CI/CD recommendations
07. Test data guidelines
08. VCR configuration
09. Known limitations to test
10. Success criteria

### FILES_OVERVIEW.md (this file)

**Purpose**: Directory structure and file reference **Audience**: New contributors, maintainers

## Example Data (1 file)

### example-output.json (71 lines)

**Purpose**: Sample spider output demonstrating structure **Type**: JSON data file

**Contains**:

- All output sections (visited_urls, mutations, captures, etc.)
- Realistic but synthetic data
- Demonstrates relationship between sections
- Reference for downstream tool integration

## Summary Statistics

| Category            | Files | Lines     | Purpose                     |
| ------------------- | ----- | --------- | --------------------------- |
| **Core Scripts**    | 2     | 1,016     | Implementation and analysis |
| **Wrapper Scripts** | 1     | 39        | Convenience and examples    |
| **Documentation**   | 4     | 1,263     | User guides and references  |
| **Example Data**    | 1     | 71        | Sample output structure     |
| **TOTAL**           | **8** | **2,389** | **Complete solution**       |

## File Relationships

```text
spider_season.py
    ├── Generates → season-{id}-spider.json
    ├── Uses → gamesheet_sdk.auth.login
    ├── Uses → gamesheet_sdk.browser.BrowserSession
    └── Uses → gamesheet_sdk.config.Config

analyze_spider_output.py
    ├── Reads → season-{id}-spider.json
    ├── Exports → api-endpoints.txt (optional)
    └── Exports → mutations.json (optional)

spider_example.sh
    ├── Wraps → spider_season.py
    └── Validates → GAMESHEET_USERNAME, GAMESHEET_PASSWORD

README.md
    ├── Documents → spider_season.py
    ├── Documents → analyze_spider_output.py
    └── References → example-output.json

SPIDER_QUICK_START.md
    ├── Quick reference for → spider_season.py
    ├── Quick reference for → analyze_spider_output.py
    └── Examples using → spider_example.sh

TEST_PLAN.md
    └── Test strategy for → spider_season.py

example-output.json
    ├── Sample output from → spider_season.py
    └── Input example for → analyze_spider_output.py
```

## Usage Workflow

### 1. Initial Setup

```bash
# Install dependencies
pip install -e ".[all]"
python -m playwright install chromium

# Set credentials
export GAMESHEET_USERNAME="user@example.com"
export GAMESHEET_PASSWORD="secret"
```

### 2. Run Spider

```bash
# Basic usage
./scripts/spider_season.py 15020

# Advanced usage
./scripts/spider_season.py 15020 \
  -o results/season-15020.json \
  --browser /usr/bin/chromium-browser \
  -vv
```

### 3. Analyze Results

```bash
# Full analysis
./scripts/analyze_spider_output.py season-15020-spider.json

# Export specific data
./scripts/analyze_spider_output.py season-15020-spider.json \
  --export-apis apis.txt \
  --export-mutations mutations.json
```

### 4. Process Extracted Data

```bash
# View API endpoints
cat apis.txt

# Query mutations
jq '.[] | select(.method == "DELETE")' mutations.json

# Compare multiple seasons
for f in results/*.json; do
  echo "$f: $(jq '.summary.discovered_mutations' $f)"
done
```

## Integration Points

### With SDK

- `gamesheet_sdk.auth.login()` - Authentication flow
- `gamesheet_sdk.browser.BrowserSession` - Browser session management
- `gamesheet_sdk.config.Config` - Configuration resolution

### With External Tools

- **jq**: JSON querying and transformation
- **Playwright**: Browser automation
- **Python**: Runtime and standard library

### With Project Infrastructure

- `.gitignore`: Excludes `season-*-spider.json` and `spider-results/`
- `pyproject.toml`: Dependencies already declared
- `CLAUDE.md`: Project context and guidelines

## Maintenance Notes

### When Adding Features

1. Update `spider_season.py` implementation
2. Update `README.md` documentation
3. Update `SPIDER_QUICK_START.md` examples
4. Add test cases to `TEST_PLAN.md`
5. Update this overview if file structure changes

### When Fixing Bugs

1. Fix in `spider_season.py` or `analyze_spider_output.py`
2. Add regression test to `TEST_PLAN.md`
3. Update documentation if behavior changes
4. Test with `example-output.json` if applicable

### Version Control

- All scripts in `scripts/` are version controlled
- Spider output files (`*.json`) are gitignored
- Example output (`example-output.json`) is version controlled

## Quick Reference

| Task             | Command                                                                |
| ---------------- | ---------------------------------------------------------------------- |
| Spider a season  | `./scripts/spider_season.py 15020`                                     |
| Verbose spider   | `./scripts/spider_season.py 15020 -vv`                                 |
| Custom output    | `./scripts/spider_season.py 15020 -o /tmp/out.json`                    |
| Analyze results  | `./scripts/analyze_spider_output.py season-15020-spider.json`          |
| Export APIs      | `./scripts/analyze_spider_output.py FILE --export-apis apis.txt`       |
| Export mutations | `./scripts/analyze_spider_output.py FILE --export-mutations muts.json` |
| Use wrapper      | `./scripts/spider_example.sh 15020 ./results`                          |
| View help        | `./scripts/spider_season.py --help`                                    |
| Check syntax     | `python -m py_compile scripts/spider_season.py`                        |

## See Also

- **SPIDER_SUMMARY.md** (project root): Implementation summary and deliverables
- **CLAUDE.md** (project root): Project guidelines and architecture
- **tests/** (future): Automated test suite when implemented

______________________________________________________________________

**Last Updated**: 2026-06-15 **Files Version**: 1.0 **Total Lines**: 2,389 **Status**: Complete and ready for use
