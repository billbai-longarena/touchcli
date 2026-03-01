import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import '../styles/DashboardPage.css';

export function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>TouchCLI Dashboard</h1>
          <div className="header-actions">
            <span className="user-info">
              {user?.name || user?.id || 'User'}
            </span>
            <button onClick={logout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="welcome-card">
          <h2>Welcome to Phase 3! 🎉</h2>
          <p>
            Task 3.4 (Real-time Streaming) is now complete! 57% of Phase 3 done.
          </p>

          <div className="quick-actions">
            <button className="action-button" onClick={() => navigate('/conversations')}>
              💬 Go to Conversations
            </button>
            <button className="action-button" onClick={() => navigate('/customers')}>
              👥 View Customers
            </button>
            <button className="action-button" onClick={() => navigate('/opportunities')}>
              🎯 View Opportunities
            </button>
          </div>

          <div className="task-status">
            <h3>Phase 3 Tasks Status</h3>
            <ul className="task-list">
              <li className="task-done">✅ Task 3.1: Project Setup & Auth</li>
              <li className="task-done">✅ Task 3.2: WebSocket Integration</li>
              <li className="task-done">✅ Task 3.3: Conversation UI</li>
              <li className="task-done">✅ Task 3.4: Real-time Streaming</li>
              <li className="task-in-progress">🚀 Task 3.5: Customer/Opportunity Dashboard</li>
              <li className="task-pending">⏳ Task 3.6: Testing & CI/CD</li>
              <li className="task-pending">⏳ Task 3.7: Deployment</li>
            </ul>
          </div>

          <div className="success-message">
            <h4>✓ Task 3.4 Completed Successfully!</h4>
            <ul className="criteria-list">
              <li>✅ Optimistic message updates</li>
              <li>✅ Message status tracking (⏳✓✗)</li>
              <li>✅ Error recovery with retry</li>
              <li>✅ Create conversation modal</li>
              <li>✅ Form validation & loading states</li>
            </ul>
          </div>

          <div className="quick-info">
            <h3>Backend Status</h3>
            <p>
              Backend is ready at{' '}
              <code>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
            </p>
            <p>
              WebSocket available at{' '}
              <code>{import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws'}</code>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
