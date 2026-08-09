# Security Scanning Pipeline

This document describes the comprehensive security scanning pipeline implemented via GitHub Actions workflows.

## 1. Overview

Four specialized security scanning workflows have been implemented following strict CI/CD hardening best practices:

1. **Semgrep SAST** (`semgrep.yml`) - Static Application Security Testing
2. **Workflow Linter** (`workflow-linter.yml`) - GitHub Actions security auditing
3. **OSV Scanner** (`osv-scanner.yml`) - Dependency vulnerability scanning
4. **GitGuardian** (`gitguardian.yml`) - Secret scanning

## 2. Security Hardening Principles

### 2.1. Commit SHA Pinning

All third-party GitHub Actions are pinned to their full 40-character commit SHA instead of mutable version tags. This prevents supply chain attacks where a
malicious actor could replace a tagged version.

**Example:**

```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

### 2.2. Least Privilege Permissions

Every workflow explicitly defines a `permissions:` block at the workflow or job level. Default repository permissions are not relied upon.

**Typical permissions:**

- `contents: read` - Read-only access to repository contents
- `security-events: write` - Upload SARIF results to GitHub Security tab
- No `write` permissions unless absolutely necessary

## 3. Workflow Details

### 3.1. Semgrep SAST (`semgrep.yml`)

**Purpose:** Static analysis for security vulnerabilities, secrets, and code quality issues.

**Triggers:**

- Push to `main` branch
- Pull requests to `main` branch

**Configuration:**

- Runs in Semgrep Docker container (`semgrep/semgrep:1.101.0`)
- Rule packs:
  - `p/security-audit` - General security vulnerabilities
  - `p/secrets` - Hardcoded secrets detection
  - `p/python` - Python-specific security issues
  - `p/dockerfile` - Dockerfile security best practices
- Outputs SARIF format for GitHub Security integration

**Coverage:**

- Python source code (96.9%)
- Dockerfile (0.7%) - Checks for root execution, hardcoded ENV secrets
- Makefile (2.4%) - Security patterns in build scripts

**Secrets Required:**

- `SEMGREP_APP_TOKEN` (optional) - For Semgrep Cloud integration

### 3.2. Workflow Linter (`workflow-linter.yml`)

**Purpose:** Audit GitHub Actions workflows for security issues.

**Triggers:**

- Push to `main` affecting `.github/workflows/**`
- Pull requests to `main` affecting `.github/workflows/**`

**Tool:** [zizmor](https://github.com/woodruffw/zizmor)

**Detects:**

- Unsafe string interpolations (code injection risks)
- Missing `permissions:` blocks
- Unpinned actions (mutable tags)
- Credential exposure in workflow files
- Dangerous workflow patterns

**Installation:** Via `pipx` for reproducible tool versioning

### 3.3. OSV Scanner (`osv-scanner.yml`)

**Purpose:** Scan Python dependencies against the Open Source Vulnerabilities (OSV) database.

**Triggers:**

- Pull requests to `main`
- Push to `main`
- Daily scheduled scan at 2 AM UTC

**Data Sources:**

- Google OSV Database
- GitHub Security Advisories
- PyPI vulnerability database
- NVD (National Vulnerability Database)

**Scans:**

- `pyproject.toml` - Project dependencies
- Lock files (if present)
- Recursive dependency tree

**Action:** `google/osv-scanner-action` (official Google OSV Scanner)

### 3.4. GitGuardian (`gitguardian.yml`)

**Purpose:** Scan for leaked secrets in code, commit history, and pull request diffs.

**Triggers:**

- Pull requests to `main`
- Push to `main`

**Scan Scope:**

- Full commit history (`fetch-depth: 0`)
- Python source files
- Configuration files
- Makefiles
- Dockerfiles
- Any text files in the repository

**Detects:**

- API keys and tokens
- Database credentials
- Private keys (RSA, SSH)
- Cloud provider credentials (AWS, GCP, Azure)
- 350+ secret patterns

**Secrets Required:**

- `GITGUARDIAN_API_KEY` - GitGuardian API authentication

**Configuration:**

- `--show-secrets` - Display found secrets in logs (redacted)
- `--exit-zero` - Don't fail the build on findings (for gradual adoption)
- `--all-policies` - Apply all GitGuardian detection policies

## 4. GitHub Security Tab Integration

All workflows upload results in SARIF (Static Analysis Results Interchange Format) to the GitHub Security tab via:

```yaml
uses: github/codeql-action/upload-sarif@f205ea1c3313d32999d8d6a48b4f6530d4437b38 # v4.37.4
```

**Benefits:**

- Centralized security findings dashboard
- Integration with Dependabot alerts
- Code scanning alerts with inline annotations
- Trend tracking over time

## 5. Required Secrets

Configure the following secrets in repository settings (`Settings > Secrets and variables > Actions`):

| Secret                | Required By       | Purpose                              | How to Obtain                                                  |
| --------------------- | ----------------- | ------------------------------------ | -------------------------------------------------------------- |
| `SEMGREP_APP_TOKEN`   | `semgrep.yml`     | Optional - Semgrep Cloud integration | [semgrep.dev](https://semgrep.dev)                             |
| `GITGUARDIAN_API_KEY` | `gitguardian.yml` | Required - GitGuardian API auth      | [dashboard.gitguardian.com](https://dashboard.gitguardian.com) |

## 6. Action Version Reference

All actions are SHA-pinned. The following table maps SHAs to version tags for reference:

| Action                              | SHA (first 7 chars) | Version Tag | Full SHA                                   |
| ----------------------------------- | ------------------- | ----------- | ------------------------------------------ |
| `actions/checkout`                  | `3d3c42e`           | v7.0.1      | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python`              | `5fda3b9`           | v7.0.0      | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| `actions/upload-artifact`           | `043fb46`           | v7.0.1      | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `github/codeql-action/upload-sarif` | `f205ea1`           | v4.37.4     | `f205ea1c3313d32999d8d6a48b4f6530d4437b38` |
| `GitGuardian/ggshield-action`       | `2002482`           | v1.53.0     | `2002482fb5990b486be5598ebcf48a8eba393fce` |

## 7. Maintenance

### 7.1. Updating Action SHAs

When a new version of an action is released:

1. Find the latest release on the action's GitHub repository
2. Navigate to the release tag
3. Copy the full 40-character commit SHA
4. Update the workflow file with the new SHA
5. Update the inline comment with the new version tag

**Example:**

```yaml
# Old
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

# New (when v7.1.0 is released)
uses: actions/checkout@<new-40-char-sha> # v7.1.0
```

### 7.2. Monitoring

- Review GitHub Security tab weekly for new findings
- Triage and remediate findings based on severity
- Update security policies as needed

### 7.3. False Positives

To suppress false positives:

- **Semgrep:** Add `# nosemgrep` comment or configure in `.semgrepignore`
- **GitGuardian:** Add to `.gitguardian.yaml` ignore list
- **OSV Scanner:** Configure in `osv-scanner.toml`

## 8. References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Semgrep Rules](https://semgrep.dev/explore)
- [OSV Database](https://osv.dev/)
- [GitGuardian Documentation](https://docs.gitguardian.com/)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)

## 9. Compliance

This security scanning pipeline helps satisfy requirements for:

- OWASP Top 10 vulnerability prevention
- CWE (Common Weakness Enumeration) coverage
- Supply chain security (SLSA Level 2+ alignment)
- SOC 2 security controls
- ISO 27001 security monitoring requirements
