import { useState } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/CreateOpportunityModal.css';

interface CreateOpportunityModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedCustomerId?: string;
}

const STAGES = ['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'];

export function CreateOpportunityModal({
  isOpen,
  onClose,
  preselectedCustomerId,
}: CreateOpportunityModalProps) {
  const [customerId, setCustomerId] = useState(preselectedCustomerId || '');
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [stage, setStage] = useState('Prospecting');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { customers, createOpportunity } = useConversationStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!customerId || !title.trim() || !amount) {
      setError('Please fill in all required fields');
      return;
    }

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await createOpportunity({
        customer_id: customerId,
        title: title.trim(),
        amount: parsedAmount,
        stage,
      });

      // Reset form and close
      setTitle('');
      setAmount('');
      setStage('Prospecting');
      if (!preselectedCustomerId) {
        setCustomerId('');
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create opportunity');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Opportunity</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && <div className="modal-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="customer">
              Customer <span className="required">*</span>
            </label>
            <select
              id="customer"
              value={customerId}
              onChange={(e) => {
                setCustomerId(e.target.value);
                setError('');
              }}
              disabled={loading || !!preselectedCustomerId}
              required
            >
              <option value="">-- Select a customer --</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} ({customer.email})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="title">
              Opportunity Title <span className="required">*</span>
            </label>
            <input
              id="title"
              type="text"
              placeholder="e.g., Enterprise License Deal"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setError('');
              }}
              disabled={loading}
              required
              maxLength={255}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="amount">
                Deal Amount ($) <span className="required">*</span>
              </label>
              <input
                id="amount"
                type="number"
                placeholder="50000"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value);
                  setError('');
                }}
                disabled={loading}
                required
                min="0"
                step="1000"
              />
            </div>

            <div className="form-group">
              <label htmlFor="stage">
                Stage <span className="required">*</span>
              </label>
              <select
                id="stage"
                value={stage}
                onChange={(e) => {
                  setStage(e.target.value);
                  setError('');
                }}
                disabled={loading}
                required
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="cancel-btn"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !customerId || !title.trim() || !amount}
            >
              {loading ? 'Creating...' : 'Create Opportunity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
