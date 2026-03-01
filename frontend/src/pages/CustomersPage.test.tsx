import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { CustomersPage } from './CustomersPage';

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the store
vi.mock('../store/conversationStore', () => ({
  useConversationStore: () => ({
    customers: [
      {
        id: 'cust1',
        name: 'Test Corp',
        email: 'test@corp.com',
        phone: '+1-555-0100',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-03-02T00:00:00Z',
      },
      {
        id: 'cust2',
        name: 'Acme Inc',
        email: 'acme@inc.com',
        phone: '+1-555-0200',
        created_at: '2026-01-15T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      },
    ],
    fetchCustomers: vi.fn(),
    loading: false,
    error: null,
  }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('CustomersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render customer list', () => {
    renderWithRouter(<CustomersPage />);

    expect(screen.getByText('Customers')).toBeInTheDocument();
    expect(screen.getByText('Test Corp')).toBeInTheDocument();
    expect(screen.getByText('Acme Inc')).toBeInTheDocument();
  });

  it('should have search input', () => {
    renderWithRouter(<CustomersPage />);

    const searchInput = screen.getByPlaceholderText(/search customers/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('should filter customers by name', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const searchInput = screen.getByPlaceholderText(/search customers/i);
    await user.type(searchInput, 'Acme');

    expect(screen.getByText('Acme Inc')).toBeInTheDocument();
    expect(screen.queryByText('Test Corp')).not.toBeInTheDocument();
  });

  it('should filter customers by email', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const searchInput = screen.getByPlaceholderText(/search customers/i);
    await user.type(searchInput, 'test@corp');

    expect(screen.getByText('Test Corp')).toBeInTheDocument();
  });

  it('should display customer detail panel when selected', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    // Detail panel should show
    expect(screen.getByText(/contact information/i)).toBeInTheDocument();
  });

  it('should display selected customer details', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    expect(screen.getByText('test@corp.com')).toBeInTheDocument();
    expect(screen.getByText('+1-555-0100')).toBeInTheDocument();
  });

  it('should have create customer button', () => {
    renderWithRouter(<CustomersPage />);

    const createBtn = screen.getByRole('button', { name: '+' });
    expect(createBtn).toBeInTheDocument();
  });

  it('should have start conversation button', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    const startConvBtn = screen.getByRole('button', { name: /start conversation/i });
    expect(startConvBtn).toBeInTheDocument();
  });

  it('should open conversation modal when start conversation is clicked', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    const startConvBtn = screen.getByRole('button', { name: /start conversation/i });
    fireEvent.click(startConvBtn);

    // Modal should appear
    await waitFor(() => {
      expect(screen.getByText(/new conversation/i)).toBeInTheDocument();
    });
  });

  it('should have view opportunities button', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    const viewOppBtn = screen.getByRole('button', { name: /view opportunities/i });
    expect(viewOppBtn).toBeInTheDocument();
  });

  it('should navigate to opportunities with customer filter', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    const viewOppBtn = screen.getByRole('button', { name: /view opportunities/i });
    fireEvent.click(viewOppBtn);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        expect.stringContaining('/opportunities')
      );
    });
  });

  it('should show empty detail state when no customer selected', () => {
    renderWithRouter(<CustomersPage />);

    expect(screen.getByText(/select a customer/i)).toBeInTheDocument();
  });

  it('should clear search when all customers filtered out', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const searchInput = screen.getByPlaceholderText(/search customers/i) as HTMLInputElement;
    await user.type(searchInput, 'NonExistent');

    expect(screen.getByText(/no customers match your search/i)).toBeInTheDocument();

    // Clear search
    await user.clear(searchInput);

    expect(screen.getByText('Test Corp')).toBeInTheDocument();
  });

  it('should display customer creation date', async () => {
    const user = userEvent.setup();
    renderWithRouter(<CustomersPage />);

    const customerItem = screen.getByText('Test Corp');
    await user.click(customerItem);

    // Should show created date in detail panel
    expect(screen.getByText(/created/i)).toBeInTheDocument();
  });
});
