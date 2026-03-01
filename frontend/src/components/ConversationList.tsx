import { useEffect } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/ConversationList.css';

export function ConversationList() {
  const {
    conversations,
    currentConversation,
    setCurrentConversation,
    fetchConversations,
  } = useConversationStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return (
    <div className="conversation-list">
      <h2>Conversations</h2>
      {conversations.length === 0 ? (
        <p className="empty">No conversations yet</p>
      ) : (
        <ul>
          {conversations.map((conv) => (
            <li
              key={conv.id}
              className={currentConversation?.id === conv.id ? 'active' : ''}
              onClick={() => setCurrentConversation(conv)}
            >
              <div className="conversation-item">
                <h3>{conv.title}</h3>
                <p>{new Date(conv.created_at).toLocaleDateString()}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
