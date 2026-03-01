import { useEffect } from 'react';
import { ConversationList } from '../components/ConversationList';
import { MessageList } from '../components/MessageList';
import { MessageInput } from '../components/MessageInput';
import { useConversationStore } from '../store/conversationStore';
import { useAuthStore } from '../store/authStore';
import { wsClient } from '../api/websocket';

export function Conversations() {
  const { fetchConversations } = useConversationStore();
  const { user, logout } = useAuthStore();

  // Fetch conversations on mount and setup WebSocket
  useEffect(() => {
    fetchConversations().catch(console.error);
    wsClient.connect().catch(console.error);

    return () => {
      // Cleanup: don't disconnect on unmount, keep connection alive
    };
  }, [fetchConversations]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>TouchCLI</h1>
          <p className="subtitle">Conversational Sales Assistant</p>
        </div>
        <div className="header-right">
          {user && <span className="user-name">{user.name || user.email || user.id}</span>}
          <button className="logout-btn" onClick={logout}>
            Logout
          </button>
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
