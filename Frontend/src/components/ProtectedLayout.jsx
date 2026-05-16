import { Outlet, Navigate, Link, useLocation } from 'react-router-dom';

const ProtectedLayout = () => {
  const token = localStorage.getItem('token');
  const location = useLocation();
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const navItems = [
    { path: '/dashboard', icon: 'home', label: 'Home' },
    { path: '/journal', icon: 'book', label: 'Journal' },
    { path: '/chat', icon: 'chat_bubble', label: 'Chat' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="bg-background text-on-surface min-h-screen">
      {/* TopNavBar Navigation Shell */}
      <nav style={{ position: 'fixed', top: 0, width: '100%', zIndex: 50, backgroundColor: 'rgba(251, 249, 245, 0.8)', backdropFilter: 'blur(24px)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '64px', padding: '0 2rem', maxWidth: '1140px', margin: '0 auto' }}>
          <div className="font-headline-md" style={{ color: 'var(--primary)' }}>SereneAI</div>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }} className="hidden-mobile">
            {navItems.map((item) => (
              <Link 
                key={item.label} 
                to={item.path} 
                className="font-body-md" 
                style={{ 
                  color: isActive(item.path) ? 'var(--primary)' : 'var(--text-muted)',
                  borderBottom: isActive(item.path) ? '2px solid var(--primary)' : 'none',
                  paddingBottom: isActive(item.path) ? '4px' : '0'
                }}
              >
                {item.label}
              </Link>
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span className="material-symbols-outlined" style={{ color: 'var(--text-muted)', cursor: 'pointer' }}>notifications</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--on-primary-container)', fontWeight: 'bold', fontSize: '14px', cursor: 'pointer' }}>
              Y
            </div>
          </div>
        </div>
      </nav>

      {/* SideNavBar Shell (Web Only) */}
      <aside className="sidebar-desktop" style={{ position: 'fixed', left: 0, top: 0, height: '100%', width: '256px', backgroundColor: 'var(--surface-container-low)', borderRight: '1px solid var(--border)', zIndex: 40, padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ marginBottom: '2rem', marginTop: '64px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '12px', backgroundColor: 'var(--primary-container)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--on-primary-container)', fontWeight: 'bold' }}>
              Y
            </div>
            <div>
              <div className="font-label-md" style={{ color: 'var(--primary)' }}>Welcome back</div>
              <div className="font-label-sm" style={{ color: 'var(--text-muted)' }}>Yuvaraj</div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {navItems.map((item) => (
              <Link 
                key={item.label} 
                to={item.path}
                style={{ 
                  display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', borderRadius: '12px', 
                  backgroundColor: isActive(item.path) ? 'var(--primary-container)' : 'transparent',
                  color: isActive(item.path) ? 'var(--on-primary-container)' : 'var(--text-muted)',
                  transition: 'all 0.2s'
                }}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="font-label-md">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>

        <button 
          className="font-label-md"
          style={{ width: '100%', padding: '0.75rem', backgroundColor: 'var(--primary)', color: 'var(--on-primary)', borderRadius: '9999px', border: 'none', cursor: 'pointer', boxShadow: 'var(--shadow-sm)', transition: 'transform 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
          onClick={() => window.location.href = '/chat'}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>chat_bubble</span> Start Session
        </button>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <Link to="/profile" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', color: 'var(--text-muted)', borderRadius: '12px' }}>
            <span className="material-symbols-outlined">settings</span>
            <span className="font-label-md">Settings</span>
          </Link>
          <button 
            onClick={() => {
              localStorage.removeItem('token');
              window.location.href = '/login';
            }}
            style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem', color: 'var(--danger)', borderRadius: '12px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}
          >
            <span className="material-symbols-outlined">logout</span>
            <span className="font-label-md">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Canvas */}
      <main className="main-content-area" style={{ paddingTop: '80px', paddingBottom: '80px', minHeight: '100vh' }}>
        <Outlet />
      </main>

      {/* Mobile BottomNavBar */}
      <nav className="mobile-bottom-nav" style={{ position: 'fixed', bottom: 0, width: '100%', backgroundColor: 'rgba(251, 249, 245, 0.9)', backdropFilter: 'blur(24px)', borderTop: '1px solid var(--border)', zIndex: 50 }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', height: '64px' }}>
          {navItems.map((item) => (
            <Link 
              key={item.label} 
              to={item.path}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', color: isActive(item.path) ? 'var(--primary)' : 'var(--text-muted)' }}
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive(item.path) ? "'FILL' 1" : "'FILL' 0" }}>{item.icon}</span>
              <span style={{ fontSize: '10px' }} className="font-label-sm">{item.label.split(' ')[0]}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default ProtectedLayout;
