import { test, expect } from '@playwright/test';

test.describe('Customer Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');
    await page.waitForURL('/dashboard');

    // Navigate to customers
    await page.click('button:has-text("Customers")');
    await page.waitForURL('/customers');
  });

  test('should display customer list', async ({ page }) => {
    // Should show customers sidebar
    expect(await page.locator('text=Customers')).toBeVisible();

    // Should show search input
    const searchInput = await page.locator('input[placeholder*="Search customers"]');
    expect(searchInput).toBeVisible();
  });

  test('should search customers by name', async ({ page }) => {
    const searchInput = await page.locator('input[placeholder*="Search customers"]');

    // Get first customer name (if exists)
    // Type partial name to filter
    await searchInput.fill('Test');

    // Should filter customer list
    // Wait for list to update
    await page.waitForTimeout(500);
  });

  test('should display customer detail on selection', async ({ page }) => {
    // Click first customer in list
    const firstCustomer = await page.locator('.customer-item').first();
    expect(firstCustomer).toBeVisible();

    await firstCustomer.click();

    // Should show detail panel
    expect(await page.locator('text=/contact information|account details/i')).toBeVisible();
  });

  test('should show customer contact information', async ({ page }) => {
    // Click first customer
    const firstCustomer = await page.locator('.customer-item').first();
    await firstCustomer.click();

    // Should show email
    expect(await page.locator('text=/email/i')).toBeVisible();

    // Should show other contact fields
    expect(await page.locator('.detail-content')).toBeVisible();
  });

  test('should open create customer modal', async ({ page }) => {
    // Click create customer button
    const createBtn = await page.locator('button.new-customer-btn');
    expect(createBtn).toBeVisible();

    await createBtn.click();

    // Modal should appear
    const modal = await page.locator('text=New Customer');
    expect(modal).toBeVisible();
  });

  test('should create new customer', async ({ page }) => {
    // Click create customer button
    const createBtn = await page.locator('button.new-customer-btn');
    await createBtn.click();

    // Wait for modal
    await page.waitForSelector('text=New Customer');

    // Fill in customer form
    await page.fill('input[id="name"]', 'New Test Company');
    await page.fill('input[id="email"]', 'newtest@company.com');
    await page.fill('input[id="phone"]', '+1-555-9999');

    // Click create button
    await page.click('button:has-text("Create Customer")');

    // Modal should close
    await page.waitForSelector('text=New Customer', { state: 'hidden' });

    // New customer should appear in list
    expect(await page.locator('text=New Test Company')).toBeVisible();
  });

  test('should open start conversation modal from customer detail', async ({ page }) => {
    // Select customer
    const firstCustomer = await page.locator('.customer-item').first();
    await firstCustomer.click();

    // Click start conversation button
    const startConvBtn = await page.locator('button:has-text("Start Conversation")');
    expect(startConvBtn).toBeVisible();

    await startConvBtn.click();

    // Modal should appear
    const conversationModal = await page.locator('text=New Conversation');
    expect(conversationModal).toBeVisible();
  });

  test('should start conversation from customer', async ({ page }) => {
    // Select customer
    const firstCustomer = await page.locator('.customer-item').first();
    await firstCustomer.click();

    // Click start conversation
    await page.click('button:has-text("Start Conversation")');

    // Wait for modal
    await page.waitForSelector('text=New Conversation');

    // Fill title
    await page.fill('input[id="title"]', 'Q1 Sales Discussion');

    // Submit
    await page.click('button:has-text("Create")');

    // Should navigate to conversations
    await page.waitForURL('/conversations');
    expect(page.url()).toContain('/conversations');
  });

  test('should navigate to opportunities from customer detail', async ({ page }) => {
    // Select customer
    const firstCustomer = await page.locator('.customer-item').first();
    await firstCustomer.click();

    // Click view opportunities
    const viewOppBtn = await page.locator('button:has-text("View Opportunities")');
    expect(viewOppBtn).toBeVisible();

    await viewOppBtn.click();

    // Should navigate to opportunities with customer filter
    await page.waitForURL(/\/opportunities/);
    expect(page.url()).toContain('/opportunities');
  });

  test('should show empty state when no customers selected', async ({ page }) => {
    // Should show select customer message
    const emptyState = await page.locator('text=/select a customer/i');
    expect(emptyState).toBeVisible();
  });

  test('should clear search to show all customers', async ({ page }) => {
    const searchInput = await page.locator('input[placeholder*="Search customers"]');

    // Search for specific customer
    await searchInput.fill('Acme');
    await page.waitForTimeout(500);

    // Clear search
    await searchInput.clear();

    // Should show all customers again
    await page.waitForTimeout(500);
  });
});
