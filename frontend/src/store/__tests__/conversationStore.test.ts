import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useConversationStore } from '../conversationStore';
import apiClient from '../../api/client';

vi.mock('../../api/client');
vi.mock('../authStore', () => ({
  useAuthStore: {
    getState: () => ({
      user: { id: 'user-1', email: 'test@example.com' },
    }),
  },
}));

describe('conversationStore', () => {
  beforeEach(() => {
    // Reset store state
    useConversationStore.setState({
      currentConversation: null,
      messages: [],
      conversations: [],
      customers: [],
      opportunities: [],
      loading: false,
      error: null,
      wsConnected: false,
      agentThinking: false,
      lastAgentAction: null,
    });
    vi.clearAllMocks();
  });

  describe('setMessages', () => {
    it('should set messages in state', () => {
      const mockMessages = [
        {
          id: '1',
          conversation_id: 'conv-1',
          user_id: 'user-1',
          content: 'Hello',
          created_at: '2026-03-02T00:00:00Z',
          status: 'sent' as const,
        },
      ];

      useConversationStore.getState().setMessages(mockMessages);

      const state = useConversationStore.getState();
      expect(state.messages).toEqual(mockMessages);
      expect(state.messages).toHaveLength(1);
    });
  });

  describe('addMessage', () => {
    it('should add message to existing messages', () => {
      const existingMessage = {
        id: '1',
        conversation_id: 'conv-1',
        user_id: 'user-1',
        content: 'Existing',
        created_at: '2026-03-02T00:00:00Z',
        status: 'sent' as const,
      };

      useConversationStore.setState({ messages: [existingMessage] });

      const newMessage = {
        id: '2',
        conversation_id: 'conv-1',
        user_id: 'user-1',
        content: 'New message',
        created_at: '2026-03-02T00:01:00Z',
        status: 'sent' as const,
      };

      useConversationStore.getState().addMessage(newMessage);

      const state = useConversationStore.getState();
      expect(state.messages).toHaveLength(2);
      expect(state.messages[1]).toEqual(newMessage);
    });
  });

  describe('sendMessage', () => {
    it('should create optimistic message immediately', async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        data: {
          id: 'server-id',
          conversation_id: 'conv-1',
          user_id: 'user-1',
          content: 'Test message',
          created_at: '2026-03-02T00:00:00Z',
          status: 'sent',
        },
      });

      const promise = useConversationStore.getState().sendMessage('conv-1', 'Test message');

      // Check optimistic state immediately
      let state = useConversationStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].status).toBe('sending');
      expect(state.messages[0].content).toBe('Test message');

      // Wait for server response
      await promise;

      // Check final state
      state = useConversationStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].status).toBe('sent');
      expect(state.messages[0].id).toBe('server-id');
    });

    it('should mark message as failed on error', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Network error'));

      const promise = useConversationStore.getState().sendMessage('conv-1', 'Test message');

      try {
        await promise;
      } catch {
        // Expected to throw
      }

      const state = useConversationStore.getState();
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].status).toBe('failed');
      expect(state.messages[0].error).toBeTruthy();
      expect(state.error).toBeTruthy();
    });

    it('should set loading state during send', async () => {
      vi.mocked(apiClient.post).mockImplementationOnce(() => {
        const state = useConversationStore.getState();
        expect(state.loading).toBe(true);

        return Promise.resolve({
          data: {
            id: 'server-id',
            conversation_id: 'conv-1',
            user_id: 'user-1',
            content: 'Test',
            created_at: '2026-03-02T00:00:00Z',
            status: 'sent',
          },
        });
      });

      await useConversationStore.getState().sendMessage('conv-1', 'Test');

      const state = useConversationStore.getState();
      expect(state.loading).toBe(false);
    });
  });

  describe('retryMessage', () => {
    it('should reset failed message to sending state', async () => {
      const failedMessage = {
        id: 'msg-1',
        conversation_id: 'conv-1',
        user_id: 'user-1',
        content: 'Failed message',
        created_at: '2026-03-02T00:00:00Z',
        status: 'failed' as const,
        error: 'Network error',
      };

      useConversationStore.setState({ messages: [failedMessage] });

      vi.mocked(apiClient.post).mockResolvedValueOnce({
        data: {
          id: 'new-server-id',
          conversation_id: 'conv-1',
          user_id: 'user-1',
          content: 'Failed message',
          created_at: '2026-03-02T00:00:00Z',
          status: 'sent',
        },
      });

      const promise = useConversationStore
        .getState()
        .retryMessage('conv-1', 'msg-1', 'Failed message');

      // Check that message is being retried
      let state = useConversationStore.getState();
      expect(state.messages[0].status).toBe('sending');
      expect(state.messages[0].error).toBeUndefined();

      // Wait for server response
      await promise;

      // Check final state
      state = useConversationStore.getState();
      expect(state.messages[0].status).toBe('sent');
      expect(state.messages[0].id).toBe('new-server-id');
    });
  });

  describe('fetchConversations', () => {
    it('should fetch and set conversations', async () => {
      const mockConversations = [
        {
          id: 'conv-1',
          user_id: 'user-1',
          customer_id: 'cust-1',
          title: 'Test Conversation',
          status: 'active',
          created_at: '2026-03-02T00:00:00Z',
          updated_at: '2026-03-02T00:00:00Z',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: mockConversations,
      });

      await useConversationStore.getState().fetchConversations();

      const state = useConversationStore.getState();
      expect(state.conversations).toEqual(mockConversations);
      expect(state.loading).toBe(false);
    });

    it('should handle fetch error', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Fetch failed'));

      await useConversationStore.getState().fetchConversations();

      const state = useConversationStore.getState();
      expect(state.error).toBeTruthy();
      expect(state.conversations).toHaveLength(0);
    });
  });

  describe('setLoading', () => {
    it('should update loading state', () => {
      useConversationStore.getState().setLoading(true);

      let state = useConversationStore.getState();
      expect(state.loading).toBe(true);

      useConversationStore.getState().setLoading(false);

      state = useConversationStore.getState();
      expect(state.loading).toBe(false);
    });
  });

  describe('setError', () => {
    it('should set and clear error', () => {
      useConversationStore.getState().setError('Test error');

      let state = useConversationStore.getState();
      expect(state.error).toBe('Test error');

      useConversationStore.getState().clearError();

      state = useConversationStore.getState();
      expect(state.error).toBeNull();
    });
  });
});
