import { useState } from 'react';
import { useConversationStore, type Opportunity, type Customer } from '../store/conversationStore';
import '../styles/OpportunityDetailModal.css';

interface OpportunityDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  opportunity: Opportunity | null;
  customer: Customer | null;
}

export function OpportunityDetailModal({
  isOpen,
  onClose,
  opportunity,
  customer,
}: OpportunityDetailModalProps) {
  const { setOpportunities, opportunities } = useConversationStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen || !opportunity) return null;

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this opportunity?')) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // In a real app, this would call the API
      // For now, remove from local state
      const updated = opportunities.filter((opp) => opp.id !== opportunity.id);
      setOpportunities(updated);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete opportunity');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsWon = async () => {
    setLoading(true);
    setError('');

    try {
      const updated = opportunities.map((opp) =>
        opp.id === opportunity.id ? { ...opp, stage: 'Closed Won' } : opp
      );
      setOpportunities(updated);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update opportunity');
    } finally {
      setLoading(false);
    }
  };

  const stageColors: Record<string, string> = {
    'Prospecting': '#3b82f6',
    'Qualification': '#60a5fa',
    'Proposal': '#8b5cf6',
    'Negotiation': '#f59e0b',
    'Closed Won': '#10b981',
    'Closed Lost': '#ef4444',
  };

  const stageColor = stageColors[opportunity.stage] || '#6b7280';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Opportunity Details</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-content">
          {error && <div className="modal-error">{error}</div>}

          <div className="detail-section">
            <div className="detail-row">
              <div className="detail-field">
                <label>Title</label>
                <h3>{opportunity.title}</h3>
              </div>
              <div className="detail-field">
                <label>Amount</label>
                <p className="amount">${(opportunity.amount / 1000).toFixed(0)}K</p>
              </div>
            </div>

            <div className="detail-row">
              <div className="detail-field">
                <label>Customer</label>
                <p>{customer?.name || 'Unknown Customer'}</p>
              </div>
              <div className="detail-field">
                <label>Stage</label>
                <span className="stage-badge" style={{ backgroundColor: stageColor }}>
                  {opportunity.stage.charAt(0).toUpperCase() + opportunity.stage.slice(1)}
                </span>
              </div>
            </div>

            <div className="detail-row">
              <div className="detail-field">
                <label>Created</label>
                <p>{new Date(opportunity.created_at).toLocaleDateString()}</p>
              </div>
              <div className="detail-field">
                <label>Updated</label>
                <p>{new Date(opportunity.updated_at).toLocaleDateString()}</p>
              </div>
            </div>

            {customer && (
              <div className="detail-row">
                <div className="detail-field">
                  <label>Customer Email</label>
                  <p>{customer.email}</p>
                </div>
                {customer.phone && (
                  <div className="detail-field">
                    <label>Customer Phone</label>
                    <p>{customer.phone}</p>
                  </div>
                )}
              </div>
            )}

            <div className="detail-row">
              <div className="detail-field">
                <label>Opportunity ID</label>
                <p className="mono">{opportunity.id}</p>
              </div>
            </div>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn-cancel"
            >
              Close
            </button>
            <button
              type="button"
              onClick={handleMarkAsWon}
              disabled={loading || opportunity.stage.startsWith('Closed')}
              className="btn-secondary"
            >
              {loading ? 'Updating...' : 'Mark as Won'}
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={loading}
              className="btn-delete"
            >
              {loading ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
