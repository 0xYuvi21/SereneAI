import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell } from 'recharts';
import { Activity, Heart, AlertTriangle, Clock } from 'lucide-react';
import api from '../services/api';

const NoDataPlaceholder = ({ message = 'No session data recorded yet.' }) => (
  <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', flexDirection: 'column', gap: '0.5rem' }}>
    <svg width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>
    <p style={{ margin: 0, fontSize: '0.875rem' }}>{message}</p>
  </div>
);

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [dashboardData, setDashboardData] = useState(null);
  const [emotionTrends, setEmotionTrends] = useState([]);
  const [anxietyTrends, setAnxietyTrends] = useState([]);
  const [recoveryData, setRecoveryData] = useState(null);
  const [dropoutRisk, setDropoutRisk] = useState(null);

  const location = useLocation();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        setError(null);
        // 1. Get current user to get their ID
        const userRes = await api.get('/users/me');
        const userId = userRes.data.user_id || userRes.data.id;

        // 2. Fetch all analytics in parallel
        const [dashRes, emotionRes, recoveryRes, riskRes, anxietyRes] = await Promise.all([
          api.get('/users/dashboard').catch(() => ({ data: {} })),
          api.get(`/analytics/emotion-trends/${userId}`).catch(() => ({ data: { trends: [] } })),
          api.get(`/analytics/recovery-rate/${userId}`).catch(() => ({ data: { rate: 0, status: 'Unknown' } })),
          api.get(`/analytics/dropout-risk/${userId}`).catch(() => ({ data: { risk_score: 'Low' } })),
          api.get(`/analytics/anxiety-trends/${userId}`).catch(() => ({ data: { anxiety_trends: [] } }))
        ]);

        setDashboardData(dashRes.data);
        setEmotionTrends(emotionRes.data.trends || []);
        setAnxietyTrends(anxietyRes.data.anxiety_trends || []);
        setRecoveryData(recoveryRes.data);
        setDropoutRisk(riskRes.data);
      } catch (err) {
        console.error(err);
        setError('Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  // Re-fetch every time the user navigates to this page
  }, [location.key]);

  if (loading) return <div style={{ textAlign: 'center', marginTop: '2rem' }}>Loading dashboard analytics...</div>;
  if (error) return <div style={{ color: 'var(--danger)', textAlign: 'center', marginTop: '2rem' }}>{error}</div>;

  const emotionToScore = {
    happy: 90, calm: 80, hopeful: 75, grateful: 85,
    neutral: 50,
    anxious: 30, stressed: 25, sad: 20, angry: 15, depressed: 10
  };

  const parsedTrends = emotionTrends.map((t, index) => ({
    day: t.session_date ? new Date(t.session_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : `S${index + 1}`,
    score: emotionToScore[t.emotion_at_start?.toLowerCase()] || 50
  }));

  const parsedAnxiety = anxietyTrends.map((t, index) => ({
    day: t.date ? new Date(t.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : `S${index + 1}`,
    ras: t.ras_score,
    tas: t.tas_score
  }));

  const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];
  const emotionDist = Object.entries(dashboardData?.emotion_distribution || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }));

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ color: 'var(--primary)', marginBottom: '0.25rem' }}>Welcome to Dashboard</h2>
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>Here is your analytics summary for this week.</p>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', backgroundColor: 'rgba(107, 70, 193, 0.1)', borderRadius: '12px', color: 'var(--primary)' }}><Activity size={24} /></div>
          <div>
            <p className="input-label" style={{ marginBottom: '0.25rem' }}>Total Sessions</p>
            <h3 style={{ margin: 0 }}>{dashboardData?.total_sessions || 0}</h3>
          </div>
        </div>
        
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', backgroundColor: 'rgba(56, 161, 105, 0.1)', borderRadius: '12px', color: 'var(--success)' }}><Heart size={24} /></div>
          <div>
            <p className="input-label" style={{ marginBottom: '0.25rem' }}>Recovery Rate</p>
            <h3 style={{ margin: 0 }}>{recoveryData?.rate || '0'}%</h3>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', backgroundColor: 'rgba(229, 62, 62, 0.1)', borderRadius: '12px', color: 'var(--danger)' }}><AlertTriangle size={24} /></div>
          <div>
            <p className="input-label" style={{ marginBottom: '0.25rem' }}>Dropout Risk</p>
            <h3 style={{ margin: 0 }}>{dropoutRisk?.risk_score || 'Low'}</h3>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', backgroundColor: 'rgba(236, 72, 153, 0.1)', borderRadius: '12px', color: '#ec4899' }}><Clock size={24} /></div>
          <div>
            <p className="input-label" style={{ marginBottom: '0.25rem' }}>Longest Session</p>
            <h3 style={{ margin: 0 }}>
              {dashboardData?.best_session_duration ? `${Math.round(dashboardData.best_session_duration / 60)} mins` : 'N/A'}
            </h3>
            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {dashboardData?.best_session_date ? new Date(dashboardData.best_session_date).toLocaleDateString() : ''}
            </p>
          </div>
        </div>
      </div>
      
      {/* Main Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div className="card" style={{ padding: '2rem' }}>
          <h4 style={{ marginBottom: '2rem', color: 'var(--text-main)' }}>Emotion Trend Analysis</h4>
          <div style={{ height: '300px', width: '100%' }}>
            {parsedTrends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={parsedTrends}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)'}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)'}} dx={-10} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                    itemStyle={{ color: 'var(--primary)', fontWeight: 600 }}
                  />
                  <Area type="monotone" dataKey="score" stroke="var(--primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <NoDataPlaceholder message="Complete a session to see your emotion trend." />
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '2rem' }}>
          <h4 style={{ marginBottom: '2rem', color: 'var(--text-main)' }}>Global Emotion Architecture</h4>
          <div style={{ height: '300px', width: '100%' }}>
            {emotionDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={emotionDist}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {emotionDist.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <NoDataPlaceholder message="No session recorded yet." />
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '2rem', gridColumn: '1 / -1' }}>
          <h4 style={{ marginBottom: '2rem', color: 'var(--text-main)' }}>Anxiety Trend Analysis (RAS & TAS)</h4>
          <div style={{ height: '300px', width: '100%' }}>
            {parsedAnxiety.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={parsedAnxiety}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)'}} dy={10} />
                  <YAxis domain={[1, 4]} axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)'}} dx={-10} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                    itemStyle={{ fontWeight: 600 }}
                  />
                  <Line type="monotone" dataKey="ras" name="Reactive Anxiety (RAS)" stroke="#ef4444" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 6}} />
                  <Line type="monotone" dataKey="tas" name="Trait Anxiety (TAS)" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 6}} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <NoDataPlaceholder message="RAS & TAS scores are calculated after you complete a session." />
            )}
          </div>
        </div>

        <div className="card" style={{ padding: '2rem', gridColumn: '1 / -1' }}>
          <h4 style={{ marginBottom: '1rem', color: 'var(--text-main)' }}>Insights & Suggestions</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {dashboardData?.latest_insights ? (
              <div style={{ padding: '1.5rem', backgroundColor: 'var(--primary-light)', borderRadius: '12px', lineHeight: '1.6', color: 'var(--text-main)', border: '1px solid rgba(107, 70, 193, 0.1)' }}>
                {dashboardData.latest_insights.split('\n').map((paragraph, idx) => {
                  // Basic formatting for bold text (e.g. **text**)
                  if (!paragraph.trim()) return null;
                  const formattedText = paragraph.split(/(\*\*.*?\*\*)/g).map((part, i) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                      return <strong key={i} style={{ color: 'var(--primary)' }}>{part.slice(2, -2)}</strong>;
                    }
                    return part;
                  });
                  return <p key={idx} style={{ marginBottom: '0.75rem' }}>{formattedText}</p>;
                })}
              </div>
            ) : (
              <div style={{ padding: '1rem', borderLeft: '4px solid var(--text-muted)', backgroundColor: 'var(--surface)', borderRadius: '0 8px 8px 0' }}>
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>Complete a chat session to generate your personalized wellness insights.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
