import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import '../styles/LoginPage.css';

export function Login() {
  const { login, isLoading, error, clearError } = useAuth();
  const [userId, setUserId] = useState('');
  const [emailInput, setEmailInput] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!userId && !emailInput) {
      alert('Please enter a user ID or email');
      return;
    }

    const id = userId || mapEmailToUserId(emailInput);
    if (!id) {
      alert('User not found. Please use a valid UUID from the database.');
      return;
    }

    try {
      await login(id);
    } catch (err) {
      // Error is handled and displayed
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>TouchCLI</h1>
          <p>Conversational Sales Assistant</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="userId">User ID (UUID)</label>
            <input
              id="userId"
              type="text"
              placeholder="Paste your user UUID here"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value);
                clearError();
              }}
              disabled={isLoading}
              className="form-input"
            />
          </div>

          <div className="form-divider">or</div>

          <div className="form-group">
            <label htmlFor="email">Email (Demo)</label>
            <input
              id="email"
              type="email"
              placeholder="e.g., alice@test.local"
              value={emailInput}
              onChange={(e) => {
                setEmailInput(e.target.value);
                clearError();
              }}
              disabled={isLoading}
              className="form-input"
            />
            <small className="form-hint">
              Demo users: alice@test.local, bob@test.local, carol@test.local
            </small>
          </div>

          {error && <div className="form-error">{error}</div>}

          <button
            type="submit"
            disabled={isLoading || (!userId && !emailInput)}
            className="form-button"
          >
            {isLoading ? 'Signing in...' : 'Continue'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            For development: Get a test user UUID from the database by running:
            <code>python -m agent_service.seeds</code>
          </p>
        </div>
      </div>
    </div>
  );
}

function mapEmailToUserId(email: string): string | null {
  const demoUsers: Record<string, string> = {
    'alice@test.local': '550e8400-e29b-41d4-a716-446655440001',
    'bob@test.local': '550e8400-e29b-41d4-a716-446655440002',
    'carol@test.local': '550e8400-e29b-41d4-a716-446655440003',
  };

  return demoUsers[email.toLowerCase()] || null;
}
