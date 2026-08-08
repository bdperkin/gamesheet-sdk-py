# GitGuardian API Key Setup Guide

## 1. Prerequisites

- GitHub account
- Valid email address

## 2. Step-by-Step Instructions

### 2.1. Sign Up for GitGuardian

**URL:** [GitGuardian Sign Up](https://dashboard.gitguardian.com/auth/signup)

**Options:**

- **Recommended:** Sign up with GitHub (OAuth) - fastest method
- Alternative: Sign up with email/password

**Plan Selection:**

- Free tier available: **10,000 secrets scanned/month**
- Sufficient for most projects
- No credit card required

### 2.2. Complete Account Setup

After signing up:

1. Verify your email (if using email signup)
2. Complete the onboarding survey (optional, can skip)
3. You'll land on the GitGuardian dashboard

### 2.3. Generate API Key

**Navigation:** Dashboard → Settings → API → Personal Access Tokens

**Direct URL:** [GitGuardian API Settings](https://dashboard.gitguardian.com/workspace/settings/api)

**Steps:**

1. Click **"API"** in the left sidebar under Settings
2. Click **"Personal Access Tokens"** tab
3. Click **"Create token"** or **"New token"** button
4. Configure the token:
   - **Name:** `GitHub Actions - gamesheet-sdk-py` (or your repo name)
   - **Scope:** Select **"Scan"** (minimum required)
   - **Expiration:** Choose based on your security policy
     - Recommended: 90 days (requires periodic renewal)
     - Alternative: 1 year or No expiration (less secure)
5. Click **"Create"** or **"Generate"**

### 2.4. Copy and Save the Token

**IMPORTANT:** The token is shown only ONCE!

```console
Example format: ggapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Actions:**

1. **Copy the token immediately** - you won't see it again
2. Store it temporarily in a secure location (password manager, secure note)
3. Do NOT commit it to git or save in plain text files

### 2.5. Add to GitHub Repository Secrets

**GitHub Repository URL:**

[Repository Secrets Settings](https://github.com/bdperkin/gamesheet-sdk-py/settings/secrets/actions)

**Steps:**

1. Navigate to your repository on GitHub
2. Click **Settings** (top navigation)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **"New repository secret"** button
5. Configure:
   - **Name:** `GITGUARDIAN_API_KEY` (exact name, case-sensitive)
   - **Value:** Paste the token you copied (starts with `ggapi-`)
6. Click **"Add secret"**

**Verification:**

- The secret should now appear in the list as `GITGUARDIAN_API_KEY`
- The value is hidden (shows as `•••••`)

## 3. Alternative: Using GitHub CLI

If you prefer command-line:

```bash
# Set the secret (you'll be prompted to paste the value)
gh secret set GITGUARDIAN_API_KEY

# Or set it directly (be careful with shell history)
echo "ggapi-your-actual-token-here" | gh secret set GITGUARDIAN_API_KEY

# Verify it was added
gh secret list
```

## 4. Token Permissions

The **"Scan"** scope provides:

- ✅ Ability to scan commits for secrets
- ✅ Access to detection policies
- ✅ Read-only access to scan results
- ❌ No ability to modify workspace settings
- ❌ No ability to delete incidents

## 5. Free Tier Limits

**GitGuardian Free Plan:**

- 10,000 secrets scanned per month
- 1 workspace
- 25 developers
- Public and private repository scanning
- 350+ secret detectors
- GitHub integration

**Typical Usage for This Repo:**

- ~100-500 files scanned per PR
- ~10-20 PRs per month
- Well within free tier limits

## 6. Security Best Practices

1. **Token Rotation:** Rotate the token every 90 days
2. **Scope Limitation:** Only grant "Scan" scope (principle of least privilege)
3. **Audit Access:** Periodically review token usage in GitGuardian dashboard
4. **Revocation:** If compromised, immediately revoke in GitGuardian dashboard

## 7. Troubleshooting

### 7.1. Error: "Invalid API key"

- Double-check you copied the entire token
- Ensure no extra spaces or newlines
- Verify the secret name is exactly `GITGUARDIAN_API_KEY`

### 7.2. Error: "Rate limit exceeded"

- You've exceeded 10,000 scans/month on free tier
- Upgrade to paid plan or wait for monthly reset

### 7.3. Workflow doesn't run

- Ensure the secret is set at the **repository** level (not environment level)
- Check workflow logs for authentication errors

## 8. Token Management Dashboard

**View your tokens:** [GitGuardian Token Management](https://dashboard.gitguardian.com/workspace/settings/api)

**Actions available:**

- View token creation date
- See last used timestamp
- Revoke tokens
- Create new tokens

## 9. Support

- Documentation: [GitGuardian Docs](https://docs.gitguardian.com)
- Community: [GitGuardian Community](https://community.gitguardian.com)
- Email: support@gitguardian.com
