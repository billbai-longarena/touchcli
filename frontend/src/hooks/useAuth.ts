import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * useAuth Hook
 * Provides authentication state and actions
 * Automatically redirects to login if not authenticated
 */
export function useAuth() {
  const navigate = useNavigate();
  const {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout: logoutAction,
    clearError,
  } = useAuthStore();

  const logout = () => {
    logoutAction();
    navigate('/login');
  };

  const handleLogin = async (userId: string) => {
    try {
      await login(userId);
      navigate('/dashboard');
    } catch (err) {
      // Error is stored in state, component can display it
      console.error('Login error:', err);
    }
  };

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout,
    clearError,
  };
}
