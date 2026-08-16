# Security Policy

<!--TOC-->

______________________________________________________________________

- [1. Project Status](#1-project-status)
- [2. Supported Versions](#2-supported-versions)
- [3. Reporting a Vulnerability](#3-reporting-a-vulnerability)
  - [3.1. Reporting Channel](#31-reporting-channel)
  - [3.2. What to Include](#32-what-to-include)
  - [3.3. Response Timeline](#33-response-timeline)
  - [3.4. Disclosure Policy](#34-disclosure-policy)
  - [3.5. Security Advisory Process](#35-security-advisory-process)
- [4. Scope](#4-scope)
  - [4.1. In Scope](#41-in-scope)
  - [4.2. Out of Scope](#42-out-of-scope)
- [5. Security Best Practices](#5-security-best-practices)
  - [5.1. Credential Storage](#51-credential-storage)
  - [5.2. API Key Handling](#52-api-key-handling)
  - [5.3. Dependency Updates](#53-dependency-updates)
  - [5.4. Network Security](#54-network-security)
- [6. Known Security Limitations](#6-known-security-limitations)
  - [6.1. WebUI Automation Dependency](#61-webui-automation-dependency)
  - [6.2. Alpha Status](#62-alpha-status)
- [7. Security-Related CI/CD](#7-security-related-cicd)
- [8. PGP Key for Encrypted Reports](#8-pgp-key-for-encrypted-reports)
- [9. Vulnerability Acceptance](#9-vulnerability-acceptance)
- [10. Contact](#10-contact)

______________________________________________________________________

<!--TOC-->

## 1. Project Status

This project is in **alpha** status. The API and internal implementation are subject to breaking changes without prior notice. Security fixes are prioritized,
but given the early stage, users should expect rapid iteration and potential instability.

## 2. Supported Versions

Security updates are applied to the latest release only. Older versions receive security patches on a case-by-case basis depending on severity and maintenance
burden.

| Version | Supported          | Security Enhancements              |
| ------- | ------------------ | ---------------------------------- |
| 0.4.x   | :white_check_mark: | Trivy, pip-audit, daily Dependabot |
| < 0.4.x | :x:                | End of life                        |

## 3. Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### 3.1. Reporting Channel

**Preferred:** Use [GitHub Security Advisories](https://github.com/bdperkin/gamesheet-sdk-py/security/advisories/new) to report vulnerabilities privately.

**Alternative:** If GitHub Security Advisories are unavailable, email the maintainer directly. Contact information can be found in the project's
`pyproject.toml` under `[project.authors]`.

### 3.2. What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Affected versions (if known)
- Any suggested mitigations or fixes
- Whether you plan to disclose this publicly (and when)

### 3.3. Response Timeline

- **Initial acknowledgment:** Within 48 hours of report submission
- **Triage and assessment:** Within 5 business days
- **Fix timeline:** Varies by severity (critical: \<7 days; high: \<14 days; medium/low: \<30 days)
- **Public disclosure:** Coordinated with reporter after fix is released

### 3.4. Disclosure Policy

We follow **coordinated disclosure**:

1. Vulnerabilities are kept private until a fix is released
2. Reporter is credited in the security advisory (unless anonymity is requested)
3. We aim for a 90-day embargo period; critical issues may be expedited
4. Reporter may disclose after the embargo period or once a fix is publicly released, whichever comes first

### 3.5. Security Advisory Process

Once a vulnerability is confirmed:

1. A private security advisory is created in the GitHub repository
2. A fix is developed and tested in a private fork
3. A CVE is requested (if applicable)
4. A patch release is cut and published to PyPI
5. The security advisory is published with mitigation guidance
6. Dependent projects are notified (if applicable)

## 4. Scope

### 4.1. In Scope

Security vulnerabilities in:

- Authentication flows (credential handling, token storage, session management)
- Data handling (sensitive information leakage, injection vulnerabilities)
- Dependency vulnerabilities (transitive or direct)
- CLI input validation (command injection, path traversal)
- Browser automation security (Playwright session isolation, data leakage)

### 4.2. Out of Scope

The following are **not** covered by security support:

- Issues in the upstream GameSheet platform (report to GameSheet Inc. directly)
- Vulnerabilities requiring physical access to the user's machine
- Social engineering attacks
- DoS attacks against the GameSheet platform
- Issues in unsupported or end-of-life versions

## 5. Security Best Practices

### 5.1. Credential Storage

- **Do not hardcode credentials** in scripts or version control
- Use environment variables (`GAMESHEET_USERNAME`, `GAMESHEET_PASSWORD`) or secure credential managers
- The SDK stores tokens in `~/.cache/gamesheet-sdk-py/browser-state.json` (browser storage state)
- Rotate credentials if the browser state file is compromised

### 5.2. API Key Handling

- Treat Scoring Access Keys (iPad keys) as sensitive credentials
- Do not log or print keys to stdout in production environments
- Use `--output json` or `--output yaml` and pipe to `jq`/`yq` to filter sensitive fields when sharing output

### 5.3. Dependency Updates

- Keep the SDK updated to the latest version to receive security patches
- Run `pip install --upgrade gamesheet-sdk-py` regularly
- Monitor [GitHub Security Advisories](https://github.com/bdperkin/gamesheet-sdk-py/security/advisories) for this repository

### 5.4. Network Security

- The SDK uses HTTPS by default for all GameSheet API communication
- Browser automation (Playwright) uses headless Chromium with sandboxing enabled
- Avoid using `--base-url` with untrusted or non-HTTPS URLs

## 6. Known Security Limitations

### 6.1. WebUI Automation Dependency

This SDK automates the GameSheet WebUI because GameSheet Inc. does not publish a public API for the operations this library targets. As a result:

- **Breakage risk:** Changes to the GameSheet UI can break functionality without warning
- **Limited validation:** The SDK relies on UI-level validation; server-side validation may differ
- **Session hijacking:** If a Playwright browser session is compromised, credentials may be exposed

### 6.2. Alpha Status

- **Breaking changes:** The API surface is unstable; security fixes may introduce breaking changes
- **Limited audit coverage:** The codebase has not undergone a formal security audit
- **Experimental features:** Browser automation workflows are the most fragile and least tested

## 7. Security-Related CI/CD

The project runs automated security and quality checks on every commit:

- **Trivy:** Filesystem and configuration vulnerability scanning (added v0.1.16)

  - Weekly scheduled scans + per-PR validation
  - SARIF upload to GitHub Security tab
  - Fails CI on CRITICAL/HIGH vulnerabilities
  - ([workflow](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/workflows/security-trivy.yml))

- **pip-audit:** Python dependency vulnerability scanner (added v0.1.16)

  - Matrix testing across Python 3.11-3.14
  - Detailed CVE reporting
  - ([workflow](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/workflows/security-trivy.yml))

- **Security, Metrics, and Complexity:** Static security analysis for Python code
  ([workflow](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/workflows/security-_metrics_-_complexity.yml))

- **CodeQL:** Semantic code analysis for security vulnerabilities
  ([workflow](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/workflows/codeql.yml))

- **Dependency Review:** Scans for known vulnerabilities in dependencies
  ([workflow](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/workflows/dependency-review.yml))

- **Dependabot:** Daily automated PRs for security updates (updated v0.1.16)

  - Increased capacity: 10 concurrent PRs
  - Grouped runtime and development updates
  - ([config](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/dependabot.yml))

## 8. PGP Key for Encrypted Reports

At this time, encrypted vulnerability reports are **not required**. GitHub Security Advisories provide sufficient privacy for most reports. If you need to send
encrypted communication, contact the maintainer for a PGP public key.

## 9. Vulnerability Acceptance

For transparency, we document our risk-based approach to vulnerability management:

- **[Vulnerability Acceptance Criteria](docs/security/vulnerability-acceptance-criteria.md):** Detailed rationale for accepting ~240 OS/Chromium vulnerabilities
- **Risk Level:** LOW-MEDIUM (reduced from MEDIUM-HIGH after security enhancements)
- **Monitoring:** Automated daily scanning with Trivy and pip-audit
- **Review Frequency:** Quarterly for accepted vulnerabilities, daily for Python packages

## 10. Contact

For non-security questions, open a [GitHub Issue](https://github.com/bdperkin/gamesheet-sdk-py/issues). For security vulnerabilities, use
[GitHub Security Advisories](https://github.com/bdperkin/gamesheet-sdk-py/security/advisories/new).

______________________________________________________________________

**Last Updated:** 2026-06-10 (v0.1.16 - Added Trivy, pip-audit, vulnerability acceptance documentation)
