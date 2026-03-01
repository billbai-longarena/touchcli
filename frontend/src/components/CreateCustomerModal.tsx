import { useState } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/CreateCustomerModal.css';

interface CreateCustomerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function CreateCustomerModal({ isOpen, onClose, onSuccess }: CreateCustomerModalProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { customers, setCustomers } = useConversationStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !email.trim()) {
      setError('Please fill in required fields');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Generate a simple UUID-like ID for demo purposes
      // In production, this would come from the backend
      const newCustomerId = `cust_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;

      const newCustomer = {
        id: newCustomerId,
        user_id: '', // Would come from auth store
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Add to local state
      const updatedCustomers = [...customers, newCustomer];
      setCustomers(updatedCustomers);

      // Reset form
      setName('');
      setEmail('');
      setPhone('');
      onClose();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create customer');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Customer</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && <div className="modal-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="name">
              Customer Name <span className="required">*</span>
            </label>
            <input
              id="name"
              type="text"
              placeholder="e.g., Acme Corporation"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError('');
              }}
              disabled={loading}
              required
              maxLength={255}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">
              Email Address <span className="required">*</span>
            </label>
            <input
              id="email"
              type="email"
              placeholder="contact@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError('');
              }}
              disabled={loading}
              required
              maxLength={255}
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone (Optional)</label>
            <input
              id="phone"
              type="tel"
              placeholder="+1 (555) 123-4567"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                setError('');
              }}
              disabled={loading}
              maxLength={20}
            />
            <small className="hint">Optional: customer phone number</small>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-cancel"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-create"
              disabled={loading || !name.trim() || !email.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Creating...
                </>
              ) : (
                <>
                  <span>+</span>
                  Create Customer
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
