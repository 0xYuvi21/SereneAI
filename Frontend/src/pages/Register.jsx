import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import api from '../services/api';

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    reason_for_using_app: '',
    age: '',
    gender: 'prefer_not_to_say',
    location: '',
    preferred_language: 'en'
  });
  
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/users/register', {
        ...formData,
        age: formData.age ? parseInt(formData.age) : null
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        // Automatically start a new session on register/login
        try {
          const sessionRes = await api.post('/sessions/start', { emotion_at_start: 'neutral' });
          if (sessionRes.data && sessionRes.data.session_id) {
            localStorage.setItem('session_id', sessionRes.data.session_id);
          }
        } catch (e) {
          console.error("Failed to start session on register", e);
        }
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout" style={{ padding: '2rem 1rem' }}>
      <div className="card" style={{ maxWidth: '450px', width: '100%', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--primary)' }}>
          Create Account
        </h2>
        
        {error && (
          <div style={{ padding: '0.75rem', backgroundColor: '#fee2e2', color: 'var(--danger)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleRegister}>
          <div className="input-group">
            <label className="input-label">Full Name</label>
            <input name="name" type="text" required className="input-field" placeholder="What should we call you?" value={formData.name} onChange={handleInputChange} />
          </div>

          <div className="input-group">
            <label className="input-label">Email</label>
            <input name="email" type="email" required className="input-field" value={formData.email} onChange={handleInputChange} />
          </div>
          
          <div className="input-group">
            <label className="input-label">Password</label>
            <input name="password" type="password" required className="input-field" value={formData.password} onChange={handleInputChange} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
             <div className="input-group">
              <label className="input-label">Age</label>
              <input name="age" type="number" className="input-field" value={formData.age} onChange={handleInputChange} />
            </div>
            <div className="input-group">
              <label className="input-label">Gender</label>
              <select name="gender" className="input-field" value={formData.gender} onChange={handleInputChange}>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Location (Optional)</label>
            <input name="location" type="text" className="input-field" value={formData.location} onChange={handleInputChange} />
          </div>

          <div className="input-group">
            <label className="input-label">Why are you using this app?</label>
            <textarea 
              name="reason_for_using_app" 
              className="input-field" 
              style={{ minHeight: '80px', resize: 'vertical' }}
              value={formData.reason_for_using_app} 
              onChange={handleInputChange}
              required
            ></textarea>
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }} disabled={loading}>
            {loading ? 'Creating...' : 'Register'}
          </button>
        </form>
        
        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Already have an account? <Link to="/login" style={{ fontWeight: 500 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
