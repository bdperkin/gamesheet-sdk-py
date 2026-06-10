# 🚀 Quick Start: API Keys Setup

## TL;DR - What You Need

### Required (Must Have)

- ✅ **GitGuardian API Key** - For secret scanning

### Optional (Nice to Have)

- ⭕ **Semgrep App Token** - For cloud dashboard (workflow works without it!)

______________________________________________________________________

## ⚡ 5-Minute Setup (Minimum Required)

### Step 1: GitGuardian API Key (REQUIRED)

**Quick steps:**

1. Go to: [GitGuardian Sign Up](https://dashboard.gitguardian.com/auth/signup)

2. Click **"Sign up with GitHub"** (fastest)

3. After login, go to: [GitGuardian API Settings](https://dashboard.gitguardian.com/workspace/settings/api)

4. Click **"Create token"**

   - Name: `GitHub Actions - gamesheet-sdk-py`
   - Scope: Select **"Scan"**
   - Expiration: **90 days** (recommended)

5. Click **"Create"** and **COPY THE TOKEN** (you won't see it again!)

6. Add to GitHub:

   ```bash
   gh secret set GITGUARDIAN_API_KEY
   # Paste the token when prompted (starts with ggapi-)
   ```

7. Verify:

   ```bash
   gh secret list | grep GITGUARDIAN
   ```

**Done!** ✅ Your GitGuardian workflow is ready.

______________________________________________________________________

## ⏭️ Skip Semgrep Token (Recommended for Now)

**The Semgrep workflow works WITHOUT a token!**

You can skip this entirely and come back later if needed.

**Why it's optional:**

- Semgrep runs locally in the workflow (no token needed)
- Results upload to GitHub Security tab (without token)
- Only needed for Semgrep Cloud dashboard features

**When to add it:**

- You manage multiple repositories
- You want a centralized cloud dashboard
- You need team collaboration features

______________________________________________________________________

## 📋 Verification Checklist

After setup, verify:

```bash
# Check secrets are configured
gh secret list

# Should show:
# GITGUARDIAN_API_KEY  Updated YYYY-MM-DD

# Optional (only if you added it):
# SEMGREP_APP_TOKEN    Updated YYYY-MM-DD
```

**Minimum Required Secrets:**

- ✅ `GITGUARDIAN_API_KEY` - Must be present

**Optional Secrets:**

- ⭕ `SEMGREP_APP_TOKEN` - Can skip

______________________________________________________________________

## 🎯 Ready to Deploy?

If you have `GITGUARDIAN_API_KEY` configured, you're ready!

```bash
# Commit the workflow files
git add .github/workflows/{semgrep,workflow-linter,osv-scanner,gitguardian}.yml
git add .github/SECURITY_SCANNING.md

# Commit
git commit -m "feat(security): implement comprehensive security scanning pipeline"

# Push (this will trigger the workflows)
git push origin main
```

After push, check results:

- GitHub → **Security** → **Code scanning**

______________________________________________________________________

## 🆘 Common Issues

### "GitGuardian workflow failed - authentication error"

**Fix:** Double-check you set `GITGUARDIAN_API_KEY` (exact name, case-sensitive)

```bash
# Check if it exists
gh secret list | grep GITGUARDIAN

# If missing, add it
gh secret set GITGUARDIAN_API_KEY
```

### "Semgrep workflow failed"

**Fix:** Semgrep doesn't need a token! Check the actual error message.

If it says "missing SEMGREP_APP_TOKEN":

- This is just a warning, not an error
- Workflow still runs and scans successfully
- Ignore or add the token (optional)

### "How do I know if it's working?"

**Check workflow runs:**

```bash
gh run list --limit 5

# Or view in browser
gh run view --web
```

**Check security findings:**

- Navigate to: Security → Code scanning
- Should see results from: Semgrep, OSV Scanner, CodeQL

______________________________________________________________________

## 📞 Need Help?

**GitGuardian Support:**

- Docs: [GitGuardian Documentation](https://docs.gitguardian.com)
- Email: support@gitguardian.com

**Semgrep Support:**

- Docs: [Semgrep Documentation](https://semgrep.dev/docs)
- Community Slack: [r2c Slack](https://r2c.dev/slack)

**Workflow Issues:**

- Check `.github/SECURITY_SCANNING.md` for troubleshooting
- Review workflow logs: `gh run view <run-id> --log`

______________________________________________________________________

## 🎉 Summary

**Absolute minimum to get started:**

1. Create GitGuardian account → Generate API key → Add to GitHub secrets
2. Commit workflows and push
3. Check Security tab for results

**Time required:** ~5 minutes

**Cost:** $0 (all free tiers)

That's it! The security pipeline will start scanning on every PR and push to main.
