import { useState, useEffect } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/CustomersPage.css';

export function CustomersPage() {
  const { customers, fetchCustomers, loading, error } = useConversationStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  const filteredCustomers = customers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedCustomer = customers.find((c) => c.id === selectedCustomerId);

  return (
    <div className="customers-page">
      <div className="customers-container">
        <div className="customers-sidebar">
          <div className="sidebar-header">
            <h2>Customers</h2>
            <button className="new-customer-btn" title="Create new customer">
              +
            </button>
          </div>

          <div className="search-box">
            <input
              type="text"
              placeholder="Search customers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="customers-list">
            {loading ? (
              <div className="loading">Loading customers...</div>
            ) : filteredCustomers.length === 0 ? (
              <div className="empty-state">
                {searchTerm ? 'No customers match your search' : 'No customers yet'}
              </div>
            ) : (
              filteredCustomers.map((customer) => (
                <div
                  key={customer.id}
                  className={`customer-item ${selectedCustomerId === customer.id ? 'active' : ''}`}
                  onClick={() => setSelectedCustomerId(customer.id)}
                >
                  <div className="customer-item-header">
                    <h3>{customer.name}</h3>
                    <span className="customer-id">{customer.id.slice(0, 8)}...</span>
                  </div>
                  <p className="customer-email">{customer.email}</p>
                  <span className="customer-date">
                    {new Date(customer.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="customer-detail">
          {selectedCustomer ? (
            <div className="detail-panel">
              <div className="detail-header">
                <h2>{selectedCustomer.name}</h2>
                <button className="detail-action-btn" title="More actions">
                  ⋮
                </button>
              </div>

              <div className="detail-content">
                <div className="detail-section">
                  <h3>Contact Information</h3>
                  <div className="detail-field">
                    <label>Email</label>
                    <p>{selectedCustomer.email}</p>
                  </div>
                  {selectedCustomer.phone && (
                    <div className="detail-field">
                      <label>Phone</label>
                      <p>{selectedCustomer.phone}</p>
                    </div>
                  )}
                </div>

                <div className="detail-section">
                  <h3>Account Details</h3>
                  <div className="detail-field">
                    <label>Customer ID</label>
                    <p className="mono">{selectedCustomer.id}</p>
                  </div>
                  <div className="detail-field">
                    <label>Created</label>
                    <p>{new Date(selectedCustomer.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                <div className="detail-actions">
                  <button className="btn-primary">Start Conversation</button>
                  <button className="btn-secondary">View Opportunities</button>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-detail">
              <p>Select a customer to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
