import { useState, useEffect } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/CreateConversationModal.css';

interface CreateConversationModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedCustomerId?: string;
  onSuccess?: () => void;
}

export function CreateConversationModal({ isOpen, onClose, preselectedCustomerId, onSuccess }: CreateConversationModalProps) {
  const [title, setTitle] = useState('');
  const [selectedCustomerId, setSelectedCustomerId] = useState(preselectedCustomerId || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Sync form state when modal opens or preselectedCustomerId changes
  useEffect(() => {
    if (isOpen) {
      setSelectedCustomerId(preselectedCustomerId || '');
      setTitle('');
      setError('');
    }
  }, [isOpen, preselectedCustomerId]);

  const { customers, createConversation } = useConversationStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !selectedCustomerId) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await createConversation(selectedCustomerId, title.trim());
      setTitle('');
      if (!preselectedCustomerId) {
        setSelectedCustomerId('');
      }
      onClose();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Conversation</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {error && <div className="modal-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="customer">Select Customer</label>
            <select
              id="customer"
              value={selectedCustomerId}
              onChange={(e) => {
                setSelectedCustomerId(e.target.value);
                setError('');
              }}
              disabled={loading || !!preselectedCustomerId}
            >
              <option value="">-- Choose a customer --</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} ({customer.email})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="title">Conversation Title</label>
            <input
              id="title"
              type="text"
              placeholder="e.g., Q1 Sales Discussion"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setError('');
              }}
              disabled={loading}
              maxLength={100}
            />
            <small className="hint">{title.length}/100</small>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose} disabled={loading} className="btn-cancel">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim() || !selectedCustomerId}
              className="btn-create"
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Creating...
                </>
              ) : (
                <>
                  <span>+</span>
                  Create
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
