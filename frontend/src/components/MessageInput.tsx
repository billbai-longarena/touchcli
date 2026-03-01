import { useState } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/MessageInput.css';

const MAX_MESSAGE_LENGTH = 2000;

export function MessageInput() {
  const [content, setContent] = useState('');
  const [sending, setSending] = useState(false);
  const { currentConversation, sendMessage, error } = useConversationStore();

  const handleSend = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (!content.trim() || !currentConversation || sending) return;

    setSending(true);
    try {
      await sendMessage(currentConversation.id, content.trim());
      setContent('');
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSend(e);
    }
  };

  const charCount = content.length;
  const isNearLimit = charCount > MAX_MESSAGE_LENGTH * 0.8;
  const isOverLimit = charCount > MAX_MESSAGE_LENGTH;

  return (
    <form className="message-input" onSubmit={handleSend}>
      {error && <div className="error-banner">{error}</div>}
      <div className="input-wrapper">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value.slice(0, MAX_MESSAGE_LENGTH))}
          placeholder="Type a message... (Ctrl+Enter to send)"
          disabled={!currentConversation || sending}
          onKeyDown={handleKeyDown}
          rows={3}
        />
        <div className="input-footer">
          <span className={`char-count ${isNearLimit && !isOverLimit ? 'warning' : ''} ${isOverLimit ? 'error' : ''}`}>
            {charCount}/{MAX_MESSAGE_LENGTH}
          </span>
          <button
            type="submit"
            disabled={!currentConversation || !content.trim() || sending || isOverLimit}
            className="send-button"
          >
            {sending ? (
              <>
                <span className="spinner" />
                Sending...
              </>
            ) : (
              <>
                <span className="send-icon">→</span>
                Send
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
