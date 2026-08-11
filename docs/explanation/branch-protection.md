# Why `main` is branch-protected the way it is

<!--TOC-->

______________________________________________________________________

- [1. The shape of the protection](#1-the-shape-of-the-protection)
- [2. Why `Build HTML for GitHub Pages` is now required](#2-why-build-html-for-github-pages-is-now-required)
- [3. Why protect at all](#3-why-protect-at-all)
- [4. Why these specific choices](#4-why-these-specific-choices)
  - [4.1. `enforce_admins: false`](#41-enforce_admins-false)
  - [4.2. `strict: false`](#42-strict-false)
  - [4.3. No required PR reviews](#43-no-required-pr-reviews)
  - [4.4. `required_linear_history: true`](#44-required_linear_history-true)
  - [4.5. `allow_force_pushes: false` and `allow_deletions: false`](#45-allow_force_pushes-false-and-allow_deletions-false)
  - [4.6. `required_conversation_resolution: true`](#46-required_conversation_resolution-true)
- [5. How to inspect or change it](#5-how-to-inspect-or-change-it)
- [6. See also](#6-see-also)

______________________________________________________________________

<!--TOC-->

The `main` branch on this repository has classic branch protection configured. This page documents what is enforced, what is deliberately _not_ enforced, and
why each knob is set the way it is. The settings themselves live in repository configuration, not in the tree, so without a write-up like this the rationale is
invisible to anyone reading the code.

## 1. The shape of the protection

| Setting                            | Value   | Effect on `main`                                                               |
| ---------------------------------- | ------- | ------------------------------------------------------------------------------ |
| Required status checks             | 24      | A PR cannot merge until every one of them is green.                            |
| `strict` (up-to-date branch)       | `false` | A PR branch does not have to be rebased onto the latest `main` before merging. |
| Required PR reviews                | none    | No human approval is enforced.                                                 |
| `enforce_admins`                   | `false` | Repository admins bypass _all_ of the rules above.                             |
| `required_linear_history`          | `true`  | Merge commits are rejected — squash or rebase only.                            |
| `allow_force_pushes`               | `false` | Force-pushes are rejected for non-admins.                                      |
| `allow_deletions`                  | `false` | The branch itself cannot be deleted.                                           |
| `required_conversation_resolution` | `true`  | PR review threads must be marked resolved before merge.                        |

The 24 required status checks enforce a comprehensive quality gate across multiple dimensions. The required contexts are:

- **Test suite:** `pytest (py3.11)` through `pytest (py3.14)` — 4 checks ensuring correctness across all supported Python versions.
- **Build & install sanity:** `sanity (py3.11)` through `sanity (py3.14)` — 4 checks verifying the package builds and installs cleanly.
- **Type checkers:** `ty (py3.11)` through `ty (py3.14)` — 4 checks running static type checking across the matrix.
- **Security scanning:** `bandit (py3.11)` through `bandit (py3.14)` — 4 checks for security vulnerabilities.
- **Pre-commit suite:** `pre-commit (py)` — 1 check running the full formatting/lint/security/config-file pipeline.
- **CodeQL analysis:** `Analyze (python)` and `Analyze (actions)` — 2 checks for deep static analysis and vulnerability detection.
- **Documentation build:** `Build HTML for GitHub Pages` — 1 check ensuring the docs build successfully.

Two CI jobs are deliberately _excluded_ from the required list:

- **`Broken external link check`** (formerly "Link check (external, informational)") — `continue-on-error: true` by design (external links flap), so it would
  block merges for reasons outside the contributor's control.
- **`Deploy to GitHub Pages`** — only triggers on `push` to `main` after `Build HTML for GitHub Pages` succeeds, so it's a deployment step rather than a merge
  gate.

## 2. Why `Build HTML for GitHub Pages` is now required

Earlier versions of this branch protection excluded the documentation build from the required list, reasoning that it "only triggers on `push` to `main`, never
on a PR, so requiring it would create an unsatisfiable precondition." The workflow has since been restructured: `Build HTML for GitHub Pages` now runs on both
`push` and `pull_request` events (with `types: [opened, reopened]`), while the _deployment_ step (`Deploy to GitHub Pages`) remains gated on `push` to `main`.
This split means PRs can (and must) prove the docs build successfully before merge, while the actual Pages publish happens only after the merge lands on `main`.
Requiring the build check catches Sphinx errors, broken cross-references, and MyST syntax issues in the PR review phase rather than post-merge.

## 3. Why protect at all

The project is currently solo and pushes directly to `main`, so on the surface branch protection looks like ceremony. It is in place for two forward-looking
reasons:

- **Drive-by contributors.** The first PR a stranger opens should meet the same bar as the maintainer's own commits, and that bar should not depend on the
  maintainer remembering to run the full matrix. Required checks make the bar mechanical.
- **A guard rail for the maintainer.** Even with admin bypass, the protection nudges the maintainer toward PR-based workflows for any non-trivial change — and
  the linear-history and no-force-push rules make it harder to accidentally rewrite published history (which, on a project that publishes to PyPI, is a
  release-management hazard).

## 4. Why these specific choices

### 4.1. `enforce_admins: false`

The maintainer is the sole admin and pushes directly to `main` for routine fixes (docs, lint, dependency bumps). Setting `enforce_admins: true` would force
every such commit through a PR with the full check matrix. For a solo alpha that's a productivity tax with no security upside — there is no second pair of eyes
available to gate on. When the project grows past one person, flipping this to `true` becomes worthwhile.

### 4.2. `strict: false`

Strict mode requires every PR branch to be up-to-date with `main` before merge — i.e. another rebase-and-recheck round-trip every time the base branch moves. On
a low-traffic alpha repo the protection that buys (rejecting a PR whose merge would silently break against newer `main`) is almost never engaged. The friction
it adds (every PR needs a final "update branch" click) is paid every time. Easy to flip on later.

### 4.3. No required PR reviews

Solo project. Requiring approvals when there is no second reviewer just blocks merges. The setting is `required_pull_request_reviews: null` rather than "1
approval", because the latter would still require a _PR-shaped_ event (so direct pushes would break), whereas `null` leaves the maintainer's direct-push
workflow alone entirely.

### 4.4. `required_linear_history: true`

Merge commits make the history harder to read and harder to bisect. Linear history (squash or rebase) keeps `main`'s log a clean left-to-right line, which
matches how `git describe` derives version numbers in {doc}`../reference/supported-configurations` and how the `Deploy to GitHub Pages` workflow's gating on
`github.ref == 'refs/heads/main'` is meant to behave (one published commit per release-worthy state).

### 4.5. `allow_force_pushes: false` and `allow_deletions: false`

These are protection against the _worst_ kind of accident — losing published history that downstream users may have pinned via git refs. Admins bypass them, but
a fat-fingered `git push --force` from a non-admin (or from a misconfigured CI bot) is now rejected by the server rather than silently rewriting published
commits.

### 4.6. `required_conversation_resolution: true`

Cheap to have on; biggest payoff is the first time someone forgets to mark "we agreed not to do X" resolved before merging the PR that did X.

## 5. How to inspect or change it

The protection settings are managed through the GitHub API. The maintainer can read them with:

```console
$ gh api repos/bdperkin/gamesheet-sdk-py/branches/main/protection
```

and replace them entirely with a `PUT` to the same URL (the API is replace-not-merge — every field must be specified on every change).

Adjustments worth thinking about as the project matures:

- Add new CI check names to `required_status_checks.contexts` as new jobs are introduced, so they actually gate merges.
- Flip `enforce_admins` to `true` once there is more than one maintainer.
- Flip `strict` to `true` if PRs start landing fast enough that base-branch drift becomes a real problem.
- Add `required_pull_request_reviews` with `required_approving_review_count: 1` the moment a second reviewer exists.

## 6. See also

- {doc}`../reference/supported-configurations` — what each required check actually checks.
- {doc}`../how-to/cut-a-release` — the one workflow that pushes a tag (which bypasses branch-protection entirely, since tags aren't branches) and is gated by
  its own per-job checks.
