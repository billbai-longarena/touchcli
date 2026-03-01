import { useEffect } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/ConversationList.css';

export function ConversationList() {
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    fetchConversations,
    subscribeToMessages,
    unsubscribeFromMessages,
  } = useConversationStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    // Subscribe to WebSocket messages when conversation is selected
    if (currentConversation) {
      subscribeToMessages();
      return () => {
        unsubscribeFromMessages();
      };
    }
  }, [currentConversation, subscribeToMessages, unsubscribeFromMessages]);

  return (
    <div className="conversation-list">
      <div className="list-header">
        <h2>Conversations</h2>
        <button className="new-conversation-btn" title="Create new conversation">
          +
        </button>
      </div>
      {conversations.length === 0 ? (
        <p className="empty">No conversations yet. Create one to get started.</p>
      ) : (
        <ul>
          {conversations.map((conv) => (
            <li
              key={conv.id}
              className={`conversation-item ${currentConversation?.id === conv.id ? 'active' : ''}`}
              onClick={() => setCurrentConversation(conv)}
            >
              <div className="item-content">
                <h3>{conv.title}</h3>
                <p className="meta">
                  <span className="status">{conv.status}</span>
                  <span className="date">
                    {new Date(conv.created_at).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
