import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import '../styles/LoginPage.css';

type LoginMode = 'sms' | 'password';

export function Login() {
  const { loginWithPassword, sendSmsCode, loginWithSms, isLoading, error, clearError } = useAuth();
  const [mode, setMode] = useState<LoginMode>('sms');

  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');

  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [devCodeHint, setDevCodeHint] = useState('');
  const [localError, setLocalError] = useState('');

  useEffect(() => {
    if (countdown <= 0) {
      return;
    }

    const timer = window.setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [countdown]);

  const canSubmitPassword = useMemo(() => account.trim().length > 0 && password.length > 0, [account, password]);
  const canSubmitSms = useMemo(() => phone.trim().length > 0 && code.trim().length > 0, [phone, code]);

  const handleSendCode = async () => {
    clearError();
    setLocalError('');
    setDevCodeHint('');

    const phoneValue = phone.trim();
    if (!phoneValue) {
      setLocalError('Please enter your phone number first.');
      return;
    }

    try {
      const result = await sendSmsCode(phoneValue);
      setCountdown(result.expiresIn > 0 ? result.expiresIn : 60);
      setDevCodeHint(result.devCode ? `Dev code: ${result.devCode}` : '');
    } catch {
      // Store-level error handles server message
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError('');

    if (!canSubmitPassword) {
      setLocalError('Please enter account and password.');
      return;
    }

    try {
      await loginWithPassword(account.trim(), password);
    } catch {
      // Store-level error handles server message
    }
  };

  const handleSmsLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError('');

    if (!canSubmitSms) {
      setLocalError('Please enter phone and verification code.');
      return;
    }

    try {
      await loginWithSms(phone.trim(), code.trim());
    } catch {
      // Store-level error handles server message
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>TouchCLI</h1>
          <p>Conversational Sales Assistant</p>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab ${mode === 'sms' ? 'active' : ''}`}
            onClick={() => {
              setMode('sms');
              setLocalError('');
              clearError();
            }}
            disabled={isLoading}
          >
            SMS Login
          </button>
          <button
            type="button"
            className={`login-tab ${mode === 'password' ? 'active' : ''}`}
            onClick={() => {
              setMode('password');
              setLocalError('');
              clearError();
            }}
            disabled={isLoading}
          >
            Password Login
          </button>
        </div>

        {mode === 'sms' ? (
          <form onSubmit={handleSmsLogin} className="login-form">
            <div className="form-group">
              <label htmlFor="phone">Phone</label>
              <input
                id="phone"
                type="text"
                placeholder="e.g., +1-555-0101"
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value);
                  setLocalError('');
                  clearError();
                }}
                disabled={isLoading}
                className="form-input"
              />
              <small className="form-hint">Demo phones: +1-555-0101 / +1-555-0102 / +1-555-0103</small>
            </div>

            <div className="form-group">
              <label htmlFor="code">Verification Code</label>
              <div className="code-row">
                <input
                  id="code"
                  type="text"
                  placeholder="Enter code"
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value);
                    setLocalError('');
                    clearError();
                  }}
                  disabled={isLoading}
                  className="form-input"
                />
                <button
                  type="button"
                  className="code-button"
                  onClick={handleSendCode}
                  disabled={isLoading || countdown > 0}
                >
                  {countdown > 0 ? `Resend (${countdown}s)` : 'Send Code'}
                </button>
              </div>
              {devCodeHint && <small className="form-hint">{devCodeHint}</small>}
            </div>

            {localError && <div className="form-error">{localError}</div>}
            {error && <div className="form-error">{error}</div>}

            <button type="submit" disabled={isLoading || !canSubmitSms} className="form-button">
              {isLoading ? 'Signing in...' : 'Login'}
            </button>
          </form>
        ) : (
          <form onSubmit={handlePasswordLogin} className="login-form">
            <div className="form-group">
              <label htmlFor="account">Username / Email / Phone</label>
              <input
                id="account"
                type="text"
                placeholder="e.g., alice"
                value={account}
                onChange={(e) => {
                  setAccount(e.target.value);
                  setLocalError('');
                  clearError();
                }}
                disabled={isLoading}
                className="form-input"
              />
              <small className="form-hint">Demo account: alice / bob / carol</small>
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setLocalError('');
                  clearError();
                }}
                disabled={isLoading}
                className="form-input"
              />
              <small className="form-hint">Demo password: touchcli123</small>
            </div>

            {localError && <div className="form-error">{localError}</div>}
            {error && <div className="form-error">{error}</div>}

            <button type="submit" disabled={isLoading || !canSubmitPassword} className="form-button">
              {isLoading ? 'Signing in...' : 'Login'}
            </button>
          </form>
        )}

        <div className="login-footer">
          <p>Reference mode from SalesTouch: password login + SMS code login.</p>
        </div>
      </div>
    </div>
  );
}
