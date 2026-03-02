import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  name?: string;
  email?: string;
  role?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  setUser: (user: User) => void;
  setToken: (token: string) => void;
  loginWithPassword: (account: string, password: string) => Promise<void>;
  sendSmsCode: (phone: string) => Promise<{ expiresIn: number; devCode?: string }>;
  loginWithSms: (phone: string, code: string) => Promise<void>;
  login: (userId: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  restoreSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => {
        set({ user, isAuthenticated: !!user });
      },

      setToken: (token) => {
        set({ token });
      },

      loginWithPassword: async (account: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/password-login`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ account, password }),
            }
          );

          const data = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(data?.detail || `Login failed: ${response.statusText}`);
          }

          const { access_token, user_id, user } = data;
          set({
            token: access_token,
            user: user || { id: user_id },
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({
            error: message,
            isLoading: false,
            token: null,
            user: null,
            isAuthenticated: false,
          });
          throw err;
        }
      },

      sendSmsCode: async (phone: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/sms/send-code`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ phone }),
            }
          );

          const data = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(data?.detail || `Send code failed: ${response.statusText}`);
          }

          set({ isLoading: false });
          return {
            expiresIn: Number(data?.expires_in ?? 60),
            devCode: typeof data?.dev_code === 'string' ? data.dev_code : undefined,
          };
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to send verification code';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      loginWithSms: async (phone: string, code: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/sms-login`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ phone, code }),
            }
          );

          const data = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(data?.detail || `Login failed: ${response.statusText}`);
          }

          const { access_token, user_id, user } = data;
          set({
            token: access_token,
            user: user || { id: user_id },
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({
            error: message,
            isLoading: false,
            token: null,
            user: null,
            isAuthenticated: false,
          });
          throw err;
        }
      },

      login: async (userId: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/login?user_id=${userId}`,
            { method: 'POST' }
          );

          const data = await response.json().catch(() => ({}));
          if (!response.ok) {
            throw new Error(data?.detail || `Login failed: ${response.statusText}`);
          }

          const { access_token, user_id, user } = data;

          set({
            token: access_token,
            user: user || { id: user_id },
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({
            error: message,
            isLoading: false,
            token: null,
            user: null,
            isAuthenticated: false,
          });
          throw err;
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      clearError: () => {
        set({ error: null });
      },

      restoreSession: () => {
        // Session is auto-restored from localStorage via persist middleware
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
