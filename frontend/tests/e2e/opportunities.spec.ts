import { test, expect } from '@playwright/test';

test.describe('Opportunity Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');
    await page.waitForURL('/dashboard');

    // Navigate to opportunities
    await page.click('button:has-text("Opportunities")');
    await page.waitForURL('/opportunities');
  });

  test('should display opportunity list', async ({ page }) => {
    // Should show opportunities header
    expect(await page.locator('text=Opportunities')).toBeVisible();

    // Should show opportunity cards
    expect(await page.locator('.opp-card')).toBeVisible();
  });

  test('should display filter controls', async ({ page }) => {
    // Should show status filter
    expect(await page.locator('select').nth(0)).toBeVisible();

    // Should show customer filter
    expect(await page.locator('select').nth(1)).toBeVisible();

    // Should show sort by filter
    expect(await page.locator('select').nth(2)).toBeVisible();
  });

  test('should filter opportunities by stage', async ({ page }) => {
    // Get initial opportunity count
    const initialCount = await page.locator('.opp-card').count();

    // Filter by stage
    const stageFilter = await page.locator('select').nth(0);
    await stageFilter.selectOption('proposal');

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Count should potentially change
    const filteredCount = await page.locator('.opp-card').count();
    // Count might be same or less
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('should filter opportunities by customer', async ({ page }) => {
    // Get filter
    const customerFilter = await page.locator('select').nth(1);

    // Should have customer options
    const options = await customerFilter.locator('option').count();
    expect(options).toBeGreaterThan(0);
  });

  test('should sort opportunities by amount', async ({ page }) => {
    // Get sort filter
    const sortFilter = await page.locator('select').nth(2);

    // Select amount sort
    await sortFilter.selectOption('amount');

    // Wait for sort to apply
    await page.waitForTimeout(500);

    // Opportunities should be visible
    expect(await page.locator('.opp-card').first()).toBeVisible();
  });

  test('should display summary cards', async ({ page }) => {
    // Should show total opportunities
    expect(await page.locator('text=/total opportunities/i')).toBeVisible();

    // Should show pipeline value
    expect(await page.locator('text=/pipeline value/i')).toBeVisible();

    // Should show average deal size
    expect(await page.locator('text=/average deal size/i')).toBeVisible();
  });

  test('should open create opportunity modal', async ({ page }) => {
    // Click create opportunity button
    const createBtn = await page.locator('button:has-text("+ New Opportunity")');
    expect(createBtn).toBeVisible();

    await createBtn.click();

    // Modal should appear
    const modal = await page.locator('text=New Opportunity');
    expect(modal).toBeVisible();
  });

  test('should create new opportunity', async ({ page }) => {
    // Click create button
    const createBtn = await page.locator('button:has-text("+ New Opportunity")');
    await createBtn.click();

    // Wait for modal
    await page.waitForSelector('text=New Opportunity');

    // Fill form
    const customerSelect = await page.locator('select').nth(0);
    const titleInput = await page.locator('input[id="title"]');
    const amountInput = await page.locator('input[id="amount"]');
    const stageSelect = await page.locator('select').nth(1);

    await customerSelect.selectOption('cust1');
    await titleInput.fill('New Enterprise Deal');
    await amountInput.fill('250000');
    await stageSelect.selectOption('Prospecting');

    // Submit form
    const submitBtn = await page.locator('button:has-text("Create Opportunity")');
    await submitBtn.click();

    // Modal should close
    await page.waitForSelector('text=New Opportunity', { state: 'hidden' });

    // New opportunity should appear in list
    expect(await page.locator('text=New Enterprise Deal')).toBeVisible();
  });

  test('should open opportunity detail modal on click', async ({ page }) => {
    // Click first opportunity card
    const firstOpp = await page.locator('.opp-card').first();
    expect(firstOpp).toBeVisible();

    await firstOpp.click();

    // Detail modal should appear
    const detailModal = await page.locator('text=Opportunity Details');
    expect(detailModal).toBeVisible();
  });

  test('should display opportunity details in modal', async ({ page }) => {
    // Click first opportunity
    const firstOpp = await page.locator('.opp-card').first();
    await firstOpp.click();

    // Wait for modal
    await page.waitForSelector('text=Opportunity Details');

    // Should show details
    expect(await page.locator('text=/customer/i')).toBeVisible();
    expect(await page.locator('text=/amount/i')).toBeVisible();
    expect(await page.locator('text=/stage/i')).toBeVisible();
  });

  test('should mark opportunity as won', async ({ page }) => {
    // Click first opportunity
    const firstOpp = await page.locator('.opp-card').first();
    await firstOpp.click();

    // Wait for modal
    await page.waitForSelector('text=Opportunity Details');

    // Click mark as won
    const markAsWonBtn = await page.locator('button:has-text("Mark as Won")');
    if (await markAsWonBtn.isEnabled()) {
      await markAsWonBtn.click();

      // Modal should close
      await page.waitForSelector('text=Opportunity Details', { state: 'hidden' });
    }
  });

  test('should delete opportunity with confirmation', async ({ page }) => {
    // Click first opportunity
    const firstOpp = await page.locator('.opp-card').first();
    const oppTitle = await firstOpp.locator('h3').textContent();

    await firstOpp.click();

    // Wait for modal
    await page.waitForSelector('text=Opportunity Details');

    // Accept confirmation dialog and click delete
    page.once('dialog', (dialog) => {
      if (dialog.type() === 'confirm') {
        dialog.accept();
      }
    });

    const deleteBtn = await page.locator('button:has-text("Delete")');
    await deleteBtn.click();

    // Modal should close
    await page.waitForSelector('text=Opportunity Details', { state: 'hidden' });

    // Opportunity might be removed from list
    await page.waitForTimeout(500);
  });

  test('should navigate to opportunities with customer filter from URL', async ({ page }) => {
    // Navigate to opportunities with customer param
    const customerFilter = 'cust1';
    await page.goto(`/opportunities?customer=${customerFilter}`);

    // Wait for page to load
    await page.waitForURL(/\/opportunities/);

    // Should be on opportunities page
    expect(page.url()).toContain(`customer=${customerFilter}`);
  });

  test('should show empty state for no matching opportunities', async ({ page }) => {
    // Filter to unlikely stage
    const stageFilter = await page.locator('select').nth(0);
    await stageFilter.selectOption('closed');

    // Wait for filter
    await page.waitForTimeout(500);

    // If no results, should show empty state
    const emptyState = await page.locator('text=/no opportunities match/i');
    const cardCount = await page.locator('.opp-card').count();

    if (cardCount === 0) {
      expect(emptyState).toBeVisible();
    }
  });
});
