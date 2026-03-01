import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useAuthStore } from './store/authStore';
import { ConversationList } from './components/ConversationList';
import { MessageList } from './components/MessageList';
import { MessageInput } from './components/MessageInput';
import { wsClient } from './api/websocket';
import './App.css';

function AppContent() {
  useEffect(() => {
    // Restore session from localStorage on app mount
    useAuthStore().restoreSession();
  }, []);

  useEffect(() => {
    // Connect WebSocket on mount (for future conversation UI)
    wsClient.connect().catch((error) => {
      console.error('Failed to connect WebSocket:', error);
    });

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
            <div className="app">
              <header className="app-header">
                <h1>TouchCLI - Sales Assistant</h1>
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
