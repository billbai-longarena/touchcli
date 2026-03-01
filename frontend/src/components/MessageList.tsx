import { useEffect, useRef } from 'react';
import { useConversationStore } from '../store/conversationStore';
import type { Message } from '../store/conversationStore';
import '../styles/MessageList.css';

export function MessageList() {
  const {
    messages,
    currentConversation,
    fetchMessages,
    agentThinking,
    lastAgentAction,
    wsConnected,
    retryMessage,
  } = useConversationStore();
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
          <div className="connection-status">
            <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`} />
            {wsConnected ? 'Connected' : 'Connecting...'}
          </div>
          <div className="messages">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${isUserMessage(msg) ? 'user' : 'agent'} ${msg.status ? `status-${msg.status}` : ''}`}
              >
                <div className="message-content">
                  <p>{msg.content}</p>
                  <div className="message-footer">
                    <span className="timestamp">
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </span>
                    {msg.status === 'sending' && (
                      <span className="status-badge sending" title="Sending...">
                        ⏳
                      </span>
                    )}
                    {msg.status === 'sent' && (
                      <span className="status-badge sent" title="Sent">
                        ✓
                      </span>
                    )}
                    {msg.status === 'failed' && (
                      <span className="status-badge failed" title={msg.error || 'Failed to send'}>
                        ✗
                      </span>
                    )}
                  </div>
                  {msg.status === 'failed' && (
                    <div className="error-retry">
                      <p className="error-message">{msg.error}</p>
                      <button
                        className="retry-button"
                        onClick={() =>
                          currentConversation &&
                          retryMessage(currentConversation.id, msg.id, msg.content)
                        }
                      >
                        Retry
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {agentThinking && lastAgentAction && (
              <div className="message agent-thinking">
                <div className="message-content">
                  <p className="thinking-indicator">
                    {lastAgentAction.description}
                    <span className="typing-dots">
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </span>
                  </p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </>
      )}
    </div>
  );
}
