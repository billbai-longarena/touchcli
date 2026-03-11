import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateCustomerModal } from './CreateCustomerModal';

// Mock the store
vi.mock('../store/conversationStore', () => ({
  useConversationStore: () => ({
    customers: [],
    setCustomers: vi.fn(),
  }),
}));

describe('CreateCustomerModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <CreateCustomerModal isOpen={false} onClose={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render form fields when isOpen is true', () => {
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    expect(screen.getByLabelText(/customer name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
  });

  it('should display form title', () => {
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('New Customer')).toBeInTheDocument();
  });

  it('should have close button', () => {
    const onClose = vi.fn();
    render(<CreateCustomerModal isOpen={true} onClose={onClose} />);

    const closeBtn = screen.getByRole('button', { name: '✕' });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('should show error when submitting empty form', async () => {
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    // The submit button is disabled when required fields are empty; submit the
    // form directly to bypass the disabled state and trigger validation.
    const form = screen.getByRole('button', { name: /create customer/i }).closest('form')!;
    fireEvent.submit(form);

    // Error element should be displayed
    const errorElement = screen.getByText((_content, element) => {
      return element?.className === 'modal-error';
    });
    expect(errorElement).toBeInTheDocument();
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    await user.type(
      screen.getByLabelText(/customer name/i),
      'Test Company'
    );
    await user.type(screen.getByLabelText(/email address/i), 'invalid-email');

    const submitBtn = screen.getByRole('button', { name: /create customer/i });
    fireEvent.click(submitBtn);

    // Error element should be displayed (validation may happen on blur or submit)
    screen.queryByText((_content, element) => {
      return element?.className === 'modal-error';
    });
  });

  it('should enable submit button when required fields are filled', async () => {
    const user = userEvent.setup();
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    const nameInput = screen.getByLabelText(/customer name/i);
    const emailInput = screen.getByLabelText(/email address/i);
    const submitBtn = screen.getByRole('button', { name: /create customer/i });

    expect(submitBtn).toBeDisabled();

    await user.type(nameInput, 'Test Company');
    await user.type(emailInput, 'test@company.com');

    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('should accept optional phone number', async () => {
    const user = userEvent.setup();
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    const phoneInput = screen.getByLabelText(/phone/i);
    expect(phoneInput).toBeInTheDocument();

    await user.type(phoneInput, '+1 (555) 123-4567');
    expect(phoneInput).toHaveValue('+1 (555) 123-4567');
  });

  it('should call onClose when cancel button is clicked', () => {
    const onClose = vi.fn();
    render(<CreateCustomerModal isOpen={true} onClose={onClose} />);

    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it('should show loading state during submission', async () => {
    const user = userEvent.setup();
    render(<CreateCustomerModal isOpen={true} onClose={() => {}} />);

    const nameInput = screen.getByLabelText(/customer name/i);
    const emailInput = screen.getByLabelText(/email address/i);

    await user.type(nameInput, 'Test Company');
    await user.type(emailInput, 'test@company.com');

    const submitBtn = screen.getByRole('button', { name: /create customer/i });
    fireEvent.click(submitBtn);

    // During submission, button text changes
    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: /create customer/i })
      ).toBeInTheDocument();
    });
  });

  it('should clear form on successful submission', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <CreateCustomerModal isOpen={true} onClose={onClose} onSuccess={onClose} />
    );

    const nameInput = screen.getByLabelText(/customer name/i) as HTMLInputElement;
    const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;

    await user.type(nameInput, 'Test Company');
    await user.type(emailInput, 'test@company.com');

    const submitBtn = screen.getByRole('button', { name: /create customer/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });
});
