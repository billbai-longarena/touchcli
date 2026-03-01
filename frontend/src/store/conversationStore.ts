import { create } from 'zustand';
import apiClient from '../api/client';

export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  content: string;
  agent_id?: string;
  created_at: string;
  metadata?: Record<string, unknown>;
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

interface ConversationStore {
  currentConversation: Conversation | null;
  messages: Message[];
  conversations: Conversation[];
  customers: Customer[];
  opportunities: Opportunity[];
  loading: boolean;
  error: string | null;

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

  // Async actions
  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  fetchCustomers: () => Promise<void>;
  fetchOpportunities: () => Promise<void>;
  createConversation: (customerId: string, title: string) => Promise<Conversation>;
  sendMessage: (conversationId: string, content: string) => Promise<Message>;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  currentConversation: null,
  messages: [],
  conversations: [],
  customers: [],
  opportunities: [],
  loading: false,
  error: null,

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  setConversations: (conversations) => set({ conversations }),
  setCustomers: (customers) => set({ customers }),
  setOpportunities: (opportunities) => set({ opportunities }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),

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

  sendMessage: async (conversationId: string, content: string) => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
        content,
      });
      const newMessage = response.data;
      set((state) => ({
        messages: [...state.messages, newMessage],
        loading: false,
      }));
      return newMessage;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      set({ error: errorMessage, loading: false });
      throw error;
    }
  },
}));
