import { useState, useEffect } from 'react';
import { useConversationStore } from '../store/conversationStore';
import { CreateConversationModal } from './CreateConversationModal';
import '../styles/ConversationList.css';

export function ConversationList() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    fetchConversations,
    fetchCustomers,
    subscribeToMessages,
    unsubscribeFromMessages,
  } = useConversationStore();

  useEffect(() => {
    fetchConversations();
    fetchCustomers();
  }, [fetchConversations, fetchCustomers]);

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
    <>
      <CreateConversationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
      <div className="conversation-list">
        <div className="list-header">
          <h2>Conversations</h2>
          <button
            className="new-conversation-btn"
            title="Create new conversation"
            onClick={() => setIsModalOpen(true)}
          >
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
    </>
  );
}
