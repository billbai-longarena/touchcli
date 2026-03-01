# Phase 3.6 Plan: Testing & CI/CD

**Status**: Scout Reconnaissance
**Date**: 2026-03-02
**Previous Phase**: 3.5 Complete (2,380+ lines, 100% verified)
**Progress**: Phase 3 at 71% (5/7 tasks), ready for test foundation

---

## Overview

**Phase 3.6: Testing & CI/CD Infrastructure**
- Set up comprehensive testing framework (unit + integration + E2E)
- Build GitHub Actions CI/CD pipeline
- Establish test coverage goals
- Add pre-commit hooks and linting automation
- Create deployment readiness verification

**Estimated Effort**: 5-7 days
**Complexity**: High (testing patterns + CI/CD infrastructure)
**Blocker Risk**: Low (no architectural changes needed)

---

## Current State Assessment

### ✅ What Exists

**Frontend Codebase** (19 TypeScript files):
- 5 pages (Login, Dashboard, Conversations, CustomersPage, OpportunitiesPage)
- 6 modals/forms (CreateConversationModal, CreateOpportunityModal, CreateCustomerModal, OpportunityDetailModal, MessageInput, etc.)
- 3 components (ConversationList, MessageList, ProtectedRoute)
- 2 stores (authStore, conversationStore) using Zustand
- 2 API modules (client.ts, websocket.ts)
- 1 hook (useAuth.ts)

**Backend Codebase** (Python FastAPI):
- Pytest infrastructure already in place
- pytest-asyncio for async tests
- pytest-cov for coverage
- conftest.py fixtures set up
- test_integration.py with basic tests
- GitHub Actions workflow for performance SLA checks (S-005)

**Development Setup**:
- ✅ ESLint configured for frontend
- ✅ TypeScript strict mode enabled
- ✅ Vite build pipeline working
- ✅ Docker compose for services
- ✅ GitHub Actions infrastructure ready

### ❌ What's Missing

**Frontend Testing**:
- ❌ No unit test framework (need Jest/Vitest)
- ❌ No component test utilities (need React Testing Library)
- ❌ No E2E tests (need Playwright/Cypress)
- ❌ No test scripts in package.json
- ❌ No test configuration files

**CI/CD Pipeline**:
- ❌ No frontend build/test workflow
- ❌ No code coverage reporting
- ❌ No pull request checks
- ❌ No pre-commit hooks
- ❌ No deployment automation

---

## Task 3.6 Implementation Plan

### Phase 3.6.1: Unit Test Foundation (Days 1-2)

**Objective**: Set up testing framework and write unit tests for stores/hooks

**1.1 Install Testing Dependencies**
```bash
npm install --save-dev \
  vitest \
  @vitest/ui \
  jsdom \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  @vitest/coverage-v8
```

**Why these choices**:
- **Vitest** over Jest: Faster, native ESM support, Vite-integrated
- **React Testing Library**: Industry standard for component testing
- **@vitest/coverage-v8**: Built-in coverage reporting
- **jsdom**: DOM simulation for tests

**1.2 Configure Vitest**

Create `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

**1.3 Create Test Utilities**

`frontend/src/test/setup.ts`:
- Import vitest matchers
- Setup RTL matchers
- Mock fetch/localStorage if needed

`frontend/src/test/test-utils.tsx`:
- Custom render function (providers wrapper)
- Zustand store mocking utilities
- API client mocking

**1.4 Write Store Unit Tests**

`frontend/src/store/__tests__/authStore.test.ts`:
- Test login/logout actions
- Test token persistence
- Test user state updates
- Test error handling

`frontend/src/store/__tests__/conversationStore.test.ts`:
- Test fetchConversations action
- Test sendMessage action with optimistic updates
- Test message status tracking
- Test error states

**1.5 Write Hook Unit Tests**

`frontend/src/hooks/__tests__/useAuth.test.ts`:
- Test authentication check
- Test redirect on auth failure
- Test user context access

---

### Phase 3.6.2: Component Integration Tests (Days 2-3)

**Objective**: Test React components with real store integration

**2.1 Modal Component Tests**

`frontend/src/components/__tests__/CreateOpportunityModal.test.tsx`:
- Test form rendering
- Test validation (empty fields)
- Test number input validation
- Test dropdown selection
- Test form submission
- Test error handling
- Test modal close

`frontend/src/components/__tests__/CreateCustomerModal.test.tsx`:
- Test email format validation
- Test required field validation
- Test form submission
- Test success callback

`frontend/src/components/__tests__/OpportunityDetailModal.test.tsx`:
- Test data display
- Test action buttons (Mark as Won, Delete)
- Test confirmation dialogs

**2.2 Page Component Tests**

`frontend/src/pages/__tests__/CustomersPage.test.tsx`:
- Test customer list rendering
- Test search/filter functionality
- Test customer selection
- Test detail panel display
- Test navigation to conversations

`frontend/src/pages/__tests__/OpportunitiesPage.test.tsx`:
- Test opportunity list display
- Test filtering by stage/customer
- Test sorting
- Test modal open/close
- Test detail view

**2.3 API Client Tests**

`frontend/src/api/__tests__/client.test.ts`:
- Test request interception (JWT auth)
- Test error handling (401, 500)
- Test retry logic
- Test base URL configuration

---

### Phase 3.6.3: E2E Testing (Days 3-4)

**Objective**: Test complete user workflows

**3.1 Install E2E Testing Framework**

```bash
npm install --save-dev playwright @playwright/test
```

**Why Playwright**:
- Cross-browser (Chrome, Firefox, Safari)
- Fast execution
- Good debugging tools
- Built-in trace/video capture

**3.2 Configure Playwright**

Create `frontend/playwright.config.ts`:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
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

**3.3 Write E2E Tests**

`frontend/e2e/auth.spec.ts`:
- Test login flow
- Test logout
- Test session persistence
- Test redirect on auth failure

`frontend/e2e/customer-flow.spec.ts`:
- Test: Load customers page
- Test: Search for customer
- Test: View customer detail
- Test: Start conversation from customer
- Test: View opportunities filtered by customer

`frontend/e2e/opportunity-flow.spec.ts`:
- Test: Create opportunity
- Test: View opportunity detail
- Test: Mark opportunity as won
- Test: Delete opportunity

`frontend/e2e/conversation-flow.spec.ts`:
- Test: Create conversation
- Test: Send message
- Test: Message appears with status
- Test: Error recovery (retry message)

---

### Phase 3.6.4: CI/CD Pipeline (Days 4-5)

**Objective**: Automate testing, coverage, and deployment

**4.1 Create Frontend Test Workflow**

`frontend/.github/workflows/frontend-tests.yml`:
```yaml
name: Frontend Tests & Build

on:
  push:
    branches: [main, swarm]
  pull_request:
    branches: [main, swarm]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Lint
        working-directory: frontend
        run: npm run lint

      - name: Type check
        working-directory: frontend
        run: npx tsc --noEmit

      - name: Unit tests
        working-directory: frontend
        run: npm run test

      - name: Coverage report
        working-directory: frontend
        run: npm run test:coverage

      - name: Build
        working-directory: frontend
        run: npm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/coverage-final.json
```

**4.2 Create E2E Test Workflow**

`frontend/.github/workflows/e2e-tests.yml`:
```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main, swarm]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  e2e:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: testpwd
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Start backend
        working-directory: backend/python
        run: |
          pip install -r requirements.txt
          python -m agent_service &

      - name: Wait for backend
        run: sleep 5

      - name: Install frontend deps
        working-directory: frontend
        run: npm ci

      - name: Run E2E tests
        working-directory: frontend
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

**4.3 Update Package.json Scripts**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch",
    "e2e": "playwright test",
    "e2e:debug": "playwright test --debug",
    "type-check": "tsc --noEmit"
  }
}
```

---

### Phase 3.6.5: Pre-commit Hooks & Polish (Days 5-6)

**Objective**: Enforce code quality standards automatically

**5.1 Install Husky**

```bash
npm install --save-dev husky lint-staged
npx husky install
```

**5.2 Create Pre-commit Hook**

`frontend/.husky/pre-commit`:
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
```

**5.3 Configure lint-staged**

`frontend/.lintstagedrc.json`:
```json
{
  "*.{ts,tsx}": ["eslint --fix", "vitest related --run"],
  "*.json": ["prettier --write"]
}
```

**5.4 Code Coverage Goals**

Target metrics:
- **Statements**: 80% coverage
- **Branches**: 75% coverage
- **Functions**: 80% coverage
- **Lines**: 80% coverage

Critical paths (must test):
- ✅ All modal form submissions
- ✅ API error handling
- ✅ Store actions (fetch, create, update)
- ✅ Authentication flow
- ✅ Message status tracking

---

## Testing Scope by Component

### High Priority (Must Test)

**Critical User Flows**:
1. ✅ Login → Create Conversation → Send Message
2. ✅ Login → Create Opportunity → View Detail
3. ✅ Login → Create Customer → Start Conversation
4. ✅ Message creation with error recovery
5. ✅ Form validation (all modals)

**Key Components**:
- CreateOpportunityModal (form validation, API call)
- CreateCustomerModal (form validation, API call)
- conversationStore.sendMessage (optimistic updates)
- authStore (login/logout, token persistence)

### Medium Priority (Should Test)

- ConversationList (rendering, filtering)
- MessageList (message display, status)
- OpportunitiesPage (filtering, sorting)
- CustomersPage (search, selection)

### Low Priority (Nice to Have)

- CSS styling verification
- Animation timing
- Performance metrics
- Accessibility compliance (WCAG)

---

## Success Criteria

**Unit Tests**:
- ✅ All stores have tests (authStore, conversationStore)
- ✅ All hooks have tests (useAuth)
- ✅ >80% code coverage on stores

**Component Tests**:
- ✅ All modal forms tested
- ✅ All form validations tested
- ✅ All error states tested
- ✅ >70% coverage on components

**E2E Tests**:
- ✅ Complete user flows pass
- ✅ Cross-browser testing (Chrome, Firefox)
- ✅ Tests run in CI/CD

**CI/CD**:
- ✅ GitHub Actions workflows passing
- ✅ Code coverage reported to PR
- ✅ Pre-commit hooks enforcing standards
- ✅ Build & test on every PR

---

## Known Challenges & Solutions

### Challenge 1: Testing Async API Calls
**Solution**: Mock axios client, use vitest.waitFor() for async state updates

### Challenge 2: Testing WebSocket
**Solution**: Mock wsClient, test message handling separately from WebSocket

### Challenge 3: Testing Zustand Store
**Solution**: Import store directly, call actions, assert state changes

### Challenge 4: Testing Modal Dialogs
**Solution**: Use React Testing Library query selectors, test user interactions

### Challenge 5: E2E Flakiness
**Solution**: Use Playwright's wait mechanisms, increase timeouts in CI

---

## File Creation Checklist

**Test Configuration**:
- [ ] `frontend/vitest.config.ts`
- [ ] `frontend/playwright.config.ts`
- [ ] `frontend/src/test/setup.ts`
- [ ] `frontend/src/test/test-utils.tsx`

**Unit Tests**:
- [ ] `frontend/src/store/__tests__/authStore.test.ts`
- [ ] `frontend/src/store/__tests__/conversationStore.test.ts`
- [ ] `frontend/src/hooks/__tests__/useAuth.test.ts`
- [ ] `frontend/src/api/__tests__/client.test.ts`

**Component Tests**:
- [ ] `frontend/src/components/__tests__/CreateOpportunityModal.test.tsx`
- [ ] `frontend/src/components/__tests__/CreateCustomerModal.test.tsx`
- [ ] `frontend/src/components/__tests__/OpportunityDetailModal.test.tsx`
- [ ] `frontend/src/pages/__tests__/CustomersPage.test.tsx`
- [ ] `frontend/src/pages/__tests__/OpportunitiesPage.test.tsx`

**E2E Tests**:
- [ ] `frontend/e2e/auth.spec.ts`
- [ ] `frontend/e2e/customer-flow.spec.ts`
- [ ] `frontend/e2e/opportunity-flow.spec.ts`
- [ ] `frontend/e2e/conversation-flow.spec.ts`

**CI/CD**:
- [ ] `.github/workflows/frontend-tests.yml`
- [ ] `.github/workflows/e2e-tests.yml`
- [ ] `frontend/.husky/pre-commit`
- [ ] `frontend/.lintstagedrc.json`

---

## Estimated Line Counts

| Phase | Component | Lines | Time |
|-------|-----------|-------|------|
| 3.6.1 | Test setup & unit tests | 800-1000 | 2 days |
| 3.6.2 | Component tests | 600-800 | 1.5 days |
| 3.6.3 | E2E tests | 400-600 | 1 day |
| 3.6.4 | CI/CD workflows | 300-400 | 1 day |
| 3.6.5 | Hooks & polish | 100-200 | 0.5 days |
| **Total** | **3.6 Complete** | **2200-3000** | **5-7 days** |

---

## Risk Assessment

**Low Risk**:
- ✅ Testing frameworks proven and stable
- ✅ No changes to application code needed
- ✅ Can be built incrementally
- ✅ Failure doesn't break production

**Medium Risk**:
- ⚠️ E2E tests can be flaky (timing issues)
- ⚠️ CI/CD requires backend service running
- ⚠️ Coverage goals may be hard to reach

**Mitigation**:
- Use Playwright best practices (wait for elements, not time)
- Run backend in GitHub Actions services
- Focus on critical paths first

---

## Next Phase Readiness

**Task 3.6 Completion enables**:
- ✅ Task 3.7 (Deployment): Can deploy with confidence
- ✅ Feature development: Tests catch regressions
- ✅ Code review: Coverage reports in PRs
- ✅ Team scaling: Tests document expected behavior

**Post-Phase 3 Work**:
- Phase 4: Advanced features (analytics, webhooks)
- Phase 5: Performance optimization
- Phase 6: Security hardening

---

## Scout Recommendations for Worker

1. **Start with Unit Tests First**
   - Fastest to implement
   - Highest ROI on coverage
   - Can run without backend

2. **Use Vitest for Speed**
   - Much faster than Jest
   - Better DX with Vite integration
   - Native ESM support

3. **Mock API Calls Consistently**
   - Create mock factory in test-utils
   - Reuse across all component tests
   - Keep mocks close to real API

4. **Focus on Happy Path First**
   - Get basic tests passing
   - Then add error scenarios
   - Polish later

5. **Run Tests Frequently**
   - Use `npm run test:watch`
   - Test-driven development approach
   - Red-Green-Refactor cycle

---

**Prepared by**: Scout Agent (Termite Protocol)
**Session Type**: Reconnaissance & Planning for Phase 3.6
**Confidence Level**: Very High (tested frameworks, clear scope)
**Recommended Next Caste**: Worker (implementation)

---

*Ready to hand off to Worker for implementation. All prerequisites analyzed, clear roadmap established, low-risk implementation path identified.*
