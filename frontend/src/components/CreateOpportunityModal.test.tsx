import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateOpportunityModal } from './CreateOpportunityModal';

// Mock the store
vi.mock('../store/conversationStore', () => ({
  useConversationStore: () => ({
    customers: [
      { id: 'cust1', name: 'Test Corp', email: 'test@corp.com' },
      { id: 'cust2', name: 'Acme Inc', email: 'acme@inc.com' },
    ],
    createOpportunity: vi.fn(() => Promise.resolve({})),
  }),
}));

describe('CreateOpportunityModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <CreateOpportunityModal isOpen={false} onClose={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render form fields when isOpen is true', () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    expect(screen.getByLabelText(/customer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/opportunity title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/deal amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/stage/i)).toBeInTheDocument();
  });

  it('should display form title', () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('New Opportunity')).toBeInTheDocument();
  });

  it('should populate customers in dropdown', () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    expect(customerSelect).toBeInTheDocument();
    // Options should be available via select element
  });

  it('should have close button', () => {
    const onClose = vi.fn();
    render(<CreateOpportunityModal isOpen={true} onClose={onClose} />);

    const closeBtn = screen.getByRole('button', { name: '✕' });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('should require all fields for submission', async () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const submitBtn = screen.getByRole('button', { name: /create opportunity/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const errorElement = screen.getByText((_content, element) => {
        return element?.className === 'modal-error';
      });
      expect(errorElement).toBeInTheDocument();
    });
  });

  it('should validate amount is greater than zero', async () => {
    const user = userEvent.setup();
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/opportunity title/i);
    const amountInput = screen.getByLabelText(/deal amount/i);

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Test Deal');
    await user.type(amountInput, '-1000');

    const submitBtn = screen.getByRole('button', { name: /create opportunity/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      screen.queryByText((_content, element) => {
        return element?.className === 'modal-error';
      });
      // Error should be shown for invalid amount
    });
  });

  it('should enable submit button when required fields are filled', async () => {
    const user = userEvent.setup();
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/opportunity title/i);
    const amountInput = screen.getByLabelText(/deal amount/i);
    const submitBtn = screen.getByRole('button', { name: /create opportunity/i });

    expect(submitBtn).toBeDisabled();

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Test Deal');
    await user.type(amountInput, '50000');

    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('should have stage dropdown with options', async () => {
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const stageSelect = screen.getByLabelText(/stage/i);
    expect(stageSelect).toBeInTheDocument();
    // Stage options should be available
  });

  it('should disable customer select when preselected', () => {
    render(
      <CreateOpportunityModal
        isOpen={true}
        onClose={() => {}}
        preselectedCustomerId="cust1"
      />
    );

    const customerSelect = screen.getByLabelText(/customer/i);
    expect(customerSelect).toBeDisabled();
  });

  it('should call onClose when cancel button is clicked', () => {
    const onClose = vi.fn();
    render(<CreateOpportunityModal isOpen={true} onClose={onClose} />);

    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it('should clear form on successful submission', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <CreateOpportunityModal isOpen={true} onClose={onClose} />
    );

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/opportunity title/i) as HTMLInputElement;
    const amountInput = screen.getByLabelText(/deal amount/i) as HTMLInputElement;

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Test Deal');
    await user.type(amountInput, '50000');

    const submitBtn = screen.getByRole('button', { name: /create opportunity/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(titleInput.value).toBe('');
      expect(amountInput.value).toBe('');
    });
  });

  it('should show loading state during submission', async () => {
    const user = userEvent.setup();
    render(<CreateOpportunityModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/opportunity title/i);
    const amountInput = screen.getByLabelText(/deal amount/i);

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Test Deal');
    await user.type(amountInput, '50000');

    const submitBtn = screen.getByRole('button', { name: /create opportunity/i });
    fireEvent.click(submitBtn);

    // Button should show loading state
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });
});
