import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

export function useAuth() {
  const store = useAuthStore();
  const navigate = useNavigate();

  // Restore session on mount
  useEffect(() => {
    store.restoreSession();
  }, [store]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!store.isAuthenticated && window.location.pathname !== '/login') {
      navigate('/login');
    }
  }, [store.isAuthenticated, navigate]);

  const loginWithPassword = async (account: string, password: string) => {
    await store.loginWithPassword(account, password);
    navigate('/');
  };

  const sendSmsCode = async (phone: string) => {
    return store.sendSmsCode(phone);
  };

  const loginWithSms = async (phone: string, code: string) => {
    await store.loginWithSms(phone, code);
    navigate('/');
  };

  const logout = () => {
    store.logout();
    navigate('/login');
  };

  return {
    user: store.user,
    token: store.token,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    loginWithPassword,
    sendSmsCode,
    loginWithSms,
    logout,
    clearError: store.clearError,
  };
}
