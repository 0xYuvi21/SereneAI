import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import api from '../services/api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Backend is at port 8000
      const response = await axios.post('http://localhost:8000/api/users/login', {
        email,
        password
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        // Automatically start a new session on login
        try {
          const sessionRes = await api.post('/sessions/start', { emotion_at_start: 'neutral' });
          if (sessionRes.data && sessionRes.data.session_id) {
            localStorage.setItem('session_id', sessionRes.data.session_id);
          }
        } catch (e) {
          console.error("Failed to start session on login", e);
        }
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid login credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="card" style={{ maxWidth: '400px', width: '100%', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--primary)' }}>
          Welcome Back
        </h2>
        
        {error && (
          <div style={{ padding: '0.75rem', backgroundColor: '#fee2e2', color: 'var(--danger)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label className="input-label">Email Address</label>
            <input 
              type="email" 
              className="input-field"
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div className="input-group">
            <label className="input-label">Password</label>
            <input 
              type="password" 
              className="input-field"
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Don't have an account? <Link to="/register" style={{ fontWeight: 500 }}>Create one</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
