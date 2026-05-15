import { useState, useEffect } from 'react';
import { User, Mail, MapPin, Globe } from 'lucide-react';
import api from '../services/api';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const { data } = await api.get('/users/me');
        setProfile(data);
      } catch (err) {
        setError('Failed to load profile data.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '2rem' }}>Loading profile...</div>;
  }

  if (error) {
    return <div style={{ color: 'var(--danger)', textAlign: 'center', marginTop: '2rem' }}>{error}</div>;
  }

  return (
    <div className="container" style={{ maxWidth: '800px' }}>
      <h2 style={{ color: 'var(--primary)', marginBottom: '1.5rem' }}>Your Profile</h2>
      
      <div className="card" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '250px' }}>
          <div style={{ padding: '2rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius)', textAlign: 'center', border: '1px solid var(--border)' }}>
            <div style={{ width: '100px', height: '100px', borderRadius: '50%', backgroundColor: 'var(--primary)', color: 'white', margin: '0 auto 1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={48} />
            </div>
            <h3 style={{ marginBottom: '0.25rem' }}>{profile.email.split('@')[0]}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{profile.role || 'User'}</p>
          </div>
        </div>
        
        <div style={{ flex: '2', minWidth: '300px' }}>
          <h4 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
            Account Details
          </h4>
          
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Mail size={18} color="var(--primary)" />
              <div>
                <span className="input-label" style={{ marginBottom: '0' }}>Email</span>
                <span>{profile.email}</span>
              </div>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <User size={18} color="var(--primary)" />
              <div>
                <span className="input-label" style={{ marginBottom: '0' }}>Age & Gender</span>
                <span style={{ textTransform: 'capitalize' }}>
                  {profile.age || 'N/A'} yrs • {profile.gender?.replace('_', ' ') || 'N/A'}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <MapPin size={18} color="var(--primary)" />
              <div>
                <span className="input-label" style={{ marginBottom: '0' }}>Location</span>
                <span>{profile.location || 'Not provided'}</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Globe size={18} color="var(--primary)" />
              <div>
                <span className="input-label" style={{ marginBottom: '0' }}>Language</span>
                <span>{profile.preferred_language?.toUpperCase() || 'EN'}</span>
              </div>
            </div>
            
            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'rgba(107, 70, 193, 0.05)', borderRadius: '8px' }}>
              <span className="input-label">Reason for using the app</span>
              <p style={{ margin: 0, fontStyle: 'italic', color: 'var(--text-main)' }}>
                "{profile.reason_for_using_app || 'No reason provided.'}"
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
