# Semgrep App Token Setup Guide

## ⚠️ IMPORTANT: This Token is OPTIONAL

**The semgrep.yml workflow will work WITHOUT this token!**

The `SEMGREP_APP_TOKEN` provides additional features:

- ✅ **Without token:** Semgrep runs locally, scans with all rule packs, uploads SARIF to GitHub
- 🎁 **With token:** Above + cloud dashboard, cross-project insights, custom rules, team collaboration

**Recommendation:** Start without the token. Add it later if you need cloud features.

## When to Use Semgrep Cloud Token

Use Semgrep Cloud (requires token) if you need:

- Centralized dashboard across multiple repositories
- Custom rule management
- Team collaboration features
- Historical trend analysis
- Advanced triage workflows
- Policy enforcement

For a single open-source project: **The free OSS version (no token) is sufficient.**

______________________________________________________________________

## Step-by-Step Instructions (if you want the token)

### 1. Sign Up for Semgrep

**URL:** [Semgrep Login](https://semgrep.dev/login)

**Options:**

- **Recommended:** Sign in with GitHub (OAuth)
- Alternative: Sign in with GitLab
- Alternative: Email/password signup

**Plan Selection:**

- **Free for Open Source:** Unlimited scans for public repositories
- **Free Team Plan:** Up to 10 private repositories, 3 contributors
- **Paid Plans:** Enterprise features (not needed for most projects)

### 2. Complete Onboarding

After signing in:

1. Choose **"Add a project"** or **"Connect repository"**
2. Select **GitHub** as the source
3. Authorize Semgrep to access your repositories
4. Select the repository: `bdperkin/gamesheet-sdk-py`
5. Semgrep will perform an initial scan

### 3. Generate App Token

**Navigation:** Settings → Tokens

**Direct URL:** [Semgrep Token Settings](https://semgrep.dev/orgs/-/settings/tokens)

**Steps:**

1. Click your profile icon (top-right)
2. Click **"Settings"**
3. Click **"Tokens"** in the left sidebar
4. Click **"Generate new token"** or **"Create token"**
5. Configure the token:
   - **Name:** `GitHub Actions - gamesheet-sdk-py`
   - **Scope:** Select **"CI"** or **"Agent"** (for CI/CD usage)
   - **Expiration:**
     - Recommended: 90 days
     - Alternative: Never (less secure)
6. Click **"Generate"** or **"Create token"**

### 4. Copy and Save the Token

**IMPORTANT:** The token is shown only ONCE!

```
Example format: <random-string-of-alphanumeric-characters>
```

**Actions:**

1. **Copy the token immediately**
2. Store temporarily in password manager
3. Do NOT commit to git

### 5. Add to GitHub Repository Secrets

**GitHub Repository URL:**

[Repository Secrets Settings](https://github.com/bdperkin/gamesheet-sdk-py/settings/secrets/actions)

**Steps:**

1. Navigate to repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Configure:
   - **Name:** `SEMGREP_APP_TOKEN` (exact name, case-sensitive)
   - **Value:** Paste the token
4. Click **"Add secret"**

**Verification:**

```bash
gh secret list | grep SEMGREP
# Should show: SEMGREP_APP_TOKEN
```

### 6. Enable in Workflow (Already Configured)

The `semgrep.yml` workflow already includes:

```yaml
env:
  SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
```

If the token exists, Semgrep will:

- Upload results to Semgrep Cloud dashboard
- Enable cross-project insights
- Store scan history

If the token is missing:

- Semgrep runs locally (perfectly fine!)
- Results still uploaded to GitHub Security tab
- No errors or failures

______________________________________________________________________

## Comparison: With vs Without Token

### Without Token (Local Mode)

```
✅ Runs Semgrep Docker container locally
✅ Scans all files with configured rule packs
✅ Uploads SARIF to GitHub Security tab
✅ Creates annotations on PRs
✅ Artifacts saved for 30 days
❌ No centralized cloud dashboard
❌ No cross-repository insights
❌ No historical trending
```

### With Token (Cloud Mode)

```
✅ Everything from local mode, PLUS:
✅ Centralized dashboard at semgrep.dev
✅ Historical scan results
✅ Cross-project vulnerability tracking
✅ Team collaboration features
✅ Custom rule management
✅ Policy enforcement
✅ Compliance reporting
```

______________________________________________________________________

## Alternative: Semgrep CI without Token

If you don't want Semgrep Cloud, the workflow can use Semgrep OSS mode:

**Current workflow (supports both):**

```yaml
container:
  image: semgrep/semgrep:1.101.0

steps:
  - run: semgrep scan --config=p/security-audit --config=p/secrets
    env:
      SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }} # Optional
```

**How it works:**

- If `SEMGREP_APP_TOKEN` exists → Cloud mode
- If `SEMGREP_APP_TOKEN` is missing → Local mode (still works perfectly!)

______________________________________________________________________

## Free Tier Limits

### Semgrep Cloud Free (Open Source)

- ✅ Unlimited public repositories
- ✅ Unlimited scans
- ✅ All community rules
- ✅ SARIF export
- ✅ GitHub integration

### Semgrep Cloud Free (Team)

- Up to 10 private repositories
- Up to 3 contributors
- 100 custom rules
- 30-day scan history

### Paid Plans

- Enterprise: Unlimited everything
- Not needed for most projects

______________________________________________________________________

## Security Best Practices

1. **Token Rotation:** Rotate every 90 days
2. **Scope Limitation:** Only grant "CI" scope
3. **Audit Access:** Review token usage in Semgrep dashboard
4. **Revocation:** Immediately revoke if compromised

______________________________________________________________________

## Troubleshooting

### Workflow runs fine without token

- This is expected! No token = local mode (still effective)

### Error: "Invalid Semgrep token"

- Check token was copied correctly (no spaces/newlines)
- Verify secret name is exactly `SEMGREP_APP_TOKEN`
- Ensure token hasn't expired

### Results not appearing in Semgrep Cloud

- Verify token has "CI" or "Agent" scope
- Check project is connected in Semgrep dashboard
- Wait 5-10 minutes for results to sync

______________________________________________________________________

## Token Management

**Dashboard:** [Semgrep Token Management](https://semgrep.dev/orgs/-/settings/tokens)

**Actions:**

- View all tokens
- See last used timestamp
- Revoke tokens
- Create new tokens

______________________________________________________________________

## Recommendation for This Project

**For gamesheet-sdk-py (single open-source project):**

1. **Start WITHOUT the token** (local mode)

   - Perfectly sufficient for security scanning
   - Results in GitHub Security tab
   - Zero cost, zero setup

2. **Add token later** if you need:

   - Multi-repository vulnerability tracking
   - Team collaboration
   - Compliance reporting

**Quick Decision Matrix:**

| Your Situation              | Use Token?                     |
| --------------------------- | ------------------------------ |
| Single developer, 1 repo    | ❌ No (local mode sufficient)  |
| Team, multiple repos        | ✅ Yes (cloud features useful) |
| Need compliance reports     | ✅ Yes (cloud required)        |
| Just want security scanning | ❌ No (local mode perfect)     |

______________________________________________________________________

## Support

- Documentation: [Semgrep Docs](https://semgrep.dev/docs)
- Community: [r2c Slack](https://r2c.dev/slack) (Slack)
- GitHub: [Semgrep Repository](https://github.com/returntocorp/semgrep)
