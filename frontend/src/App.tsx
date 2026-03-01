import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useAuthStore } from './store/authStore';
import { useAuth } from './hooks/useAuth';
import { ConversationList } from './components/ConversationList';
import { MessageList } from './components/MessageList';
import { MessageInput } from './components/MessageInput';
import { wsClient } from './api/websocket';
import './App.css';

function ConversationApp() {
  const { user, logout } = useAuth();

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>TouchCLI</h1>
          <p className="subtitle">Sales Assistant</p>
        </div>
        <div className="header-right">
          {user && (
            <>
              <span className="user-name">{user.name || user.id}</span>
              <button className="logout-btn" onClick={logout}>
                Logout
              </button>
            </>
          )}
        </div>
      </header>
      <div className="app-container">
        <aside className="sidebar">
          <ConversationList />
        </aside>
        <main className="main-content">
          <MessageList />
          <MessageInput />
        </main>
      </div>
    </div>
  );
}

function AppContent() {
  useEffect(() => {
    // Restore session from localStorage on app mount
    useAuthStore().restoreSession();
  }, []);

  useEffect(() => {
    // Connect WebSocket when authenticated
    const authStore = useAuthStore.getState();
    if (authStore.token && authStore.isAuthenticated) {
      wsClient.setToken(authStore.token);
      wsClient.connect().catch((error) => {
        console.error('Failed to connect WebSocket:', error);
      });
    }

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ConversationApp />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
