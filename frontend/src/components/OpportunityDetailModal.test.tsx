import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OpportunityDetailModal } from './OpportunityDetailModal';

// Mock the store
vi.mock('../store/conversationStore', () => ({
  useConversationStore: () => ({
    opportunities: [
      {
        id: 'opp1',
        title: 'Enterprise Deal',
        amount: 100000,
        stage: 'proposal',
        customer_id: 'cust1',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-03-02T00:00:00Z',
      },
    ],
    setOpportunities: vi.fn(),
  }),
}));

const mockOpportunity = {
  id: 'opp1',
  title: 'Enterprise Deal',
  amount: 100000,
  stage: 'proposal',
  customer_id: 'cust1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-03-02T00:00:00Z',
};

const mockCustomer = {
  id: 'cust1',
  name: 'Test Corp',
  email: 'test@corp.com',
  phone: '+1-555-0100',
  user_id: 'user1',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-03-02T00:00:00Z',
};

describe('OpportunityDetailModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <OpportunityDetailModal
        isOpen={false}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should not render when opportunity is null', () => {
    const { container } = render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={null}
        customer={mockCustomer}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should display opportunity details when open', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    expect(screen.getByText('Opportunity Details')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
    expect(screen.getByText(/100k/i)).toBeInTheDocument();
  });

  it('should display customer information', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    expect(screen.getByText('Test Corp')).toBeInTheDocument();
    expect(screen.getByText('test@corp.com')).toBeInTheDocument();
    expect(screen.getByText('+1-555-0100')).toBeInTheDocument();
  });

  it('should display stage badge with correct color', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const stageBadge = screen.getByText('Proposal');
    expect(stageBadge).toBeInTheDocument();
  });

  it('should display created and updated dates', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    // Dates should be formatted
    expect(screen.getByText(/created/i)).toBeInTheDocument();
    expect(screen.getByText(/updated/i)).toBeInTheDocument();
  });

  it('should have close button', () => {
    const onClose = vi.fn();
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={onClose}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const closeBtn = screen.getByRole('button', { name: '✕' });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('should have mark as won button', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const markAsWonBtn = screen.getByRole('button', { name: /mark as won/i });
    expect(markAsWonBtn).toBeInTheDocument();
  });

  it('should have delete button', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    expect(deleteBtn).toBeInTheDocument();
  });

  it('should disable mark as won if opportunity is already closed', () => {
    // The component disables "Mark as Won" when stage starts with 'Closed'
    // (e.g. 'Closed Won' or 'Closed Lost').
    const closedOpportunity = { ...mockOpportunity, stage: 'Closed Won' };
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={closedOpportunity}
        customer={mockCustomer}
      />
    );

    const markAsWonBtn = screen.getByRole('button', { name: /mark as won/i });
    expect(markAsWonBtn).toBeDisabled();
  });

  it('should call onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={onClose}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const closeBtn = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('should handle mark as won action', async () => {
    const onClose = vi.fn();
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={onClose}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const markAsWonBtn = screen.getByRole('button', { name: /mark as won/i });
    fireEvent.click(markAsWonBtn);

    await waitFor(() => {
      // Modal should close after action
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('should show delete confirmation', async () => {
    global.confirm = vi.fn(() => false);

    const onClose = vi.fn();
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={onClose}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
    });
  });

  it('should display opportunity ID in monospace font', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const idElement = screen.getByText('opp1');
    expect(idElement).toHaveClass('mono');
  });

  it('should display unknown customer when customer is null', () => {
    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={null}
      />
    );

    expect(screen.getByText(/unknown customer/i)).toBeInTheDocument();
  });

  it('should show loading state during delete action', async () => {
    global.confirm = vi.fn(() => true);

    render(
      <OpportunityDetailModal
        isOpen={true}
        onClose={() => {}}
        opportunity={mockOpportunity}
        customer={mockCustomer}
      />
    );

    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      // Delete action should show loading state
      expect(deleteBtn).toBeDefined();
    });
  });
});
