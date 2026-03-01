import { useState } from 'react';
import { useConversationStore } from '../store/conversationStore';
import '../styles/MessageInput.css';

export function MessageInput() {
  const [content, setContent] = useState('');
  const [sending, setSending] = useState(false);
  const { currentConversation, sendMessage, error } = useConversationStore();

  const handleSend = async (e: React.FormEvent) => {
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

  return (
    <form className="message-input" onSubmit={handleSend}>
      {error && <div className="error-banner">{error}</div>}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Type a message..."
        disabled={!currentConversation || sending}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.ctrlKey) {
            handleSend(e);
          }
        }}
      />
      <button
        type="submit"
        disabled={!currentConversation || !content.trim() || sending}
      >
        {sending ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
}
