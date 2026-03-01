import { useEffect, useRef } from 'react';
import { useConversationStore } from '../store/conversationStore';
import type { Message } from '../store/conversationStore';
import '../styles/MessageList.css';

export function MessageList() {
  const { messages, currentConversation, fetchMessages } = useConversationStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (currentConversation) {
      fetchMessages(currentConversation.id);
    }
  }, [currentConversation, fetchMessages]);

  const isUserMessage = (msg: Message) => !msg.agent_id;

  return (
    <div className="message-list">
      {!currentConversation ? (
        <div className="empty-state">
          <p>Select a conversation to view messages</p>
        </div>
      ) : (
        <>
          <div className="messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${isUserMessage(msg) ? 'user' : 'agent'}`}
              >
                <div className="message-content">
                  <p>{msg.content}</p>
                  <span className="timestamp">
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </>
      )}
    </div>
  );
}
