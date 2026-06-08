# Configure Release Token for Automated Releases

This guide explains how to set up a Personal Access Token (PAT) to allow the automated release workflow to bypass branch protection rules.

## Why This Is Needed

The automated release workflow (`release.yml`) needs to push commits to the protected `main` branch:

1. PSR creates a release commit (`chore(release): X.Y.Z`)
2. PSR updates `pyproject.toml` and `CHANGELOG.md`
3. PSR creates and pushes a git tag

The default `GITHUB_TOKEN` **cannot bypass branch protection**, so PSR fails with:

```text
remote: error: GH006: Protected branch update failed for refs/heads/main
```

## Solution: Use a Personal Access Token

A fine-grained Personal Access Token (PAT) with specific permissions can bypass branch protection.

## Setup Steps

### 1. Create Fine-Grained Personal Access Token

1. Go to: <https://github.com/settings/tokens?type=beta>
2. Click **"Generate new token"** → **"Generate new token (fine-grained)"**
3. Configure the token:
   - **Token name**: `gamesheet-sdk-py-release-token`
   - **Description**: "Allows automated release workflow to push to protected main branch"
   - **Expiration**: 1 year (or custom - you'll need to renew it)
   - **Repository access**: Only select repositories → `gamesheet-sdk-py`
   - **Permissions**:
     - **Contents**: Read and write ✅
     - **Metadata**: Read-only (automatically selected) ✅
4. Click **"Generate token"**
5. **Copy the token** (you won't see it again!)

### 2. Add Token as Repository Secret

1. Go to: <https://github.com/bdperkin/gamesheet-sdk-py/settings/secrets/actions>
2. Click **"New repository secret"**
3. Configure:
   - **Name**: `RELEASE_TOKEN`
   - **Secret**: Paste the token you copied
4. Click **"Add secret"**

### 3. Verify Workflow Configuration

The workflow (`.github/workflows/release.yml`) should already be configured to use the token:

```yaml
- name: Checkout repository
  uses: actions/checkout@v6
  with:
    fetch-depth: 0
    # Use PAT with permissions to bypass branch protection
    token: ${{ secrets.RELEASE_TOKEN || secrets.GITHUB_TOKEN }}

- name: Run semantic-release
  env:
    GH_TOKEN: ${{ secrets.RELEASE_TOKEN || secrets.GITHUB_TOKEN }}
  run: |
    semantic-release version --changelog
```

The `||` fallback means:

- If `RELEASE_TOKEN` exists → use it (can bypass protection)
- If `RELEASE_TOKEN` is missing → use `GITHUB_TOKEN` (will fail on protected branches)

## Testing

After setting up the token:

1. Create a test commit with a conventional commit message:

   ```bash
   git checkout -b test/release-token
   echo "# Test" >> README.md
   git add README.md
   git commit -m "chore: test release token configuration"
   git push -u origin test/release-token
   ```

2. Create and merge a PR to `main`

3. The `Version and Release` workflow should run successfully and push the release commit to `main`

## Token Renewal

Fine-grained PATs expire. When your token expires:

1. You'll see workflow failures with authentication errors
2. Generate a new token following the same steps above
3. Update the `RELEASE_TOKEN` secret with the new value

**Set a calendar reminder** to renew the token before it expires!

## Security Considerations

- **Least Privilege**: The token only has `Contents: write` permission on one repository
- **Expiration**: Tokens expire, requiring periodic renewal (reduces risk of leaked tokens)
- **Repository Secret**: The token is encrypted and only accessible to workflows
- **Audit Trail**: All actions taken with the token are logged in the repository

## Alternative: GitHub App (More Secure)

For organizations or projects requiring higher security, consider using a GitHub App instead:

- More granular permissions
- Rotating credentials
- Better audit logging
- No expiration issues

See: <https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps>

## Troubleshooting

### Workflow Still Fails with "Protected branch update failed"

**Check:**

1. Token was created with `Contents: write` permission
2. Token was added as `RELEASE_TOKEN` secret (exact name matters)
3. Token hasn't expired
4. Token scope includes the `gamesheet-sdk-py` repository

### Token Expired

**Error**: `Bad credentials` or `401 Unauthorized`

**Solution**: Generate a new token and update the secret

### Workflow Can't Find Secret

**Error**: Workflow uses `GITHUB_TOKEN` instead of `RELEASE_TOKEN`

**Check**: Secret name is exactly `RELEASE_TOKEN` (case-sensitive)

## References

- [GitHub Fine-Grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
