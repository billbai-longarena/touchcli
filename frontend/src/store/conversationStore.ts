import { create } from 'zustand';
import apiClient from '../api/client';
import { wsClient, type WebSocketFrame } from '../api/websocket';

export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  content: string;
  agent_id?: string;
  created_at: string;
  metadata?: Record<string, unknown>;
  status?: 'sending' | 'sent' | 'failed'; // Optimistic update tracking
  error?: string; // Error message if failed
}

export interface Conversation {
  id: string;
  user_id: string;
  customer_id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Opportunity {
  id: string;
  customer_id: string;
  title: string;
  amount: number;
  stage: string;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  user_id: string;
  name: string;
  email: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

interface AgentAction {
  type: string;
  description: string;
  timestamp: string;
}

interface ConversationStore {
  currentConversation: Conversation | null;
  messages: Message[];
  conversations: Conversation[];
  customers: Customer[];
  opportunities: Opportunity[];
  loading: boolean;
  error: string | null;
  wsConnected: boolean;
  agentThinking: boolean;
  lastAgentAction: AgentAction | null;

  // Actions
  setCurrentConversation: (conversation: Conversation) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setConversations: (conversations: Conversation[]) => void;
  setCustomers: (customers: Customer[]) => void;
  setOpportunities: (opportunities: Opportunity[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  setWsConnected: (connected: boolean) => void;

  // Async actions
  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  fetchCustomers: () => Promise<void>;
  fetchOpportunities: () => Promise<void>;
  createConversation: (customerId: string, title: string) => Promise<Conversation>;
  createOpportunity: (data: { customer_id: string; title: string; amount: number; stage: string }) => Promise<Opportunity>;
  sendMessage: (conversationId: string, content: string) => Promise<Message>;
  retryMessage: (conversationId: string, messageId: string, content: string) => Promise<Message>;
  subscribeToMessages: () => void;
  unsubscribeFromMessages: () => void;
}

let messageUnsubscribe: (() => void) | null = null;
let actionUnsubscribe: (() => void) | null = null;

export const useConversationStore = create<ConversationStore>((set) => ({
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

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  setConversations: (conversations) => set({ conversations }),
  setCustomers: (customers) => set({ customers }),
  setOpportunities: (opportunities) => set({ opportunities }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  setWsConnected: (connected) => set({ wsConnected: connected }),

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/conversations');
      set({ conversations: response.data, loading: false });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch conversations';
      set({ error: errorMessage, loading: false });
    }
  },

  fetchMessages: async (conversationId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get(`/conversations/${conversationId}/messages`);
      set({ messages: response.data, loading: false });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch messages';
      set({ error: errorMessage, loading: false });
    }
  },

  fetchCustomers: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/customers');
      set({ customers: response.data, loading: false });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch customers';
      set({ error: errorMessage, loading: false });
    }
  },

  fetchOpportunities: async () => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get('/opportunities');
      set({ opportunities: response.data, loading: false });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch opportunities';
      set({ error: errorMessage, loading: false });
    }
  },

  createConversation: async (customerId: string, title: string) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post('/conversations', {
        customer_id: customerId,
        title,
      });
      const newConversation = response.data;
      set((state) => ({
        conversations: [...state.conversations, newConversation],
        currentConversation: newConversation,
        loading: false,
      }));
      return newConversation;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create conversation';
      set({ error: errorMessage, loading: false });
      throw error;
    }
  },

  createOpportunity: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post('/opportunities', data);
      const newOpportunity = response.data;
      set((state) => ({
        opportunities: [...state.opportunities, newOpportunity],
        loading: false,
      }));
      return newOpportunity;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create opportunity';
      set({ error: errorMessage, loading: false });
      throw error;
    }
  },

  sendMessage: async (conversationId: string, content: string) => {
    // Generate temporary ID for optimistic update
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).slice(2)}`;

    // Create optimistic message
    const optimisticMessage: Message = {
      id: tempId,
      conversation_id: conversationId,
      user_id: useAuthStore.getState().user?.id || '',
      content,
      created_at: new Date().toISOString(),
      status: 'sending',
    };

    // Add optimistic message to UI immediately
    set((state) => ({
      messages: [...state.messages, optimisticMessage],
      loading: true,
      error: null,
    }));

    try {
      const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
        content,
      });
      const newMessage = response.data;

      // Replace optimistic message with confirmed message
      set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id === tempId ? { ...newMessage, status: 'sent' } : msg
        ),
        loading: false,
      }));

      return newMessage;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';

      // Mark optimistic message as failed
      set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id === tempId
            ? {
                ...msg,
                status: 'failed',
                error: errorMessage,
              }
            : msg
        ),
        error: errorMessage,
        loading: false,
      }));

      throw error;
    }
  },

  retryMessage: async (conversationId: string, messageId: string, content: string) => {
    // Reset failed message to sending state
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? { ...msg, status: 'sending', error: undefined }
          : msg
      ),
      loading: true,
      error: null,
    }));

    try {
      const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
        content,
      });
      const newMessage = response.data;

      // Replace failed message with confirmed message
      set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id === messageId ? { ...newMessage, status: 'sent' } : msg
        ),
        loading: false,
      }));

      return newMessage;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';

      // Mark as failed again
      set((state) => ({
        messages: state.messages.map((msg) =>
          msg.id === messageId
            ? {
                ...msg,
                status: 'failed',
                error: errorMessage,
              }
            : msg
        ),
        error: errorMessage,
        loading: false,
      }));

      throw error;
    }
  },

  subscribeToMessages: () => {
    // Subscribe to incoming messages from agents
    messageUnsubscribe = wsClient.on('message', (frame: WebSocketFrame) => {
      const messageData = frame.data as unknown as Message;
      if (messageData && typeof messageData === 'object' && 'id' in messageData) {
        set((state) => {
          // Only add if not already in messages
          if (!state.messages.find((m) => m.id === messageData.id)) {
            return { messages: [...state.messages, messageData] };
          }
          return state;
        });
      }
    });

    // Subscribe to agent actions (thinking/planning)
    actionUnsubscribe = wsClient.on('agent-action', (frame: WebSocketFrame) => {
      const actionData = frame.data as unknown as { type?: string; description?: string };
      set({
        agentThinking: true,
        lastAgentAction: {
          type: actionData?.type || 'processing',
          description: actionData?.description || 'Agent is processing...',
          timestamp: frame.timestamp,
        },
      });
    });

    // Mark as connected
    set({ wsConnected: true });
  },

  unsubscribeFromMessages: () => {
    if (messageUnsubscribe) {
      messageUnsubscribe();
      messageUnsubscribe = null;
    }
    if (actionUnsubscribe) {
      actionUnsubscribe();
      actionUnsubscribe = null;
    }
    set({ wsConnected: false, agentThinking: false });
  },
}));
