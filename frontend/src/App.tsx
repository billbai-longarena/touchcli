import { useEffect } from 'react';
import { ConversationList } from './components/ConversationList';
import { MessageList } from './components/MessageList';
import { MessageInput } from './components/MessageInput';
import { wsClient } from './api/websocket';
import './App.css';

function App() {
  useEffect(() => {
    // Connect WebSocket on mount
    wsClient.connect().catch((error) => {
      console.error('Failed to connect WebSocket:', error);
    });

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
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
  );
}

export default App;
