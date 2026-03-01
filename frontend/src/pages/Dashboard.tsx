import { useAuth } from '../hooks/useAuth';
import '../styles/DashboardPage.css';

export function Dashboard() {
  const { user, logout } = useAuth();

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
            Task 3.1 (Project Setup) and Task 3.2 (WebSocket Integration) are complete!
          </p>

          <div className="task-status">
            <h3>Phase 3 Tasks Status</h3>
            <ul className="task-list">
              <li className="task-done">✅ Task 3.1: Project Setup & Auth</li>
              <li className="task-done">✅ Task 3.2: WebSocket Integration</li>
              <li className="task-pending">⏳ Task 3.3: Conversation UI</li>
              <li className="task-pending">⏳ Task 3.4: Real-time Streaming</li>
              <li className="task-pending">⏳ Task 3.5: Dashboard</li>
              <li className="task-pending">⏳ Task 3.6: Auth & Session Mgmt</li>
              <li className="task-pending">⏳ Task 3.7: Testing & Deploy</li>
            </ul>
          </div>

          <div className="quick-info">
            <h3>Backend Status</h3>
            <p>
              Backend is ready at{' '}
              <code>${import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code>
            </p>
            <p>
              WebSocket available at{' '}
              <code>${import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws'}</code>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
