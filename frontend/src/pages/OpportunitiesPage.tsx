import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useConversationStore, type Opportunity } from '../store/conversationStore';
import { CreateOpportunityModal } from '../components/CreateOpportunityModal';
import { OpportunityDetailModal } from '../components/OpportunityDetailModal';
import '../styles/OpportunitiesPage.css';

export function OpportunitiesPage() {
  const [searchParams] = useSearchParams();
  const { opportunities, customers, fetchOpportunities, loading, error } =
    useConversationStore();
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCustomerId, setFilterCustomerId] = useState<string>(searchParams.get('customer') || '');
  const [sortBy, setSortBy] = useState<'amount' | 'date'>('amount');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  // filterCustomerId is initialized directly from searchParams above;
  // update it if the URL param changes after mount
  useEffect(() => {
    const customerParam = searchParams.get('customer') ?? '';
    setFilterCustomerId(customerParam);
  }, [searchParams]);

  const filteredOpportunities = opportunities
    .filter((opp) => !filterStatus || opp.stage === filterStatus)
    .filter((opp) => !filterCustomerId || opp.customer_id === filterCustomerId)
    .sort((a, b) => {
      if (sortBy === 'amount') {
        return b.amount - a.amount;
      } else {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      }
    });

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'discovery':
        return '#3b82f6';
      case 'proposal':
        return '#8b5cf6';
      case 'negotiation':
        return '#f59e0b';
      case 'closed':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getStageLabel = (stage: string) => {
    return stage.charAt(0).toUpperCase() + stage.slice(1);
  };

  const totalPipeline = filteredOpportunities.reduce((sum, opp) => sum + opp.amount, 0);

  const handleOpenDetail = (opp: Opportunity) => {
    setSelectedOpportunity(opp);
    setIsDetailModalOpen(true);
  };

  return (
    <div className="opportunities-page">
      <CreateOpportunityModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
      <OpportunityDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedOpportunity(null);
        }}
        opportunity={selectedOpportunity}
        customer={selectedOpportunity ? customers.find((c) => c.id === selectedOpportunity.customer_id) ?? null : null}
      />
      <div className="opps-header">
        <h1>Opportunities</h1>
        <button className="new-opp-btn" onClick={() => setIsModalOpen(true)}>
          + New Opportunity
        </button>
      </div>

      <div className="opps-filters">
        <div className="filter-group">
          <label>Status</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">All Stages</option>
            <option value="discovery">Discovery</option>
            <option value="proposal">Proposal</option>
            <option value="negotiation">Negotiation</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Customer</label>
          <select value={filterCustomerId} onChange={(e) => setFilterCustomerId(e.target.value)}>
            <option value="">All Customers</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Sort By</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as 'amount' | 'date')}>
            <option value="amount">Amount (High to Low)</option>
            <option value="date">Date Updated</option>
          </select>
        </div>
      </div>

      <div className="opps-content">
        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="loading">Loading opportunities...</div>
        ) : filteredOpportunities.length === 0 ? (
          <div className="empty-state">No opportunities match your filters</div>
        ) : (
          <>
            <div className="opps-summary">
              <div className="summary-card">
                <p className="summary-label">Total Opportunities</p>
                <p className="summary-value">{filteredOpportunities.length}</p>
              </div>
              <div className="summary-card">
                <p className="summary-label">Pipeline Value</p>
                <p className="summary-value">${(totalPipeline / 1000).toFixed(0)}K</p>
              </div>
              <div className="summary-card">
                <p className="summary-label">Average Deal Size</p>
                <p className="summary-value">
                  ${(totalPipeline / filteredOpportunities.length / 1000).toFixed(0)}K
                </p>
              </div>
            </div>

            <div className="opps-list">
              {filteredOpportunities.map((opp) => {
                const customer = customers.find((c) => c.id === opp.customer_id);
                return (
                  <div key={opp.id} className="opp-card" onClick={() => handleOpenDetail(opp)} style={{ cursor: 'pointer' }}>
                    <div className="opp-card-header">
                      <div className="opp-title">
                        <h3>{opp.title}</h3>
                        <span
                          className="stage-badge"
                          style={{ backgroundColor: getStageColor(opp.stage) }}
                        >
                          {getStageLabel(opp.stage)}
                        </span>
                      </div>
                      <div className="opp-amount">${(opp.amount / 1000).toFixed(0)}K</div>
                    </div>

                    <div className="opp-card-body">
                      <div className="opp-field">
                        <span className="label">Customer</span>
                        <span className="value">{customer?.name || 'Unknown'}</span>
                      </div>
                      <div className="opp-field">
                        <span className="label">Updated</span>
                        <span className="value">
                          {new Date(opp.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    <div className="opp-card-footer">
                      <small>Click to view details</small>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
