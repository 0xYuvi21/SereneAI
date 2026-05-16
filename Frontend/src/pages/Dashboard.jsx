import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import api from '../services/api';

const NoDataPlaceholder = ({ message = 'No session data recorded yet.' }) => (
  <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', flexDirection: 'column', gap: '0.5rem' }}>
    <span className="material-symbols-outlined" style={{ fontSize: '32px', opacity: 0.5 }}>query_stats</span>
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

  const [selectedTag, setSelectedTag] = useState('');
  const [influenceNotes, setInfluenceNotes] = useState('');
  const [influenceStatus, setInfluenceStatus] = useState('');

  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        setError(null);
        const userRes = await api.get('/users/me');
        const userId = userRes.data.user_id || userRes.data.id;

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
  }, [location.key]);

  if (loading) return <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--primary)' }}>Loading your sanctuary...</div>;
  if (error) return <div style={{ color: 'var(--danger)', textAlign: 'center', marginTop: '4rem' }}>{error}</div>;

  const handleSaveInfluence = async () => {
    if (!selectedTag || !influenceNotes) {
      setInfluenceStatus('Please select a tag and add notes.');
      setTimeout(() => setInfluenceStatus(''), 3000);
      return;
    }
    try {
      setInfluenceStatus('Saving...');
      await api.post('/users/influence', { topic: selectedTag, content: influenceNotes });
      setInfluenceStatus('Saved successfully!');
      setSelectedTag('');
      setInfluenceNotes('');
      setTimeout(() => setInfluenceStatus(''), 3000);
    } catch (err) {
      setInfluenceStatus('Failed to save.');
      setTimeout(() => setInfluenceStatus(''), 3000);
    }
  };

  const emotionToScore = {
    happy: 90, calm: 80, hopeful: 75, grateful: 85,
    neutral: 50,
    anxious: 30, stressed: 25, sad: 20, angry: 15, depressed: 10
  };

  const parsedTrends = emotionTrends.map((t, index) => ({
    day: t.session_date ? new Date(t.session_date).toLocaleDateString(undefined, { weekday: 'short' }) : `S${index + 1}`,
    score: emotionToScore[t.emotion_at_start?.toLowerCase()] || 50
  }));

  const parsedAnxiety = anxietyTrends.map((t, index) => ({
    day: t.date ? new Date(t.date).toLocaleDateString(undefined, { weekday: 'short' }) : `S${index + 1}`,
    ras: t.ras_score,
    tas: t.tas_score
  }));

  const COLORS = ['#84a59d', '#45645e', '#aaccda', '#c7eae1', '#e4e2de', '#9e9bb5'];
  const emotionDist = Object.entries(dashboardData?.emotion_distribution || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }));

  let insights = dashboardData?.latest_insights || {};
  if (typeof insights === 'string') {
    insights = { detailed_report: insights };
  }
  const hasInsights = Object.keys(insights).length > 0;

  return (
    <div className="container" style={{ padding: '3rem 1rem', maxWidth: '1140px' }}>
      <header style={{ marginBottom: '4rem' }}>
        <h1 className="font-display-lg" style={{ color: 'var(--primary)', marginBottom: '1rem' }}>How are you feeling today?</h1>
        <p className="font-body-lg" style={{ color: 'var(--text-muted)', maxWidth: '42rem', margin: 0 }}>
          Take a moment to check in with yourself. Tracking your emotions helps you understand patterns and find your balance.
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', alignItems: 'start' }}>
        
        {/* Left Column: Charts and Stats */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem', gridColumn: 'span 7' }}>
          
          {/* Current Mood Header Card */}
          <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--primary-fixed)' }}>
            <div>
              <div className="font-label-md" style={{ color: 'var(--on-primary-container)', marginBottom: '4px' }}>CURRENT MOOD</div>
              <div className="font-headline-lg" style={{ color: 'var(--on-primary-container)' }}>Calm</div>
            </div>
            <button 
              className="font-label-md"
              style={{ padding: '0.75rem 1.5rem', backgroundColor: 'var(--primary)', color: 'var(--on-primary)', borderRadius: '9999px', border: 'none', cursor: 'pointer', boxShadow: 'var(--shadow-sm)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>sync</span> Update
            </button>
          </div>

          {/* Influences Tags */}
          <div className="glass-card">
            <h2 className="font-headline-md" style={{ color: 'var(--primary)', margin: '0 0 1.5rem 0' }}>What's influencing your mood?</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.5rem' }}>
              {['Sleep', 'Work', 'Food', 'Exercise', 'Social', 'Weather'].map(tag => (
                <button 
                  key={tag} 
                  onClick={() => setSelectedTag(tag)}
                  style={{ 
                    padding: '0.5rem 1rem', 
                    borderRadius: '9999px', 
                    border: '1px solid var(--border)', 
                    backgroundColor: selectedTag === tag ? 'var(--primary-container)' : 'transparent', 
                    color: selectedTag === tag ? 'var(--on-primary-container)' : 'var(--text-main)', 
                    cursor: 'pointer',
                    fontWeight: selectedTag === tag ? '600' : 'normal'
                  }} 
                  className="font-label-md hover:bg-surface-container-high transition-colors"
                >
                  {tag}
                </button>
              ))}
              <button style={{ padding: '0.5rem 1rem', borderRadius: '9999px', border: '1px dashed var(--primary)', backgroundColor: 'transparent', color: 'var(--primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }} className="font-label-md hover:bg-primary-container transition-colors">
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add</span> Add New
              </button>
            </div>
            <textarea 
              value={influenceNotes}
              onChange={(e) => setInfluenceNotes(e.target.value)}
              placeholder="Add any specific notes about how you're feeling..."
              style={{ width: '100%', padding: '1rem', borderRadius: '16px', border: '1px solid var(--border)', backgroundColor: 'rgba(255,255,255,0.5)', resize: 'none', minHeight: '100px' }}
              className="font-body-md"
            ></textarea>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
               <span style={{ color: influenceStatus.includes('Failed') ? 'var(--danger)' : 'var(--primary)', fontSize: '0.875rem' }}>{influenceStatus}</span>
               <button 
                onClick={handleSaveInfluence}
                className="font-label-md"
                style={{ padding: '0.5rem 1.5rem', backgroundColor: 'var(--primary)', color: 'var(--on-primary)', borderRadius: '9999px', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>save</span> Save Entry
              </button>
            </div>
          </div>

          {/* Main Trend Chart */}
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h2 className="font-headline-md" style={{ color: 'var(--primary)', margin: 0 }}>Weekly Trend</h2>
              <span className="material-symbols-outlined" style={{ color: 'var(--text-muted)' }}>more_horiz</span>
            </div>
            
            <div style={{ height: '240px', width: '100%', marginBottom: '1.5rem' }}>
              {parsedTrends.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={parsedTrends}>
                    <defs>
                      <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--primary-container)" stopOpacity={1}/>
                        <stop offset="100%" stopColor="var(--primary-container)" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 12, fontFamily: 'Inter'}} dy={10} />
                    <YAxis hide domain={[0, 100]} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: 'var(--shadow-md)', backgroundColor: 'rgba(255, 255, 255, 0.9)' }}
                      itemStyle={{ color: 'var(--primary)', fontWeight: 600 }}
                    />
                    <Area type="monotone" dataKey="score" stroke="var(--primary)" strokeWidth={4} fillOpacity={0.2} fill="url(#colorScore)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <NoDataPlaceholder message="Complete a session to see your emotion trend." />
              )}
            </div>

            {hasInsights && insights.weekly_trend_insight && (
              <div style={{ padding: '1rem', backgroundColor: 'rgba(199, 234, 225, 0.3)', borderRadius: '16px', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                <span className="material-symbols-outlined" style={{ color: 'var(--primary)', marginTop: '2px' }}>lightbulb</span>
                <p className="font-label-md" style={{ color: 'var(--primary-hover)', margin: 0, lineHeight: 1.5 }}>
                  {insights.weekly_trend_insight}
                </p>
              </div>
            )}
          </div>

          {/* Anxiety Trends */}
          <div className="glass-card">
            <h2 className="font-headline-md" style={{ color: 'var(--primary)', marginBottom: '2rem', margin: 0 }}>Anxiety Levels</h2>
            <div style={{ height: '240px', width: '100%' }}>
              {parsedAnxiety.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={parsedAnxiety}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 12}} dy={10} />
                    <YAxis domain={[1, 4]} axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 12}} dx={-10} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                    />
                    <Line type="monotone" dataKey="ras" name="Reactive (RAS)" stroke="var(--danger)" strokeWidth={3} dot={false} activeDot={{r: 6}} />
                    <Line type="monotone" dataKey="tas" name="Trait (TAS)" stroke="var(--secondary)" strokeWidth={3} dot={false} activeDot={{r: 6}} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <NoDataPlaceholder message="Anxiety scores populate after completing an assessment session." />
              )}
            </div>
          </div>

          {/* Legacy Stats Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <div className="font-label-md" style={{ color: 'var(--text-muted)' }}>Recovery Rate</div>
              <div className="font-headline-lg" style={{ color: 'var(--primary)' }}>{recoveryData?.rate || '0'}%</div>
            </div>
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <div className="font-label-md" style={{ color: 'var(--text-muted)' }}>Dropout Risk</div>
              <div className="font-headline-lg" style={{ color: dropoutRisk?.risk_score === 'High' ? 'var(--danger)' : 'var(--primary)' }}>
                {dropoutRisk?.risk_score || 'Low'}
              </div>
            </div>
          </div>
        </section>

        {/* Right Column: AI Insights */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem', gridColumn: 'span 5' }}>
          
          {/* Mini Insights Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {hasInsights && insights.mini_insights ? (
              insights.mini_insights.map((mi, i) => (
                <div key={i} className="glass-card" style={{ padding: '1.5rem' }}>
                  <div style={{ fontSize: '28px', marginBottom: '0.5rem' }}>{mi.icon}</div>
                  <div className="font-label-md" style={{ color: 'var(--text-muted)' }}>{mi.label}</div>
                  <div className="font-headline-md" style={{ color: 'var(--primary)' }}>{mi.value}</div>
                </div>
              ))
            ) : (
              <>
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                  <div style={{ fontSize: '28px', marginBottom: '0.5rem' }}>🧘</div>
                  <div className="font-label-md" style={{ color: 'var(--text-muted)' }}>Sessions</div>
                  <div className="font-headline-md" style={{ color: 'var(--primary)' }}>{dashboardData?.total_sessions || 0}</div>
                </div>
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                  <div style={{ fontSize: '28px', marginBottom: '0.5rem' }}>🔥</div>
                  <div className="font-label-md" style={{ color: 'var(--text-muted)' }}>Streak</div>
                  <div className="font-headline-md" style={{ color: 'var(--primary)' }}>{dashboardData?.login_streak || 0}</div>
                </div>
              </>
            )}
          </div>

          {/* Featured Reflection Card */}
          <div style={{ position: 'relative', borderRadius: '24px', overflow: 'hidden', height: '260px', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ position: 'absolute', inset: 0, backgroundColor: 'var(--primary-container)', backgroundImage: 'linear-gradient(to top, rgba(69, 100, 94, 0.9), rgba(69, 100, 94, 0.2))' }}></div>
            <div style={{ position: 'absolute', bottom: 0, padding: '2rem', width: '100%' }}>
              <h3 className="font-headline-md" style={{ color: 'var(--on-primary)', marginBottom: '0.5rem', margin: 0 }}>Evening Reflection</h3>
              <p className="font-body-md" style={{ color: 'rgba(255,255,255,0.9)', margin: '0 0 1rem 0' }}>
                {hasInsights && insights.reflection_question ? insights.reflection_question : "What made you smile today?"}
              </p>
              <button 
                onClick={() => navigate('/chat')}
                style={{ background: 'none', border: 'none', color: 'var(--on-primary)', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} 
                className="font-label-md hover:translate-x-1 transition-transform"
              >
                Reflect now <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
              </button>
            </div>
          </div>

          {/* Detailed Report */}
          <div className="glass-card">
            <h2 className="font-headline-md" style={{ color: 'var(--primary)', marginBottom: '1.5rem', margin: 0 }}>Your Wellness Guide</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {hasInsights && insights.detailed_report ? (
                <div className="font-body-md" style={{ color: 'var(--text-main)', lineHeight: '1.7' }}>
                  {insights.detailed_report.split('\n').map((paragraph, idx) => {
                    if (!paragraph.trim()) return null;
                    const formattedText = paragraph.split(/(\*\*.*?\*\*)/g).map((part, i) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={i} style={{ color: 'var(--primary)' }}>{part.slice(2, -2)}</strong>;
                      }
                      return part;
                    });
                    return <p key={idx} style={{ marginBottom: '1rem', margin: 0 }}>{formattedText}</p>;
                  })}
                </div>
              ) : (
                <div style={{ padding: '1rem', borderLeft: '4px solid var(--border)', backgroundColor: 'rgba(255,255,255,0.5)', borderRadius: '0 12px 12px 0' }}>
                  <p className="font-body-md" style={{ margin: 0, color: 'var(--text-muted)' }}>Complete a chat session to generate your personalized wellness insights and analysis.</p>
                </div>
              )}
            </div>
          </div>

        </section>
      </div>
    </div>
  );
};

export default Dashboard;
