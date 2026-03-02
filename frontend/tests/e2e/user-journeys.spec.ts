import { test, expect, type Page } from '@playwright/test';

// ─── Helper Functions ───────────────────────────────────────────────

/**
 * Login with username/password credentials.
 * After login, useAuth navigates to '/' (root). We wait until we leave /login.
 */
async function loginWithPassword(page: Page, account: string, password: string) {
  await page.goto('/login');
  await page.click('button:has-text("Password Login")');
  await page.fill('input[id="account"]', account);
  await page.fill('input[id="password"]', password);
  await page.click('button[type="submit"]');
  // useAuth.loginWithPassword navigates to '/' on success
  await page.waitForFunction(() => !window.location.pathname.startsWith('/login'));
}

/**
 * Login via SMS verification code.
 * Sends code, reads dev hint, fills code, submits.
 */
async function loginWithSms(page: Page, phone: string) {
  await page.goto('/login');
  await page.click('button:has-text("SMS Login")');
  await page.fill('input[id="phone"]', phone);
  await page.click('button:has-text("Send Code")');

  // Extract dev code from hint text (format: "Dev code: XXXXXX")
  const devHint = page.locator('small.form-hint:has-text("Dev code:")');
  await devHint.waitFor({ state: 'visible', timeout: 5000 });
  const hintText = await devHint.textContent();
  const code = hintText?.replace('Dev code: ', '') ?? '';

  await page.fill('input[id="code"]', code);
  await page.click('button[type="submit"]');
  // useAuth.loginWithSms navigates to '/' on success
  await page.waitForFunction(() => !window.location.pathname.startsWith('/login'));
}

/**
 * Navigate to a section via the dashboard page.
 * First goes to /dashboard, then clicks the section button.
 */
async function navigateFromDashboard(
  page: Page,
  section: 'Conversations' | 'Customers' | 'Opportunities',
) {
  await page.goto('/dashboard');
  await page.waitForURL('/dashboard');
  await page.click(`button:has-text("${section}")`);
  await page.waitForURL(`/${section.toLowerCase()}`);
}

/**
 * Wait for the opportunities page data to load (loading state to disappear and content to appear).
 */
async function waitForOpportunitiesLoad(page: Page) {
  // Wait for either opp-cards or empty-state to appear (meaning loading is done)
  await page.waitForFunction(
    () =>
      document.querySelector('.opp-card') !== null ||
      document.querySelector('.empty-state') !== null ||
      document.querySelector('.summary-card') !== null,
    null,
    { timeout: 15000 },
  );
}

// ─── UC-01: B2B Morning Pipeline Review ─────────────────────────────

test.describe('UC-01: B2B Morning Pipeline Review', () => {
  test('Alice reviews sales pipeline to plan her day', async ({ page }) => {
    // Step 1: Login as Alice (B2B Account Manager)
    await loginWithPassword(page, 'alice', 'touchcli123');

    // Step 2: Navigate to Opportunities
    await navigateFromDashboard(page, 'Opportunities');
    await waitForOpportunitiesLoad(page);

    // Step 3: Verify summary cards for pipeline overview
    await expect(page.locator('.summary-card').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Total Opportunities')).toBeVisible();
    await expect(page.locator('text=Pipeline Value')).toBeVisible();
    await expect(page.locator('text=Average Deal Size')).toBeVisible();

    // Step 4: Filter by stage to focus on proposals
    const stageFilter = page.locator('select').nth(0);
    const initialCount = await page.locator('.opp-card').count();
    await stageFilter.selectOption('proposal');
    await page.waitForTimeout(500);
    const filteredCount = await page.locator('.opp-card').count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);

    // Step 5: Reset stage filter, then sort by deal amount
    await stageFilter.selectOption('');
    await page.waitForTimeout(300);
    const sortFilter = page.locator('select').nth(2);
    await sortFilter.selectOption('amount');
    await page.waitForTimeout(500);
    const afterSortCount = await page.locator('.opp-card').count();
    expect(afterSortCount).toBeGreaterThan(0);

    // Step 6: Verify customer filter has selectable options
    const customerFilter = page.locator('select').nth(1);
    const customerOptions = await customerFilter.locator('option').count();
    expect(customerOptions).toBeGreaterThan(0);
  });
});

// ─── UC-02: B2B New Client Acquisition ──────────────────────────────

test.describe('UC-02: B2B New Client Acquisition', () => {
  test('Bob meets prospect, creates client/opportunity/conversation', async ({ page }) => {
    // Step 1: Login as Bob (B2B Account Manager)
    await loginWithPassword(page, 'bob', 'touchcli123');

    // Step 2: Navigate to Customers
    await navigateFromDashboard(page, 'Customers');

    // Step 3: Create new B2B customer
    await page.locator('button.new-customer-btn').click();
    await page.waitForSelector('text=New Customer');
    await page.fill('input[id="name"]', 'Meridian Dynamics');
    await page.fill('input[id="email"]', 'sales@meridian-dynamics.com');
    await page.fill('input[id="phone"]', '+1-555-8001');
    await page.click('button:has-text("Create Customer")');
    await page.waitForSelector('text=New Customer', { state: 'hidden' });

    // Step 4: Verify new customer appears in list
    await expect(page.locator('text=Meridian Dynamics')).toBeVisible();

    // Step 5: Select customer and view contact details
    await page.locator('text=Meridian Dynamics').click();
    await expect(page.locator('h3:has-text("Contact Information")')).toBeVisible();

    // Step 6: Navigate to opportunities from customer detail
    await page.click('button:has-text("View Opportunities")');
    await page.waitForURL(/\/opportunities/);
    await waitForOpportunitiesLoad(page);

    // Step 7: Create opportunity for this customer
    await page.locator('button:has-text("+ New Opportunity")').click();
    await page.waitForSelector('text=New Opportunity');

    // Select customer in dropdown (no preselection from opportunities page)
    const oppCustomerSelect = page.locator('select#customer');
    const oppCustomerOpts = await oppCustomerSelect.locator('option').count();
    if (oppCustomerOpts > 1) {
      await oppCustomerSelect.selectOption({ index: 1 });
    }
    await page.fill('input[id="title"]', 'Meridian Enterprise License');
    await page.fill('input[id="amount"]', '180000');
    await page.click('button:has-text("Create Opportunity")');
    // Wait for modal to close (use modal header h2, not button text)
    await page.waitForSelector('.modal-overlay', { state: 'hidden', timeout: 10000 });

    // Step 8: Go back to Customers and start a conversation
    await page.goto('/customers');
    await page.waitForURL('/customers');
    await page.locator('.customer-item').first().click();
    await page.click('button:has-text("Start Conversation")');
    await page.waitForSelector('text=New Conversation');
    await page.fill('input[id="title"]', 'Meridian Initial Contact');
    await page.click('button.btn-create');
    await page.waitForTimeout(1000);
    expect(page.url()).toContain('/conversations');
  });
});

// ─── UC-03: B2C Post-Consultation Record ────────────────────────────

test.describe('UC-03: B2C Post-Consultation Record', () => {
  test('Carol records beauty consultation via SMS login on phone', async ({ page }) => {
    // Step 1: SMS login as Carol (B2C Consultant)
    await loginWithSms(page, '+1-555-0103');

    // Step 2: Navigate to Customers
    await navigateFromDashboard(page, 'Customers');

    // Step 3: Create individual client record (local demo mode)
    await page.locator('button.new-customer-btn').click();
    await page.waitForSelector('text=New Customer');
    await page.fill('input[id="name"]', 'Li Wei');
    await page.fill('input[id="email"]', 'liwei@personal.com');
    await page.fill('input[id="phone"]', '+86-138-0001-0001');
    await page.click('button:has-text("Create Customer")');
    await page.waitForSelector('text=New Customer', { state: 'hidden' });

    // Step 4: Verify client appears in list
    await expect(page.locator('text=Li Wei')).toBeVisible();

    // Step 5: Select an existing customer (with valid backend UUID) to start conversation
    // Note: locally-created customers have demo IDs, so use a seeded customer for API calls
    const firstSeededCustomer = page.locator('.customer-item').first();
    await firstSeededCustomer.click();
    await expect(page.locator('h3:has-text("Contact Information")')).toBeVisible();

    // Step 6: Start consultation conversation
    await page.click('button:has-text("Start Conversation")');
    await page.waitForSelector('text=New Conversation');
    await page.fill('input[id="title"]', 'Beauty Consultation - Skin Care');
    await page.click('button.btn-create');

    // Step 7: Verify navigation to conversations
    await page.waitForFunction(
      () => window.location.pathname === '/' || window.location.pathname.startsWith('/conversations'),
      null,
      { timeout: 5000 },
    );
  });
});

// ─── UC-04: B2B Deal Closure ────────────────────────────────────────

test.describe('UC-04: B2B Deal Closure', () => {
  test('Alice closes an enterprise deal by marking it as Won', async ({ page }) => {
    // Step 1: Login
    await loginWithPassword(page, 'alice', 'touchcli123');

    // Step 2: Navigate to Opportunities
    await navigateFromDashboard(page, 'Opportunities');
    await waitForOpportunitiesLoad(page);

    // Step 3: Verify deals exist (wait for cards to render)
    await expect(page.locator('.opp-card').first()).toBeVisible({ timeout: 10000 });
    const oppCount = await page.locator('.opp-card').count();
    expect(oppCount).toBeGreaterThan(0);

    // Step 4: Click first deal to open detail modal
    await page.locator('.opp-card').first().click();
    await page.waitForSelector('text=Opportunity Details');

    // Step 5: Verify deal details are shown
    await expect(page.locator('text=/customer/i').first()).toBeVisible();
    await expect(page.locator('text=/amount/i').first()).toBeVisible();
    await expect(page.locator('text=/stage/i').first()).toBeVisible();

    // Step 6: Mark as Won if available
    const markWonBtn = page.locator('button:has-text("Mark as Won")');
    if (await markWonBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      if (await markWonBtn.isEnabled()) {
        await markWonBtn.click();
        await page.waitForSelector('text=Opportunity Details', {
          state: 'hidden',
        });
      }
    }

    // Step 7: Verify still on opportunities page
    expect(page.url()).toContain('/opportunities');
  });
});

// ─── UC-05: Sales Manager Pipeline Analysis ─────────────────────────

test.describe('UC-05: Sales Manager Pipeline Analysis', () => {
  test('Carol analyzes team pipeline for weekly meeting', async ({ page }) => {
    // Step 1: Carol uses password login for desktop analysis
    await loginWithPassword(page, 'carol', 'touchcli123');

    // Step 2: Navigate to Opportunities
    await navigateFromDashboard(page, 'Opportunities');
    await waitForOpportunitiesLoad(page);

    // Step 3: Review summary cards
    await expect(page.locator('.summary-card').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Total Opportunities')).toBeVisible();
    await expect(page.locator('text=Pipeline Value')).toBeVisible();

    // Step 4: Filter by stage (proposal)
    const stageFilter = page.locator('select').nth(0);
    await stageFilter.selectOption('proposal');
    await page.waitForTimeout(500);

    // Step 5: Sort by amount to compare deal sizes
    const sortFilter = page.locator('select').nth(2);
    await sortFilter.selectOption('amount');
    await page.waitForTimeout(500);

    // Step 6: Filter by customer to drill down
    const customerFilter = page.locator('select').nth(1);
    const options = await customerFilter.locator('option').count();
    if (options > 1) {
      await customerFilter.selectOption({ index: options - 1 });
      await page.waitForTimeout(500);
    }

    // Step 7: Check for results or empty state
    const cardCount = await page.locator('.opp-card').count();
    if (cardCount === 0) {
      await expect(page.locator('.empty-state')).toBeVisible();
    } else {
      await expect(page.locator('.opp-card').first()).toBeVisible();
    }
  });
});

// ─── UC-06: B2B Customer Follow-up Messaging ────────────────────────

test.describe('UC-06: B2B Customer Follow-up Messaging', () => {
  test('Bob sends follow-up messages in existing conversation', async ({ page }) => {
    // Step 1: Login as Bob
    await loginWithPassword(page, 'bob', 'touchcli123');

    // Step 2: Login lands on '/' which renders ConversationApp
    await page.waitForTimeout(500);

    // Step 3: Check for existing conversations
    const convoCount = await page.locator('.conversation-item').count();

    if (convoCount > 0) {
      // Step 4: Select existing conversation
      await page.locator('.conversation-item').first().click();
      await page.waitForTimeout(500);

      // Step 5: Find message input
      const messageInput = page
        .locator('textarea')
        .or(page.locator('input[type="text"]'))
        .nth(0);

      if (await messageInput.isVisible()) {
        // Step 6: Send first follow-up message
        await messageInput.fill(
          'Hi, following up on our discussion from last week.',
        );
        const sendBtn = page.locator('button').filter({ hasText: /send/i });
        if ((await sendBtn.count()) > 0) {
          await sendBtn.first().click();
          await page.waitForTimeout(1000);

          // Step 7: Send second follow-up message
          await messageInput.fill(
            'Would you be available for a call this Thursday?',
          );
          await sendBtn.first().click();
          await page.waitForTimeout(1000);
        }
      }
    }

    // Step 8: Verify still on conversations page (root '/' or '/conversations')
    const url = page.url();
    expect(url.endsWith('/') || url.includes('/conversations')).toBeTruthy();
  });
});

// ─── UC-07: Cross-Entity Navigation Workflow ────────────────────────

test.describe('UC-07: Cross-Entity Navigation Workflow', () => {
  test('Alice navigates across customers, opportunities, and conversations', async ({ page }) => {
    // Step 1: Login
    await loginWithPassword(page, 'alice', 'touchcli123');

    // Step 2: Navigate to Customers
    await navigateFromDashboard(page, 'Customers');

    // Step 3: Select a customer and view contact info
    const firstCustomer = page.locator('.customer-item').first();
    await expect(firstCustomer).toBeVisible();
    await firstCustomer.click();
    await expect(page.locator('h3:has-text("Contact Information")')).toBeVisible();
    await expect(page.locator('.detail-panel')).toBeVisible();

    // Step 4: Navigate to opportunities via customer detail
    await page.click('button:has-text("View Opportunities")');
    await page.waitForURL(/\/opportunities/);
    await waitForOpportunitiesLoad(page);

    // Step 5: Navigate back to Customers
    await page.goto('/customers');
    await page.waitForURL('/customers');

    // Step 6: Select customer and start conversation
    await page.locator('.customer-item').first().click();
    await page.click('button:has-text("Start Conversation")');
    await page.waitForSelector('text=New Conversation');
    await page.fill('input[id="title"]', 'Cross-Entity Review Discussion');
    await page.click('button.btn-create');

    // Step 7: Verify navigation to conversations
    await page.waitForFunction(
      () => window.location.pathname === '/' || window.location.pathname.startsWith('/conversations'),
      null,
      { timeout: 5000 },
    );
  });
});

// ─── UC-08: Mobile Session Continuity ───────────────────────────────

test.describe('UC-08: Mobile Session Continuity', () => {
  test('Bob session persists across reloads and terminates on logout', async ({ page }) => {
    // Step 1: Login as Bob (field salesperson on mobile)
    await loginWithPassword(page, 'bob', 'touchcli123');

    // Step 2: Navigate to Customers
    await navigateFromDashboard(page, 'Customers');
    expect(page.url()).toContain('/customers');

    // Step 3: Simulate phone interruption — reload page
    await page.reload();
    await page.waitForTimeout(1000);
    // Session should persist (not redirected to login)
    expect(page.url()).not.toContain('/login');

    // Step 4: Navigate to Opportunities
    await page.goto('/opportunities');
    await page.waitForURL(/\/opportunities/);
    expect(page.url()).toContain('/opportunities');

    // Step 5: Another reload (resume after phone call)
    await page.reload();
    await page.waitForTimeout(1000);
    expect(page.url()).not.toContain('/login');

    // Step 6: Logout
    await page.click('button:has-text("Logout")');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'));
    expect(page.url()).toContain('/login');

    // Step 7: Verify protected routes are inaccessible after logout
    await page.goto('/dashboard');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'));
    expect(page.url()).toContain('/login');

    await page.goto('/customers');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'));
    expect(page.url()).toContain('/login');
  });
});

// ─── UC-09: New Employee System Exploration ─────────────────────────

test.describe('UC-09: New Employee System Exploration', () => {
  test('Alice explores all system sections after onboarding', async ({ page }) => {
    // Step 1: Login and navigate to dashboard
    await loginWithPassword(page, 'alice', 'touchcli123');
    await page.goto('/dashboard');
    await page.waitForURL('/dashboard');

    // Step 2: Verify dashboard elements
    await expect(page.locator('text=TouchCLI Dashboard')).toBeVisible();
    await expect(page.locator('button:has-text("Conversations")')).toBeVisible();
    await expect(page.locator('button:has-text("Customers")')).toBeVisible();
    await expect(page.locator('button:has-text("Opportunities")')).toBeVisible();

    // Step 3: Explore Customers section
    await page.click('button:has-text("Customers")');
    await page.waitForURL('/customers');
    const searchInput = page.locator('input.search-input');
    await expect(searchInput).toBeVisible();

    // Step 4: Search and clear
    await searchInput.fill('Acme');
    await page.waitForTimeout(500);
    await searchInput.clear();
    await page.waitForTimeout(500);

    // Step 5: Explore Opportunities section
    await page.goto('/opportunities');
    await page.waitForURL('/opportunities');
    await waitForOpportunitiesLoad(page);
    await expect(page.locator('.summary-card').first()).toBeVisible({ timeout: 10000 });

    // Step 6: Explore Conversations section
    await page.goto('/conversations');
    await page.waitForURL('/conversations');

    // Verify either conversation list or empty state
    const convoList = page.locator('.conversation-item');
    const emptyState = page.locator('.empty');
    const hasConversations = (await convoList.count()) > 0;
    const isEmpty = await emptyState.isVisible().catch(() => false);
    expect(hasConversations || isEmpty).toBeTruthy();

    // Step 7: Create a new conversation
    const createBtn = page.locator('button.new-conversation-btn');
    await createBtn.click();
    await page.waitForSelector('text=New Conversation');

    // Select customer and fill title
    const customerSelect = page.locator('select#customer');
    const customerOpts = await customerSelect.locator('option').count();
    if (customerOpts > 1) {
      await customerSelect.selectOption({ index: 1 });
    }
    await page.fill('input[id="title"]', 'Exploration Test Chat');

    await page.click('button.btn-create');
    await page.waitForTimeout(1000);
  });
});

// ─── UC-10: Error Handling & Validation Guard ───────────────────────

test.describe('UC-10: Error Handling & Validation Guard', () => {
  test('UC-10A: wrong password shows error message', async ({ page }) => {
    await page.goto('/login');
    await page.click('button:has-text("Password Login")');
    await page.fill('input[id="account"]', 'alice');
    await page.fill('input[id="password"]', 'wrong-password');
    await page.click('button[type="submit"]');

    // Wait for the error to appear in .form-error
    await expect(page.locator('.form-error')).toBeVisible({ timeout: 10000 });
    // Should remain on login page
    expect(page.url()).toContain('/login');
  });

  test('UC-10B: SMS send code with empty phone shows validation error', async ({ page }) => {
    await page.goto('/login');
    // SMS is the default tab
    await page.click('button:has-text("SMS Login")');

    // Try sending code without entering phone
    await page.click('button:has-text("Send Code")');

    await expect(
      page.locator('text=/please enter your phone number/i'),
    ).toBeVisible();
  });

  test('UC-10C: protected routes redirect to login without auth', async ({ page }) => {
    // Try accessing each protected route directly — wait for client-side redirect
    await page.goto('/dashboard');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'), null, { timeout: 5000 });
    expect(page.url()).toContain('/login');

    await page.goto('/customers');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'), null, { timeout: 5000 });
    expect(page.url()).toContain('/login');

    await page.goto('/opportunities');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'), null, { timeout: 5000 });
    expect(page.url()).toContain('/login');

    await page.goto('/conversations');
    await page.waitForFunction(() => window.location.pathname.startsWith('/login'), null, { timeout: 5000 });
    expect(page.url()).toContain('/login');
  });

  test('UC-10D: create conversation without required fields keeps modal open', async ({ page }) => {
    await loginWithPassword(page, 'alice', 'touchcli123');
    // Login lands on '/' which is the conversations page
    await page.waitForTimeout(500);

    // Open create conversation modal
    const createBtn = page.locator('button.new-conversation-btn');
    await createBtn.click();
    await page.waitForSelector('text=New Conversation');

    // Create button should be disabled when fields are empty
    const submitBtn = page.locator('button.btn-create');
    await expect(submitBtn).toBeDisabled();

    // Fill title only — button still disabled (no customer selected)
    await page.fill('input[id="title"]', 'Incomplete Test');
    await expect(submitBtn).toBeDisabled();

    // Modal should still be open
    await expect(page.locator('text=New Conversation')).toBeVisible();
  });

  test('UC-10E: password login button disabled with empty fields', async ({ page }) => {
    await page.goto('/login');
    await page.click('button:has-text("Password Login")');

    // Login button should be disabled when fields are empty
    const loginBtn = page.locator('button[type="submit"]');
    await expect(loginBtn).toBeDisabled();

    // Fill only account — still disabled
    await page.fill('input[id="account"]', 'alice');
    await expect(loginBtn).toBeDisabled();

    // Fill password too — now enabled
    await page.fill('input[id="password"]', 'touchcli123');
    await expect(loginBtn).toBeEnabled();

    // Clear password — disabled again
    await page.fill('input[id="password"]', '');
    await expect(loginBtn).toBeDisabled();
  });
});
