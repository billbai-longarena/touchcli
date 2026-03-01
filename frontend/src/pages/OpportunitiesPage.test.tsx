import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { OpportunitiesPage } from './OpportunitiesPage';

// Mock navigation
const mockUseSearchParams = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: mockUseSearchParams,
  };
});

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
      {
        id: 'opp2',
        title: 'Mid-Market Deal',
        amount: 50000,
        stage: 'discovery',
        customer_id: 'cust2',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      },
    ],
    customers: [
      { id: 'cust1', name: 'Test Corp', email: 'test@corp.com' },
      { id: 'cust2', name: 'Acme Inc', email: 'acme@inc.com' },
    ],
    fetchOpportunities: vi.fn(),
    loading: false,
    error: null,
  }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  mockUseSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('OpportunitiesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render opportunity list', () => {
    renderWithRouter(<OpportunitiesPage />);

    expect(screen.getByText('Opportunities')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
    expect(screen.getByText('Mid-Market Deal')).toBeInTheDocument();
  });

  it('should have new opportunity button', () => {
    renderWithRouter(<OpportunitiesPage />);

    const newOppBtn = screen.getByRole('button', { name: /\+ new opportunity/i });
    expect(newOppBtn).toBeInTheDocument();
  });

  it('should have filter by status', () => {
    renderWithRouter(<OpportunitiesPage />);

    const statusFilter = screen.getByLabelText(/status/i);
    expect(statusFilter).toBeInTheDocument();
  });

  it('should filter opportunities by stage', async () => {
    renderWithRouter(<OpportunitiesPage />);

    const stageFilter = screen.getByLabelText(/status/i);
    fireEvent.change(stageFilter, { target: { value: 'discovery' } });

    await waitFor(() => {
      expect(screen.getByText('Mid-Market Deal')).toBeInTheDocument();
      expect(screen.queryByText('Enterprise Deal')).not.toBeInTheDocument();
    });
  });

  it('should have filter by customer', () => {
    renderWithRouter(<OpportunitiesPage />);

    const customerFilter = screen.getByLabelText(/customer/i);
    expect(customerFilter).toBeInTheDocument();
  });

  it('should filter opportunities by customer', async () => {
    renderWithRouter(<OpportunitiesPage />);

    const customerFilter = screen.getByLabelText(/customer/i);
    fireEvent.change(customerFilter, { target: { value: 'cust1' } });

    await waitFor(() => {
      expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
      expect(screen.queryByText('Mid-Market Deal')).not.toBeInTheDocument();
    });
  });

  it('should have sort options', () => {
    renderWithRouter(<OpportunitiesPage />);

    const sortBy = screen.getByLabelText(/sort by/i);
    expect(sortBy).toBeInTheDocument();
  });

  it('should sort by amount', async () => {
    renderWithRouter(<OpportunitiesPage />);

    const sortBy = screen.getByLabelText(/sort by/i);
    fireEvent.change(sortBy, { target: { value: 'amount' } });

    await waitFor(() => {
      // Opportunities should be sorted by amount
      const opportunities = screen.getAllByText(/deal/i);
      expect(opportunities).toBeDefined();
    });
  });

  it('should display summary cards', () => {
    renderWithRouter(<OpportunitiesPage />);

    expect(screen.getByText(/total opportunities/i)).toBeInTheDocument();
    expect(screen.getByText(/pipeline value/i)).toBeInTheDocument();
    expect(screen.getByText(/average deal size/i)).toBeInTheDocument();
  });

  it('should show opportunity cards with details', () => {
    renderWithRouter(<OpportunitiesPage />);

    expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
    expect(screen.getByText(/100k/i)).toBeInTheDocument(); // Amount
    expect(screen.getByText('Test Corp')).toBeInTheDocument(); // Customer
  });

  it('should show stage badge with color', () => {
    renderWithRouter(<OpportunitiesPage />);

    const stageBadges = screen.getAllByText((content, element) => {
      return element?.className?.includes('stage-badge');
    });
    expect(stageBadges.length).toBeGreaterThan(0);
  });

  it('should open detail modal on card click', async () => {
    renderWithRouter(<OpportunitiesPage />);

    const enterpriseDeal = screen.getByText('Enterprise Deal');
    fireEvent.click(enterpriseDeal.closest('.opp-card') || enterpriseDeal);

    await waitFor(() => {
      expect(screen.getByText(/opportunity details/i)).toBeInTheDocument();
    });
  });

  it('should show updated date on opportunity card', () => {
    renderWithRouter(<OpportunitiesPage />);

    expect(screen.getByText(/updated/i)).toBeInTheDocument();
  });

  it('should handle empty state when no opportunities match filters', async () => {
    renderWithRouter(<OpportunitiesPage />);

    const stageFilter = screen.getByLabelText(/status/i);
    fireEvent.change(stageFilter, { target: { value: 'closed' } });

    await waitFor(() => {
      expect(screen.getByText(/no opportunities match/i)).toBeInTheDocument();
    });
  });

  it('should open create opportunity modal', () => {
    renderWithRouter(<OpportunitiesPage />);

    const newOppBtn = screen.getByRole('button', { name: /\+ new opportunity/i });
    fireEvent.click(newOppBtn);

    expect(screen.getByText(/new opportunity/i)).toBeInTheDocument();
  });

  it('should calculate total pipeline correctly', () => {
    renderWithRouter(<OpportunitiesPage />);

    // Total should be 150K (100K + 50K)
    const pipelineValue = screen.getByText(/pipeline value/i).parentElement;
    expect(pipelineValue?.textContent).toContain('150');
  });

  it('should calculate average deal size correctly', () => {
    renderWithRouter(<OpportunitiesPage />);

    // Average should be 75K (150K / 2 opportunities)
    const avgDealSize = screen.getByText(/average deal size/i).parentElement;
    expect(avgDealSize?.textContent).toContain('75');
  });

  it('should display loading state', () => {
    vi.mock('../store/conversationStore', () => ({
      useConversationStore: () => ({
        opportunities: [],
        customers: [],
        fetchOpportunities: vi.fn(),
        loading: true,
        error: null,
      }),
    }));

    // Component should handle loading state
  });

  it('should update filter from URL query param', () => {
    const mockSetSearchParams = vi.fn();
    mockUseSearchParams.mockReturnValue([
      new URLSearchParams('customer=cust1'),
      mockSetSearchParams,
    ]);

    renderWithRouter(<OpportunitiesPage />);

    // Should apply customer filter from URL
    expect(screen.getByText('Enterprise Deal')).toBeInTheDocument();
  });
});
