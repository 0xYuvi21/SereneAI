import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Video, VideoOff } from 'lucide-react';
import { useBlocker } from 'react-router-dom';
import api from '../services/api';

const Chat = () => {
  const [messages, setMessages] = useState([
    { id: 1, role: 'bot', text: 'Hello! I am SereneBot, your AI companion. How are you feeling today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endOfMessagesRef = useRef(null);

  const [sentiment, setSentiment] = useState('neutral');
  const [dropoutRisk, setDropoutRisk] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraPermissionDenied, setCameraPermissionDenied] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);

  const [endingSession, setEndingSession] = useState(false);

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      sessionId !== null && currentLocation.pathname !== nextLocation.pathname
  );

  const handleEndSession = async () => {
    setEndingSession(true);
    try {
      await api.put(`/sessions/${sessionId}/end`, { 
        emotion_at_end: sentiment,
        session_quality_score: 5 
      });
      localStorage.removeItem('session_id');
      setSessionId(null);
      if (blocker.state === 'blocked') {
        blocker.proceed();
      }
    } catch (err) {
      console.error("Failed to end session", err);
      if (blocker.state === 'blocked') {
        blocker.proceed();
      }
    } finally {
      setEndingSession(false);
    }
  };

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (sessionId) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sessionId]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    // Initial load: Fetch analytics to provide to chat context
    const loadContext = async () => {
      try {
        const userRes = await api.get('/users/me');
        const userId = userRes.data.user_id || userRes.data.id;
        
        const [emotionRes, riskRes] = await Promise.all([
          api.get(`/analytics/emotion-trends/${userId}`).catch(() => ({ data: { trends: [] } })),
          api.get(`/analytics/dropout-risk/${userId}`).catch(() => ({ data: { risk_score: 0 } }))
        ]);
        
        const trends = emotionRes.data.trends || [];
        // If last score < 50, mark as negative
        if (trends.length > 0 && trends[trends.length - 1].score < 50) {
          setSentiment('negative');
        }
        
        const risk = riskRes.data.risk_score;
        if (risk === 'High' || risk > 70) {
          setDropoutRisk(true);
        }
        
        // Check if we already have a session from login
        let currentSessionId = localStorage.getItem('session_id');
        
        if (!currentSessionId) {
          // Fallback: start a new session if one doesn't exist
          const sessionRes = await api.post('/sessions/start', { emotion_at_start: sentiment || 'neutral' });
          currentSessionId = sessionRes.data.session_id;
          localStorage.setItem('session_id', currentSessionId);
        }
        
        setSessionId(currentSessionId);
        
        try {
          const historyRes = await api.get(`/conversations/${currentSessionId}`);
          if (historyRes.data && historyRes.data.length > 0) {
            const historyMessages = [];
            historyRes.data.forEach(msg => {
              historyMessages.push({ id: `user-${msg.conversation_id}`, role: 'user', text: msg.user_input });
              historyMessages.push({ id: `bot-${msg.conversation_id}`, role: 'bot', text: msg.bot_response });
            });
            setMessages([
              { id: 1, role: 'bot', text: 'Hello! I am SereneBot, your AI companion. How are you feeling today?' },
              ...historyMessages
            ]);
          }
        } catch (historyErr) {
            console.error("Failed to load chat history:", historyErr);
        }
        
      } catch (err) {
        console.error("Could not load context for chat", err);
      }
    };
    loadContext();
  }, []);

  useEffect(() => {
    let stream = null;
    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsCameraActive(true);
          setCameraPermissionDenied(false);
        }
      } catch (err) {
        console.warn("Camera permission denied or not available", err);
        setCameraPermissionDenied(true);
        setIsCameraActive(false);
        setCameraEnabled(false);
      }
    };
    
    if (cameraEnabled) {
      startCamera();
    } else {
      if (videoRef.current && videoRef.current.srcObject) {
         videoRef.current.srcObject.getTracks().forEach(track => track.stop());
         videoRef.current.srcObject = null;
      }
      setIsCameraActive(false);
    }
    
    return () => {
      if (stream) {
         stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraEnabled]);

  const typewriterAnimate = (botMessageId, fullText) => {
    let i = 0;
    // Start with the first character already shown
    setMessages((prev) =>
      prev.map(msg => msg.id === botMessageId ? { ...msg, text: fullText[0] || '' } : msg)
    );
    const interval = setInterval(() => {
      i++;
      if (i >= fullText.length) {
        clearInterval(interval);
        return;
      }
      setMessages((prev) =>
        prev.map(msg =>
          msg.id === botMessageId ? { ...msg, text: fullText.slice(0, i + 1) } : msg
        )
      );
    }, 18); // ~18ms per character — smooth but not too slow
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { id: Date.now(), role: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const startTime = Date.now();
      
      let base64Image = null;
      if (cameraEnabled && !cameraPermissionDenied && videoRef.current && canvasRef.current && videoRef.current.readyState >= 2) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          base64Image = canvas.toDataURL('image/jpeg', 0.8);
        }
      }

      // Await the full JSON response — thinking bubble stays visible the whole time
      const res = await api.post('/chat/', {
        message: userMessage.text,
        sentiment: sentiment,
        dropout_risk: dropoutRisk,
        image: base64Image,
      });

      const replyText = res.data.response || '';
      const responseTime = (Date.now() - startTime) / 1000;

      // Hide thinking bubble, insert bot message with empty text
      setLoading(false);
      const botMessageId = Date.now() + 1;
      setMessages((prev) => [...prev, { id: botMessageId, role: 'bot', text: '' }]);

      // Simulate smooth streaming via typewriter effect
      typewriterAnimate(botMessageId, replyText);

      // Persist conversation
      if (sessionId) {
        await api.post('/conversations/', {
          session_id: sessionId,
          user_input: userMessage.text,
          bot_response: replyText || '[Error: Empty response]',
          sentiment_score: sentiment === 'negative' ? -1.0 : 0.0,
          response_time: parseFloat(responseTime.toFixed(2)),
        }).catch(e => console.error('Failed to log conversation:', e));
      }

    } catch (err) {
      console.error(err);
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'bot', text: 'Sorry, I am having trouble connecting to the server right now. Please try again later.' },
      ]);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '800px', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 4rem)' }}>
      <video ref={videoRef} autoPlay playsInline muted style={{ display: 'none' }}></video>
      <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ color: 'var(--primary)', marginBottom: '0.25rem' }}>SereneAI Chat</h2>
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>Speak freely with your AI companion.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isCameraActive && (
            <span style={{ fontSize: '0.75rem', color: '#854d0e', backgroundColor: '#fef08a', padding: '0.5rem 0.75rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '500' }}>
              <span style={{ width: '8px', height: '8px', backgroundColor: '#ef4444', borderRadius: '50%', display: 'inline-block', flexShrink: 0, animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}></span>
              Camera Active (Emotion Tracking)
            </span>
          )}
          <button 
            type="button"
            onClick={() => setCameraEnabled(!cameraEnabled)}
            style={{ 
              display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', 
              borderRadius: '20px', border: '1px solid var(--border)', 
              backgroundColor: cameraEnabled ? 'var(--primary-light)' : '#fff', 
              color: cameraEnabled ? 'var(--primary)' : 'var(--text-muted)', 
              cursor: 'pointer', transition: 'all 0.2s', fontWeight: '500'
            }}
            title={cameraEnabled ? "Turn off emotion sensor" : "Turn on emotion sensor"}
          >
            {cameraEnabled ? <Video size={18} /> : <VideoOff size={18} />}
            {cameraEnabled ? "On" : "Off"}
          </button>
        </div>
      </div>

      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
        {/* Chat History */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', backgroundColor: '#fdfdfd' }}>
          {messages.map((msg) => (
            <div key={msg.id} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
              {msg.role === 'bot' && (
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Bot size={20} />
                </div>
              )}
              
              <div style={{ 
                padding: '1rem 1.25rem', 
                borderRadius: '16px', 
                backgroundColor: msg.role === 'user' ? 'var(--primary)' : 'var(--surface)', 
                color: msg.role === 'user' ? '#fff' : 'var(--text-main)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
                borderBottomLeftRadius: msg.role === 'bot' ? '4px' : '16px',
                lineHeight: '1.5'
              }}>
                {msg.text}
              </div>

              {msg.role === 'user' && (
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'var(--bg-color)', border: '1px solid var(--border)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <User size={20} />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', maxWidth: '80%' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '50%',
                backgroundColor: 'var(--primary-light)', color: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
              }}>
                <Bot size={20} />
              </div>
              <div style={{
                padding: '1rem 1.25rem', borderRadius: '16px', borderBottomLeftRadius: '4px',
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', gap: '5px'
              }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--primary)', display: 'inline-block', animation: 'typingBounce 1.2s ease-in-out infinite', animationDelay: '0s' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--primary)', display: 'inline-block', animation: 'typingBounce 1.2s ease-in-out infinite', animationDelay: '0.2s' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--primary)', display: 'inline-block', animation: 'typingBounce 1.2s ease-in-out infinite', animationDelay: '0.4s' }} />
              </div>
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>

        {/* Chat Input */}
        <div style={{ borderTop: '1px solid var(--border)', padding: '1.5rem', backgroundColor: '#fff' }}>
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
             <div style={{ flex: 1 }}>
                <textarea 
                  className="input-field" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e); } }}
                  placeholder="Type a message..."
                  style={{ resize: 'none', height: '60px', borderRadius: '12px', padding: '1rem' }}
                  disabled={loading}
                />
             </div>
             <button type="submit" className="btn btn-primary" style={{ padding: '0', width: '60px', height: '60px', borderRadius: '12px' }} disabled={loading || !input.trim()}>
                <Send size={24} />
             </button>
          </form>
        </div>
      </div>

      {/* Session End Banner Modal */}
      {blocker.state === "blocked" && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="card" style={{ padding: '2rem', maxWidth: '400px', width: '90%', textAlign: 'center' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--text-main)' }}>Do you want to end the session?</h3>
            <p style={{ marginBottom: '2rem', color: 'var(--text-muted)' }}>
              Leaving will officially end this chat session and record your metrics like session duration and message count.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => blocker.reset()}
                disabled={endingSession}
              >
                No, continue
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleEndSession}
                disabled={endingSession}
              >
                {endingSession ? 'Ending...' : 'Yes, end session'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
