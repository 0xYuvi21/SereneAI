import { useState, useEffect } from 'react';
import api from '../services/api';

const Journal = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchJournal = async () => {
      try {
        const response = await api.get('/users/influence');
        setEntries(response.data.entries || []);
      } catch (err) {
        console.error('Failed to fetch journal entries:', err);
        setError('Failed to load your journal entries.');
      } finally {
        setLoading(false);
      }
    };
    fetchJournal();
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTopicColor = (topic) => {
    const colors = {
      'Sleep': '#e6f2ff',
      'Work': '#ffe6e6',
      'Food': '#e6ffe6',
      'Exercise': '#fff2e6',
      'Social': '#f2e6ff',
      'Weather': '#e6ffff',
    };
    return colors[topic] || '#fff9e6'; // Default yellow-ish for unknown topics
  };

  if (loading) return <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--primary)' }}>Loading your journal...</div>;
  if (error) return <div style={{ color: 'var(--danger)', textAlign: 'center', marginTop: '4rem' }}>{error}</div>;

  return (
    <div className="container" style={{ padding: '3rem 1rem', maxWidth: '1140px' }}>
      <header style={{ marginBottom: '4rem' }}>
        <h1 className="font-display-lg" style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Your Journal</h1>
        <p className="font-body-lg" style={{ color: 'var(--text-muted)', maxWidth: '42rem', margin: 0 }}>
          Reflect on your past entries. Here are the things that have influenced your mood.
        </p>
      </header>

      {entries.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '4rem' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '48px', opacity: 0.5, marginBottom: '1rem' }}>edit_note</span>
          <p>No journal entries found. Share what's influencing your mood on the dashboard!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '2rem' }}>
          {entries.map(entry => (
            <div 
              key={entry.id} 
              style={{
                backgroundColor: getTopicColor(entry.topic),
                padding: '1.5rem',
                borderRadius: '8px',
                boxShadow: '2px 4px 12px rgba(0,0,0,0.05)',
                position: 'relative',
                minHeight: '200px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              {/* Sticky Note Pin/Tape effect */}
              <div style={{
                position: 'absolute',
                top: '-10px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '60px',
                height: '20px',
                backgroundColor: 'rgba(255,255,255,0.6)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                zIndex: 1
              }}></div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid rgba(0,0,0,0.05)', paddingBottom: '0.5rem' }}>
                <span className="font-label-md" style={{ fontWeight: 'bold', color: 'rgba(0,0,0,0.7)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {entry.topic}
                </span>
                <span className="font-label-sm" style={{ color: 'rgba(0,0,0,0.5)' }}>
                  {formatDate(entry.timestamp)}
                </span>
              </div>
              
              <p className="font-body-md" style={{ color: 'rgba(0,0,0,0.8)', flexGrow: 1, whiteSpace: 'pre-wrap', fontFamily: "'Caveat', 'Segoe Print', cursive, sans-serif", fontSize: '1.1rem', lineHeight: '1.5' }}>
                {entry.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Journal;
