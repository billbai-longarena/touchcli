# Developer Setup Guide - TouchCLI

Complete setup instructions for local development with all testing and CI/CD hooks.

---

## Prerequisites

### Required

- **Node.js 18+** - https://nodejs.org/
- **Python 3.11+** - https://www.python.org/
- **Git** - https://git-scm.com/
- **npm** - Comes with Node.js

### Optional but Recommended

- **Docker** - For running PostgreSQL/Redis in containers
- **PostgreSQL 15** - For local backend development
- **Redis 7** - For async tasks
- **VS Code** - https://code.visualstudio.com/

---

## Quick Start (5 minutes)

### 1. Clone Repository

```bash
git clone <repo-url>
cd touchcli
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Install Backend Dependencies

```bash
cd backend/python
pip install -r requirements.txt
cd ../..
```

### 4. Setup Husky Hooks

```bash
.husky/setup.sh
```

### 5. Start Development

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend (if needed)
cd backend/python
python agent_service/main.py
```

---

## Detailed Setup

### Step 1: Node.js and npm

#### macOS (with Homebrew)

```bash
brew install node@18
node --version  # Should be 18.x or higher
npm --version   # Should be 9.x or higher
```

#### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Windows

Download from https://nodejs.org/ and run installer.

### Step 2: Python

#### macOS (with Homebrew)

```bash
brew install python@3.11
python3 --version  # Should be 3.11 or higher
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv
```

#### Windows

Download from https://www.python.org/ and run installer.

### Step 3: Clone Repository

```bash
git clone https://github.com/your-username/touchcli.git
cd touchcli
```

### Step 4: Frontend Setup

```bash
# Install dependencies
npm install

# Verify installation
npm --version
node --version

# Setup Husky hooks for git
npx husky install

# Verify Husky setup
cat .husky/pre-commit  # Should show hook content
```

**Frontend Structure:**
```
frontend/
├── src/
│   ├── pages/           # Page components
│   ├── components/      # Reusable components
│   ├── store/          # Zustand stores
│   ├── api/            # API client
│   ├── styles/         # CSS files
│   └── App.tsx         # Root component
├── tests/
│   ├── unit/           # Unit tests (*.test.tsx)
│   └── e2e/            # E2E tests (*.spec.ts)
├── vitest.config.ts    # Unit test config
├── playwright.config.ts # E2E test config
└── package.json        # Dependencies and scripts
```

### Step 5: Backend Setup

```bash
# Navigate to backend
cd backend/python

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m agent_service.main --version  # Or just import to verify

# Return to root
cd ../..
```

**Backend Structure:**
```
backend/python/
├── agent_service/
│   ├── main.py         # FastAPI app
│   ├── models.py       # SQLAlchemy models
│   ├── schemas.py      # Pydantic schemas
│   ├── db.py          # Database setup
│   ├── auth.py        # Authentication
│   └── ...
├── tests/
│   ├── test_integration.py  # All tests
│   └── conftest.py          # Fixtures
├── migrations/         # Alembic migrations
├── requirements.txt    # Python dependencies
└── setup.py
```

### Step 6: Database Setup

#### Option A: Docker (Recommended)

```bash
# Start PostgreSQL
docker run -d --name touchcli-postgres \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=touchcli_dev \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d --name touchcli-redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify
docker ps | grep touchcli
```

#### Option B: Local Installation

**macOS:**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

**Linux (Ubuntu):**
```bash
sudo apt-get install postgresql-15 redis-server
sudo systemctl start postgresql
sudo systemctl start redis-server
```

#### Create Development Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE touchcli_dev;
CREATE USER touchcli_user WITH PASSWORD 'dev_password';
ALTER ROLE touchcli_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE touchcli_dev TO touchcli_user;
\q
```

#### Run Migrations

```bash
cd backend/python
export DATABASE_URL=postgresql://touchcli_user:dev_password@localhost/touchcli_dev
alembic upgrade head
cd ../..
```

### Step 7: Environment Variables

#### Frontend `.env`

Create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8080/ws
```

#### Backend `.env`

Create `backend/python/.env`:
```
DATABASE_URL=postgresql://touchcli_user:dev_password@localhost/touchcli_dev
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Running the Application

### Start All Services

**Terminal 1: Frontend (port 5173)**
```bash
cd frontend
npm run dev
```

**Terminal 2: Backend (port 8000)**
```bash
cd backend/python
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
python -m uvicorn agent_service.main:app --reload
```

**Terminal 3: WebSocket Gateway (port 8080)**
```bash
# Usually runs as part of backend or separate service
# Depends on your architecture
```

### Verify Everything Works

```bash
# Frontend is running
curl http://localhost:5173

# Backend is running
curl http://localhost:8000/health

# Should see: {"status":"ok",...}
```

---

## Testing

### Run All Tests

```bash
# Frontend unit tests
npm --prefix frontend run test:run

# Frontend E2E tests (requires frontend and backend running)
npm --prefix frontend run test:e2e

# Backend tests
cd backend/python
pytest tests/ -v
```

### Run Tests in Watch Mode

```bash
# Frontend (auto-rerun on file change)
npm --prefix frontend run test

# Frontend UI dashboard
npm --prefix frontend run test:ui

# Backend (auto-rerun)
cd backend/python
pytest tests/ --watch  # Requires pytest-watch: pip install pytest-watch
```

### Generate Coverage Reports

```bash
# Frontend coverage
npm --prefix frontend run test:coverage
# Report in: frontend/coverage/

# Backend coverage
cd backend/python
pytest tests/ --cov=agent_service --cov-report=html
# Report in: backend/python/htmlcov/
```

### Run Specific Tests

```bash
# Frontend: Run single test file
npm --prefix frontend run test:run -- CreateCustomerModal.test.tsx

# Frontend: Run tests matching pattern
npm --prefix frontend run test:run -- --grep "should validate"

# Backend: Run single test file
cd backend/python
pytest tests/test_integration.py::test_login -v

# Backend: Run tests matching pattern
pytest tests/ -k "test_create" -v
```

---

## Git Workflow with Hooks

### Making Changes

```bash
# Create feature branch
git checkout -b feature/my-awesome-feature

# Make changes
# ... edit files ...

# Check what changed
git status
git diff

# Stage changes
git add .
git add src/  # Or add specific files

# Commit (pre-commit hook runs linting)
git commit -m "feat: add awesome feature"

# If linting fails:
# 1. Read error messages
# 2. Fix issues
# 3. Re-run commit (auto-fixed files are re-staged)
# 4. Commit again

# Push (pre-push hook runs tests)
git push origin feature/my-awesome-feature

# If tests fail:
# 1. Fix failing tests
# 2. Push again
```

### Bypass Hooks (If Needed)

```bash
# Skip pre-commit hook (not recommended)
git commit --no-verify

# Skip pre-push hook (not recommended)
git push --no-verify

# Skip both
git commit --no-verify && git push --no-verify
```

### Creating Pull Request

```bash
# After pushing, visit GitHub and:
# 1. Click "Create Pull Request"
# 2. Select base: develop
# 3. Add description
# 4. Submit PR

# GitHub Actions will:
# - Run all tests
# - Check code coverage
# - Run linters
# - Provide feedback

# After approval, merge to develop
# - This triggers auto-deployment to staging
```

---

## Common Issues

### Problem: `npm install` fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Problem: Hooks not running

**Solution:**
```bash
# Reinstall Husky
npm install husky --save-dev
npx husky install

# Make hooks executable
chmod +x .husky/pre-commit .husky/pre-push
```

### Problem: `pytest` not found

**Solution:**
```bash
# Activate virtual environment
cd backend/python
source venv/bin/activate

# Install pytest
pip install pytest

# Try again
pytest tests/ -v
```

### Problem: PostgreSQL connection refused

**Solution:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"

# If not running, start it:
# macOS: brew services start postgresql@15
# Linux: sudo systemctl start postgresql
# Docker: docker start touchcli-postgres

# Check DATABASE_URL is correct
echo $DATABASE_URL
# Should be: postgresql://user:password@localhost:5432/db_name
```

### Problem: Tests pass locally but fail in CI

**Solution:**
1. Check Node/Python versions: `node --version`, `python --version`
2. Check services are running: PostgreSQL, Redis
3. Clear cache: `npm ci` instead of `npm install`
4. Check environment variables in CI secrets

---

## IDE Setup

### VS Code Extensions (Recommended)

```json
{
  "extensions": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "GitHub.copilot"
  ]
}
```

### VS Code Settings

Create `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true
}
```

---

## Performance Tips

### Speed Up Tests

```bash
# Run only affected files
npm --prefix frontend run test -- --changed

# Run specific test suites
npm --prefix frontend run test:run -- components/

# Skip coverage (faster)
npm --prefix frontend run test:run  # No --coverage flag
```

### Speed Up Development

```bash
# Use Vite dev server (fast HMR)
npm --prefix frontend run dev

# Use Python hot reload
python -m uvicorn agent_service.main:app --reload
```

### Reduce Bundle Size

```bash
# Build frontend for production
npm --prefix frontend run build

# Check bundle size
npm --prefix frontend run build -- --analyze
```

---

## Useful Commands

```bash
# Frontend
npm run dev           # Start dev server
npm run build         # Build for production
npm run test          # Run tests (watch)
npm run test:run      # Run tests (CI mode)
npm run test:e2e      # Run E2E tests
npm run lint          # Run ESLint

# Backend
python -m agent_service.main:app --reload  # Start dev server
pytest tests/ -v                           # Run tests
pytest tests/ --cov                        # Run with coverage
alembic upgrade head                       # Run migrations

# Git
git status            # See changes
git diff              # See detailed changes
git log               # See commit history
git branch -a         # See all branches
```

---

## Getting Help

### Documentation

- **Frontend Architecture**: See `frontend/README.md`
- **Backend Architecture**: See `backend/python/README.md`
- **CI/CD Setup**: See `CI_CD_SETUP.md`
- **Project Plan**: See `PHASE_3_PLAN.md`

### Debugging

```bash
# Frontend: Check browser console (F12)
# Frontend: Check Vite server output
# Backend: Check server logs
# Database: Use psql or pgAdmin
# Redis: Use redis-cli
```

### Reporting Issues

1. Reproduce the issue
2. Note down:
   - Environment (OS, Node version, Python version)
   - Steps to reproduce
   - Expected vs actual behavior
3. Share logs/screenshots
4. Create GitHub issue with details

---

## Next Steps

1. ✅ Complete this setup
2. 📖 Read `PHASE_3_PLAN.md` for project overview
3. 🔍 Review code in `src/` directories
4. 💬 Ask questions in discussions
5. 🚀 Start developing!

Happy coding! 🎉
