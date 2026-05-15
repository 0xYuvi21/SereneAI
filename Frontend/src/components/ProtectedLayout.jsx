import { Outlet, Navigate, Link } from 'react-router-dom';

const ProtectedLayout = () => {
  // Simple token check for unauthenticated users
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-layout">
      {/* Sidebar will go here */}
      <nav style={{
        width: '250px', 
        height: '100vh', 
        position: 'fixed', 
        backgroundColor: '#fff',
        borderRight: '1px solid var(--border)',
        padding: '2rem 1rem'
      }}>
        <h2 style={{ color: 'var(--primary)', marginBottom: '2rem', textAlign: 'center' }}>
          SereneAI
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Link to="/dashboard" className="btn btn-secondary" style={{ width: '100%' }}>Dashboard</Link>
          <Link to="/profile" className="btn btn-secondary" style={{ width: '100%' }}>Profile</Link>
          <Link to="/chat" className="btn btn-secondary" style={{ width: '100%' }}>Chat Assistant</Link>
          <button 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: 'auto' }}
            onClick={() => {
              localStorage.removeItem('token');
              window.location.href = '/login';
            }}
          >
            Logout
          </button>
        </div>
      </nav>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default ProtectedLayout;
