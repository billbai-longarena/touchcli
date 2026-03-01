# Task 3.6: Testing & CI/CD Setup Plan

**Status**: Ready to Start
**Duration Estimate**: 5-7 days
**Scope**: Frontend unit/E2E tests, backend API tests, CI/CD pipeline

---

## 📋 Scope & Objectives

### Primary Goals
1. ✅ **Frontend Unit Tests** - Test React components (modals, pages, hooks)
2. ✅ **Frontend E2E Tests** - Test complete user workflows (create conversation, etc.)
3. ✅ **Backend API Tests** - Test CRUD endpoints with edge cases
4. ✅ **CI/CD Pipeline** - GitHub Actions for automated build/test/deploy
5. ✅ **Quality Gates** - Pre-commit hooks, coverage thresholds
6. ✅ **Build Verification** - Ensure builds pass before merge

### Success Criteria
- Frontend unit test coverage ≥ 80% for modals and core components
- All user workflows covered by E2E tests (happy path + error cases)
- Backend API tests pass with 100% endpoint coverage
- GitHub Actions pipeline runs on every PR and merge
- Pre-commit hooks enforce linting and basic tests
- Zero test failures on main branch

---

## 🏗️ Implementation Plan

### Phase 1: Frontend Testing Setup (Days 1-2)

#### 1.1 Install Vitest + Testing Dependencies
```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom
```

**Files to create/modify**:
- `frontend/vitest.config.ts` - Vitest configuration
- `frontend/src/setup.ts` - Test environment setup
- `frontend/package.json` - Add test scripts

**Test Scripts**:
```json
{
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --coverage",
  "test:run": "vitest run"
}
```

#### 1.2 Unit Tests for Core Components (Coverage: 80%+)

**Tests to write** (~20-30 tests, 500 lines):

1. **Modal Components** (each ~5 tests):
   - `CreateConversationModal.test.tsx` - Form submission, validation, callbacks
   - `CreateOpportunityModal.test.tsx` - Form validation, amount input, stage selection
   - `CreateCustomerModal.test.tsx` - Email validation, required fields
   - `OpportunityDetailModal.test.tsx` - Display data, delete confirmation, actions

2. **Page Components** (each ~5-8 tests):
   - `CustomersPage.test.tsx` - Search, selection, modal opening
   - `OpportunitiesPage.test.tsx` - Filtering, sorting, query params

3. **Hooks & Store** (~5-10 tests):
   - `useAuth.test.ts` - Login/logout, token persistence
   - `conversationStore.test.ts` - State mutations, async actions

**Test Template**:
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CreateOpportunityModal } from '../CreateOpportunityModal';

describe('CreateOpportunityModal', () => {
  it('should display form fields when open', () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByLabelText(/customer/i)).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);
    fireEvent.click(screen.getByText(/create/i));
    expect(await screen.findByText(/required/i)).toBeInTheDocument();
  });

  it('should call onClose on success', async () => {
    const onClose = vi.fn();
    const { getByText } = render(
      <CreateOpportunityModal isOpen={true} onClose={onClose} />
    );
    // Fill form, submit...
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });
});
```

**Coverage Goals**:
- Components: 80% line coverage
- Branches: 75% (conditional logic)
- Functions: 80%
- Lines: 80%

---

### Phase 2: Frontend E2E Testing (Days 2-3)

#### 2.1 Install Playwright
```bash
npm install -D @playwright/test
npx playwright install
```

**Files to create**:
- `frontend/playwright.config.ts` - Configuration
- `frontend/tests/e2e/` - E2E test directory
- `frontend/.env.test` - Test environment variables

#### 2.2 E2E Test Scenarios (~10-15 tests, 800 lines)

**Test Coverage**:

1. **Authentication Flow**:
   - `login.spec.ts` - Login with demo user, redirect to dashboard
   - `protected-routes.spec.ts` - Verify protection, redirect to login

2. **Customer Management**:
   - `customers.spec.ts` - List, search, view detail, open conversation modal
   - Create customer via "+" button, see in list
   - Navigate to opportunities from customer

3. **Opportunity Management**:
   - `opportunities.spec.ts` - List, filter, sort, view detail
   - Create opportunity from modal, see in list
   - Delete/update opportunity from detail modal
   - Filtering by customer query param

4. **Conversation Flow**:
   - `conversations.spec.ts` - Start conversation from customer
   - Send message, see optimistic update + confirmation
   - Error handling (failed messages show retry button)

5. **Cross-Page Navigation**:
   - `navigation.spec.ts` - Customer → Conversation, Customer → Opportunities
   - Verify query params persist filters

**Test Template**:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Customer Management', () => {
  test('should create and view customer', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="userId"]', 'demo-user-id');
    await page.click('button:has-text("Login")');

    // Navigate to customers
    await page.click('text=Customers');
    expect(page).toHaveURL('/customers');

    // Create customer
    await page.click('text="+"');
    await page.fill('[name="name"]', 'Test Corp');
    await page.fill('[name="email"]', 'test@corp.com');
    await page.click('button:has-text("Create Customer")');

    // Verify in list
    await expect(page.locator('text=Test Corp')).toBeVisible();
  });

  test('should navigate to opportunities from customer', async ({ page }) => {
    // ... setup ...
    await page.click('text=Test Corp');
    await page.click('button:has-text("View Opportunities")');
    expect(page).toHaveURL(/\/opportunities\?customer=/);
  });
});
```

---

### Phase 3: Backend API Tests (Day 3-4)

#### 3.1 Expand pytest Test Suite

**Current State**: `tests/test_integration.py` exists

**Add Tests For** (~30-50 tests):

1. **Authentication Endpoints**:
   - `test_login` - Valid credentials, invalid credentials, token generation
   - `test_token_refresh` - Token expiry, refresh workflow
   - `test_protected_routes` - Unauthorized access returns 401

2. **Conversation CRUD**:
   - `test_create_conversation` - Valid input, missing fields, invalid customer_id
   - `test_list_conversations` - Pagination, filtering, sorting
   - `test_get_conversation` - Existing/non-existing ID
   - `test_update_conversation` - Status changes
   - `test_delete_conversation` - Cascading message deletion

3. **Opportunity CRUD**:
   - `test_create_opportunity` - Valid input, validation, amount > 0
   - `test_list_opportunities` - Filter by stage, customer, sorting
   - `test_update_opportunity` - Stage progression rules
   - `test_delete_opportunity` - Authorization checks

4. **Customer CRUD**:
   - `test_create_customer` - Email validation, unique constraint
   - `test_list_customers` - Pagination, search
   - `test_get_customer` - With related conversations/opportunities

5. **Message Operations**:
   - `test_send_message` - Create, optional update
   - `test_message_status_updates` - sending → sent → failed
   - `test_message_ordering` - Correct chronological order

6. **Error Handling**:
   - Invalid JSON payloads
   - Missing required fields
   - Invalid data types
   - Authorization failures
   - Resource not found (404)
   - Conflict errors (409)

**Test Structure**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_opportunity(client: AsyncClient, auth_headers: dict):
    """Test successful opportunity creation"""
    response = await client.post(
        '/opportunities',
        json={
            'customer_id': 'test-customer-id',
            'title': 'Test Deal',
            'amount': 50000,
            'stage': 'proposal'
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()['title'] == 'Test Deal'
    assert response.json()['amount'] == 50000

@pytest.mark.asyncio
async def test_create_opportunity_missing_amount(client: AsyncClient, auth_headers: dict):
    """Test validation error for missing amount"""
    response = await client.post(
        '/opportunities',
        json={
            'customer_id': 'test-customer-id',
            'title': 'Test Deal',
            'stage': 'proposal'
            # amount missing
        },
        headers=auth_headers
    )
    assert response.status_code == 422
    assert 'amount' in response.json()['detail'][0]['loc']

@pytest.mark.asyncio
async def test_opportunity_authorization(client: AsyncClient):
    """Test unauthorized access to create opportunity"""
    response = await client.post(
        '/opportunities',
        json={
            'customer_id': 'test-customer-id',
            'title': 'Test Deal',
            'amount': 50000,
            'stage': 'proposal'
        }
        # no auth headers
    )
    assert response.status_code == 401
```

---

### Phase 4: GitHub Actions CI/CD Pipeline (Days 4-5)

#### 4.1 Create `.github/workflows/` Pipeline

**Files to create**:

1. **`.github/workflows/test.yml`** - Run all tests
```yaml
name: Test

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Lint
        run: cd frontend && npm run lint

      - name: Unit tests
        run: cd frontend && npm run test:run

      - name: E2E tests
        run: cd frontend && npm run test:e2e

      - name: Build
        run: cd frontend && npm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json

  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: cd backend/python && pip install -r requirements.txt

      - name: Lint
        run: cd backend/python && pylint agent_service/

      - name: Tests
        run: cd backend/python && pytest -v --cov=agent_service tests/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/python/.coverage
```

2. **`.github/workflows/deploy.yml`** - Deploy on successful tests
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Build frontend
        run: cd frontend && npm install && npm run build

      - name: Deploy to staging
        run: |
          # Deployment script (varies by platform)
          echo "Deploying to staging environment..."
```

#### 4.2 Pre-commit Hooks

**File**: `.husky/pre-commit`
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Frontend checks
cd frontend
npm run lint
npm run test:run

# Backend checks
cd ../backend/python
pylint agent_service/
pytest -v --cov=agent_service tests/
```

---

### Phase 5: Test Configuration Files (Day 5)

#### 5.1 Vitest Configuration
**File**: `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/main.tsx',
      ],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### 5.2 Playwright Configuration
**File**: `frontend/playwright.config.ts`
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['json', { outputFile: 'test-results.json' }]],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
});
```

---

## 📊 Deliverables Checklist

### Frontend Testing
- [ ] Vitest + dependencies installed and configured
- [ ] Unit tests written for 6 modal components (~120 lines each = 720 lines)
- [ ] Unit tests written for 2 page components (~150 lines each = 300 lines)
- [ ] Unit tests written for hooks/store (~200 lines)
- [ ] Test coverage: 80%+ for modals and pages
- [ ] E2E tests for auth, customer CRUD, opportunity CRUD, messaging (~800 lines)
- [ ] E2E test scripts in package.json

### Backend Testing
- [ ] Pytest test suite expanded to cover all CRUD endpoints
- [ ] Authorization tests (401/403 errors)
- [ ] Validation tests (required fields, data types)
- [ ] Error handling tests (404, 422, conflict errors)
- [ ] Database transaction tests (rollback on error)
- [ ] ~50 new test cases, ~800 lines

### CI/CD Infrastructure
- [ ] `.github/workflows/test.yml` - Runs all tests on push/PR
- [ ] `.github/workflows/deploy.yml` - Deploys on main merge
- [ ] `.husky/` pre-commit hooks configured
- [ ] Coverage reporting integrated (Codecov)
- [ ] Test result reporting (HTML, JSON)

### Quality Gates
- [ ] 80% test coverage enforced
- [ ] Linting passes on CI
- [ ] All tests pass before merge
- [ ] Build succeeds on all platforms

---

## 🎯 Execution Order

**Day 1**: Frontend testing setup + vitest config + unit test scaffold
**Day 2**: Write modal unit tests (~6 components × 5 tests = 30 tests)
**Day 3**: Write page unit tests + E2E setup + first E2E tests
**Day 3-4**: Backend API test expansion (~50 tests)
**Day 4-5**: GitHub Actions pipeline + pre-commit hooks + coverage setup
**Day 5**: Polish, coverage reporting, final verification

---

## 📈 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Frontend unit test coverage | 80%+ | 0% |
| Frontend E2E test count | 15+ | 0 |
| Backend API test count | 50+ | ~15 |
| CI/CD pipelines active | 2 (test + deploy) | 0 |
| Pre-commit hooks blocking | Yes | No |
| Linting enforcement | Automated | Manual |
| Build verification | Gated on PR | None |

---

## 🔧 Commands Reference

```bash
# Frontend
cd frontend
npm run test              # Watch mode
npm run test:run         # Single run
npm run test:ui          # UI dashboard
npm run test:coverage    # Coverage report
npm run test:e2e         # E2E tests
npm run lint             # ESLint check

# Backend
cd backend/python
pytest -v                # Run all tests
pytest -v --cov         # With coverage
pytest -v -k "test_create"  # Filter tests

# Git hooks
husky install            # Setup pre-commit hooks
husky uninstall          # Remove hooks
```

---

## 📝 Notes

- **Parallel Execution**: Frontend and backend tests run in parallel in CI
- **Coverage Thresholds**: Enforced at 80% - lower coverage blocks merge
- **E2E Test Data**: Use fixtures/factories for consistent test data
- **Flaky Tests**: Retry failed tests 1-2 times in CI
- **Local vs CI**: E2E tests use `localhost:5173` locally, GitHub hosted runner in CI
- **Database**: Use test database (separate from dev) with transaction rollback

Generated: 2026-03-02
Task: 3.6 Testing & CI/CD
Duration: 5-7 days
