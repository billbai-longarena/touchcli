import { test, expect, type Page } from '@playwright/test';

async function loginWithPassword(page: Page) {
  await page.goto('/login');
  await page.click('button:has-text("Password Login")');
  await page.fill('input[id="account"]', 'alice');
  await page.fill('input[id="password"]', 'touchcli123');
  await page.click('button:has-text("Login")');
  await page.waitForURL('/dashboard');
}

test.describe('Authentication Flow', () => {
  test('should display login page on initial load', async ({ page }) => {
    await page.goto('/');

    expect(page.url()).toContain('/login');
    expect(await page.locator('button:has-text("SMS Login")')).toBeVisible();
    expect(await page.locator('button:has-text("Password Login")')).toBeVisible();
  });

  test('should login with username and password', async ({ page }) => {
    await loginWithPassword(page);
    expect(page.url()).toContain('/dashboard');
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.click('button:has-text("Password Login")');
    await page.fill('input[id="account"]', 'alice');
    await page.fill('input[id="password"]', 'wrong-password');
    await page.click('button:has-text("Login")');

    await expect(page.locator('text=/invalid username or password/i')).toBeVisible();
  });

  test('should display dashboard with navigation after login', async ({ page }) => {
    await loginWithPassword(page);

    expect(await page.locator('button:has-text("Conversations")')).toBeVisible();
    expect(await page.locator('button:has-text("Customers")')).toBeVisible();
    expect(await page.locator('button:has-text("Opportunities")')).toBeVisible();
  });

  test('should persist session across page reloads', async ({ page }) => {
    await loginWithPassword(page);
    await page.reload();
    expect(page.url()).toContain('/dashboard');
  });
});
