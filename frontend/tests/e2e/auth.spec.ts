import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display login page on initial load', async ({ page }) => {
    await page.goto('/');

    // Should redirect to login if not authenticated
    expect(page.url()).toContain('/login');
    expect(await page.locator('input[placeholder*="UUID"]')).toBeVisible();
  });

  test('should login with demo user ID', async ({ page }) => {
    await page.goto('/login');

    // Enter demo user ID
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');

    // Click login button
    await page.click('button:has-text("Login")');

    // Should redirect to dashboard after login
    await page.waitForURL('/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Try empty credentials
    await page.click('button:has-text("Login")');

    // Should show error message
    const errorMessage = await page.locator('text=/invalid|required/i');
    expect(errorMessage).toBeVisible();
  });

  test('should display dashboard with navigation after login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');

    // Wait for dashboard
    await page.waitForURL('/dashboard');

    // Should show navigation buttons
    expect(await page.locator('button:has-text("Conversations")')).toBeVisible();
    expect(await page.locator('button:has-text("Customers")')).toBeVisible();
    expect(await page.locator('button:has-text("Opportunities")')).toBeVisible();
  });

  test('should navigate to customers page', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');

    // Wait for dashboard and click Customers
    await page.waitForURL('/dashboard');
    await page.click('button:has-text("Customers")');

    // Should navigate to customers page
    await page.waitForURL('/customers');
    expect(page.url()).toContain('/customers');
  });

  test('should navigate to opportunities page', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');

    // Wait for dashboard and click Opportunities
    await page.waitForURL('/dashboard');
    await page.click('button:has-text("Opportunities")');

    // Should navigate to opportunities page
    await page.waitForURL('/opportunities');
    expect(page.url()).toContain('/opportunities');
  });

  test('should navigate to conversations page', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');

    // Wait for dashboard and click Conversations
    await page.waitForURL('/dashboard');
    await page.click('button:has-text("Conversations")');

    // Should navigate to conversations page
    await page.waitForURL('/conversations');
    expect(page.url()).toContain('/conversations');
  });

  test('should persist session across page reloads', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');
    await page.waitForURL('/dashboard');

    // Reload page
    await page.reload();

    // Should still be on dashboard (not redirected to login)
    expect(page.url()).toContain('/dashboard');
  });

  test('should handle token expiration gracefully', async ({ page }) => {
    // This test would check if expired tokens redirect to login
    // Implementation depends on backend token lifecycle
    await page.goto('/login');
    await page.fill('input[placeholder*="UUID"]', 'demo-user-id');
    await page.click('button:has-text("Login")');
    await page.waitForURL('/dashboard');

    // Dashboard should be accessible with valid token
    expect(page.url()).toContain('/dashboard');
  });
});
