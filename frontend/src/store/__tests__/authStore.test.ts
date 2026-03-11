import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  describe('setUser', () => {
    it('should set user in state and update isAuthenticated', () => {
      const mockUser = { id: '1', email: 'test@example.com' };

      useAuthStore.getState().setUser(mockUser);

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe('setToken', () => {
    it('should set token in state', () => {
      const mockToken = 'test-jwt-token';

      useAuthStore.getState().setToken(mockToken);

      const state = useAuthStore.getState();
      expect(state.token).toBe(mockToken);
    });
  });

  describe('clearError', () => {
    it('should clear error message', () => {
      useAuthStore.setState({ error: 'Some error' });
      useAuthStore.getState().clearError();

      const state = useAuthStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe('logout', () => {
    it('should clear user, token, and authentication', () => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com' },
        token: 'test-token',
        isAuthenticated: true,
      });

      useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('isAuthenticated', () => {
    it('should be true when user is set', () => {
      useAuthStore.getState().setUser({ id: '1' });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
    });

    it('should be false when user is null', () => {
      useAuthStore.setState({ user: null });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });

    it('should be false initially', () => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('should set loading state when login starts', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: 'test-token', user_id: 'user-1' }),
      }));

      const loginPromise = useAuthStore.getState().login('user-1');
      await loginPromise;

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe('test-token');
    });

    it('should handle login error', async () => {
      vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(new Error('Network error')));

      const loginPromise = useAuthStore.getState().login('user-1');

      try {
        await loginPromise;
      } catch (_e) {
        // Expected to throw
      }

      const state = useAuthStore.getState();
      expect(state.error).toBeTruthy();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('password + sms auth actions', () => {
    it('should login with password endpoint', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            access_token: 'pwd-token',
            user_id: 'user-1',
            user: { id: 'user-1', name: 'Alice' },
          }),
        })
      );

      await useAuthStore.getState().loginWithPassword('alice', 'touchcli123');
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe('pwd-token');
      expect(state.user?.id).toBe('user-1');
    });

    it('should return countdown and dev code from sendSmsCode', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({ expires_in: 300, dev_code: '123456' }),
        })
      );

      const result = await useAuthStore.getState().sendSmsCode('+1-555-0101');
      expect(result.expiresIn).toBe(300);
      expect(result.devCode).toBe('123456');
    });

    it('should login with sms endpoint', async () => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            access_token: 'sms-token',
            user_id: 'user-2',
            user: { id: 'user-2', name: 'Bob' },
          }),
        })
      );

      await useAuthStore.getState().loginWithSms('+1-555-0102', '654321');
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe('sms-token');
      expect(state.user?.id).toBe('user-2');
    });
  });
});
