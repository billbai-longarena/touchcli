# CI/CD Pipeline Setup - TouchCLI

Complete automated testing and deployment pipeline for TouchCLI.

---

## Overview

This CI/CD setup provides:

1. **Automated Testing** - Run tests on every PR and push
2. **Pre-commit Hooks** - Lint before committing
3. **Pre-push Hooks** - Full test suite before pushing
4. **Staging Deployment** - Auto-deploy to staging on merge to develop
5. **Coverage Reporting** - Upload to Codecov for tracking
6. **Build Verification** - Ensure builds pass

---

## GitHub Actions Workflows

### `.github/workflows/test.yml`

**Triggers:**
- On `push` to `main` or `develop` branches
- On `pull_request` to `main` or `develop` branches

**What it does:**
1. Spins up PostgreSQL 15 and Redis 7 services
2. Runs frontend linting (eslint if available)
3. Runs frontend unit tests (Vitest)
4. Runs frontend unit test coverage
5. Installs and runs Playwright E2E tests
6. Runs backend linting (flake8)
7. Runs backend pytest suite with coverage
8. Uploads coverage reports to Codecov
9. Provides summary report

**Test Matrix:**
- Node.js 18.x
- Python 3.11

**Services:**
- PostgreSQL 15 (port 5432, password: test_password)
- Redis 7 (port 6379)

**Coverage:**
- Frontend unit tests → Codecov
- Backend unit tests → Codecov
- Combined coverage tracking

### `.github/workflows/deploy.yml`

**Triggers:**
- On `push` to `develop` branch
- On `workflow_run` after successful `test.yml`

**What it does:**
1. Checks out develop branch
2. Builds frontend (with staging environment variables)
3. Builds backend
4. Runs database migrations (alembic)
5. Builds Docker images (optional)
6. Provides deployment summary
7. Notifies Slack (if webhook configured)

**Status:**
- Creates summary in GitHub Actions UI
- Optional Slack notification on deployment

---

## Pre-commit Hooks (Husky)

### Setup

```bash
# Install dependencies (if not already done)
npm install

# Run setup script
.husky/setup.sh

# OR manually initialize
npx husky install
```

### Hook 1: `.husky/pre-commit`

**Triggers:** Before every `git commit`

**What it does:**
1. Gets list of staged files
2. If frontend files staged:
   - Runs ESLint on staged files with auto-fix
   - Runs Prettier on staged files
   - Re-stages fixed files
3. If backend files staged:
   - Checks Python syntax (py_compile)
   - Runs flake8 for style violations
   - Runs Black formatter

**Exit behavior:**
- ✅ Passes if no errors
- ❌ Fails if ESLint or syntax errors found
- ⚠️ Warns on style issues but continues

**To bypass:**
```bash
git commit --no-verify
```

### Hook 2: `.husky/pre-push`

**Triggers:** Before `git push`

**What it does:**
1. Runs frontend test suite: `npm run test:run`
2. Runs backend test suite: `pytest tests/`

**Exit behavior:**
- ✅ Passes if all tests pass
- ❌ Fails if any tests fail
- Prevents pushing broken code

**To bypass:**
```bash
git push --no-verify
```

---

## Environment Variables

### GitHub Secrets

Configure these in your GitHub repository settings:

```yaml
STAGING_API_URL           # Base URL for staging API
STAGING_WS_URL            # WebSocket URL for staging
STAGING_DATABASE_URL      # PostgreSQL connection string
SLACK_WEBHOOK_URL         # Optional: Slack notifications
```

### Local `.env` Files

Frontend (optional - defaults in vite.config.ts):
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8080/ws
```

Backend:
```
DATABASE_URL=postgresql://user:password@localhost:5432/touchcli_db
REDIS_URL=redis://localhost:6379
```

---

## Test Coverage

### Frontend (80%+ required)

```bash
npm --prefix frontend run test:coverage
```

Coverage report: `frontend/coverage/`

Requirements:
- Lines: 80%
- Functions: 80%
- Branches: 75%
- Statements: 80%

### Backend

```bash
cd backend/python
pytest tests/ --cov=agent_service --cov-report=html
```

Coverage report: `backend/python/htmlcov/`

---

## Codecov Integration

Coverage reports are automatically uploaded to Codecov.

**Setup:**
1. Visit https://codecov.io
2. Connect your GitHub repo
3. Coverage reports auto-upload from CI

**Features:**
- Track coverage over time
- Per-PR coverage reports
- Coverage badges for README

---

## Local Development Workflow

### Initial Setup

```bash
# Clone repo
git clone <repo>
cd touchcli

# Install dependencies
npm install
pip install -r backend/python/requirements.txt

# Setup Husky hooks
.husky/setup.sh
```

### Before Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, run tests locally
npm --prefix frontend run test:run
cd backend/python && pytest tests/
```

### Committing

```bash
# Stage changes
git add .

# Commit (pre-commit hook will lint automatically)
git commit -m "feat: add new feature"

# If linting fails:
# 1. Fix errors shown in hook output
# 2. Re-run commit (auto-fixed files are re-staged)
# 3. Commit again
```

### Pushing

```bash
# Push to remote (pre-push hook runs all tests)
git push origin feature/my-feature

# If tests fail:
# 1. Fix failing tests
# 2. Push again
# 3. GitHub Actions will also run on PR

# To skip hooks (not recommended):
git push --no-verify
```

### Pull Request

1. Push feature branch to GitHub
2. Open PR against `develop` branch
3. GitHub Actions tests run automatically
4. Codecov reports coverage changes
5. PR must pass all checks before merge
6. Merge to `develop` triggers auto-deployment

---

## Troubleshooting

### Husky hooks not running

```bash
# Reinstall husky
npm install husky --save-dev

# Initialize
npx husky install

# Verify hooks are executable
chmod +x .husky/pre-commit .husky/pre-push
```

### ESLint not found

```bash
# Install in frontend
npm --prefix frontend install eslint eslint-config-react-app --save-dev
```

### Tests fail locally but pass in CI

1. Check Node/Python versions match CI matrix
2. Ensure test databases are running:
   ```bash
   # PostgreSQL
   psql -U postgres -c "CREATE DATABASE test_db;"

   # Redis
   redis-server
   ```
3. Clear any cache: `npm ci` (instead of `npm install`)

### Deployment stuck

1. Check GitHub Actions logs
2. Verify environment secrets are set correctly
3. Check database migration compatibility

---

## Performance Tips

### Speed up CI

1. **Use cache** - Dependencies cached between runs
2. **Parallel jobs** - Frontend and backend tests could be parallel (split into separate jobs if needed)
3. **Skip optional checks** - Use `continue-on-error: true` for non-critical checks

### Speed up local development

1. **Run only affected tests** - `npm --prefix frontend run test:run -- --watch`
2. **Skip E2E tests** - Use `npm --prefix frontend run test:run` (unit tests only)
3. **Use npm ci** - Faster than npm install for CI

---

## Branch Strategy

```
main (production)
  ↑
  └── develop (staging) ← Merge approved PRs here
       ↑
       └── feature/* (feature branches)
       └── bugfix/* (bug fix branches)
       └── hotfix/* (hotfixes to main)
```

**Rules:**
1. `main` is production-ready (manually deployed)
2. `develop` is staging (auto-deployed via CI/CD)
3. All feature branches merge to `develop` via PR
4. PR must pass all CI checks before merge

---

## Monitoring

### GitHub Actions Dashboard

https://github.com/your-repo/actions

Shows:
- Test results for each run
- Build status for each branch
- Workflow execution logs

### Codecov Dashboard

https://app.codecov.io/gh/your-repo

Shows:
- Coverage trends over time
- Per-file coverage breakdown
- PR impact on coverage

### Slack Notifications (Optional)

If configured, get Slack messages for:
- PR checks passed/failed
- Deployment status
- Coverage changes

---

## Security

### Secrets Management

**GitHub Secrets** are encrypted and never logged.

Never commit:
- Database passwords
- API keys
- JWT secrets
- Private tokens

### Pre-commit Prevention

Pre-commit hook prevents committing if:
- ESLint finds security issues
- Python syntax is invalid
- Coverage drops below threshold (optional)

---

## FAQ

**Q: Can I push without running tests?**
A: Use `git push --no-verify` but not recommended.

**Q: Why did my commit fail?**
A: Pre-commit hook caught linting errors. Fix and recommit.

**Q: How do I test locally like CI does?**
A: Run:
```bash
npm --prefix frontend run test:run
cd backend/python && pytest tests/
```

**Q: Can I skip E2E tests in CI?**
A: Yes, remove the E2E test step from `.github/workflows/test.yml`

**Q: How often are deployments?**
A: Every merge to `develop` triggers deployment to staging.

---

## Maintenance

### Update CI dependencies

```bash
# Update GitHub Actions (when new versions available)
# Edit .github/workflows/*.yml

# Update local hooks
npm install husky@latest
```

### Disable a hook temporarily

```bash
# Remove permission
chmod -x .husky/pre-commit

# Re-enable
chmod +x .husky/pre-commit
```

### Monitor CI cost

GitHub provides 2000 free CI minutes per month.
Optimize if getting close to limit.
