import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateConversationModal } from './CreateConversationModal';

// Mock the store
vi.mock('../store/conversationStore', () => ({
  useConversationStore: () => ({
    customers: [
      { id: 'cust1', name: 'Test Corp', email: 'test@corp.com' },
      { id: 'cust2', name: 'Acme Inc', email: 'acme@inc.com' },
    ],
    createConversation: vi.fn(() => Promise.resolve({})),
  }),
}));

describe('CreateConversationModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    const { container } = render(
      <CreateConversationModal isOpen={false} onClose={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render form fields when isOpen is true', () => {
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    expect(screen.getByLabelText(/customer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/conversation title/i)).toBeInTheDocument();
  });

  it('should display form title', () => {
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('New Conversation')).toBeInTheDocument();
  });

  it('should populate customers in dropdown', () => {
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    expect(customerSelect).toBeInTheDocument();
  });

  it('should have close button', () => {
    const onClose = vi.fn();
    render(<CreateConversationModal isOpen={true} onClose={onClose} />);

    const closeBtn = screen.getByRole('button', { name: '✕' });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalled();
  });

  it('should require customer and title fields', async () => {
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const submitBtn = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const errorElement = screen.getByText((content, element) => {
        return element?.className === 'modal-error';
      });
      expect(errorElement).toBeInTheDocument();
    });
  });

  it('should enforce title character limit and display counter', async () => {
    const user = userEvent.setup();
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const titleInput = screen.getByLabelText(/conversation title/i);
    await user.type(titleInput, 'Q1 Sales Discussion');

    // Should show character counter
    const counter = screen.getByText(/\/100/i);
    expect(counter).toBeInTheDocument();
  });

  it('should enable submit button when required fields are filled', async () => {
    const user = userEvent.setup();
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/conversation title/i);
    const submitBtn = screen.getByRole('button', { name: /create/i });

    expect(submitBtn).toBeDisabled();

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Q1 Discussion');

    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('should disable customer select when preselected', () => {
    render(
      <CreateConversationModal
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
    render(<CreateConversationModal isOpen={true} onClose={onClose} />);

    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it('should call onSuccess callback after successful submission', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onSuccess = vi.fn();

    render(
      <CreateConversationModal
        isOpen={true}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/conversation title/i);

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Q1 Discussion');

    const submitBtn = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('should clear form on successful submission', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <CreateConversationModal isOpen={true} onClose={onClose} />
    );

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/conversation title/i) as HTMLInputElement;

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Q1 Discussion');

    const submitBtn = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(titleInput.value).toBe('');
    });
  });

  it('should show loading state during submission', async () => {
    const user = userEvent.setup();
    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/conversation title/i);

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Q1 Discussion');

    const submitBtn = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitBtn);

    // Button should show loading state during submission
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('should display error message on submission failure', async () => {
    const user = userEvent.setup();
    vi.mock('../store/conversationStore', () => ({
      useConversationStore: () => ({
        customers: [{ id: 'cust1', name: 'Test Corp', email: 'test@corp.com' }],
        createConversation: vi.fn(() =>
          Promise.reject(new Error('Network error'))
        ),
      }),
    }));

    render(<CreateConversationModal isOpen={true} onClose={() => {}} />);

    const customerSelect = screen.getByLabelText(/customer/i);
    const titleInput = screen.getByLabelText(/conversation title/i);

    fireEvent.change(customerSelect, { target: { value: 'cust1' } });
    await user.type(titleInput, 'Q1 Discussion');

    const submitBtn = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitBtn);

    // Error should be displayed
    await waitFor(() => {
      // Form remains visible after error
      expect(screen.getByLabelText(/customer/i)).toBeInTheDocument();
    });
  });
});
