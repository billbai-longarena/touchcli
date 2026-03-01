import React from 'react';
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import type { RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';

/**
 * Custom render function that wraps components with necessary providers
 */
function AllTheProviders({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllTheProviders, ...options });
}

export * from '@testing-library/react';
export { customRender as render };

/**
 * Mock API client for testing
 */
export const mockApiClient = {
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
};

/**
 * Mock auth context
 */
export const mockAuthContext = {
  user: {
    id: 'test-user-id',
    email: 'test@example.com',
  },
  token: 'test-token',
  login: vi.fn(),
  logout: vi.fn(),
};

/**
 * Create a mock conversation
 */
export function createMockConversation(overrides = {}) {
  return {
    id: 'conv-1',
    user_id: 'user-1',
    customer_id: 'cust-1',
    title: 'Test Conversation',
    status: 'active',
    created_at: '2026-03-02T00:00:00Z',
    updated_at: '2026-03-02T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create a mock message
 */
export function createMockMessage(overrides = {}) {
  return {
    id: 'msg-1',
    conversation_id: 'conv-1',
    user_id: 'user-1',
    content: 'Test message',
    created_at: '2026-03-02T00:00:00Z',
    status: 'sent' as const,
    ...overrides,
  };
}

/**
 * Create a mock opportunity
 */
export function createMockOpportunity(overrides = {}) {
  return {
    id: 'opp-1',
    customer_id: 'cust-1',
    title: 'Test Opportunity',
    amount: 50000,
    stage: 'Prospecting',
    created_at: '2026-03-02T00:00:00Z',
    updated_at: '2026-03-02T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create a mock customer
 */
export function createMockCustomer(overrides = {}) {
  return {
    id: 'cust-1',
    user_id: 'user-1',
    name: 'Test Customer',
    email: 'customer@example.com',
    phone: '+1234567890',
    created_at: '2026-03-02T00:00:00Z',
    updated_at: '2026-03-02T00:00:00Z',
    ...overrides,
  };
}
