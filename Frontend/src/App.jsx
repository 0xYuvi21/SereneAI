import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Profile from './pages/Profile';
import Journal from './pages/Journal';
import ProtectedLayout from './components/ProtectedLayout';

const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  { path: "/register", element: <Register /> },
  { 
    element: <ProtectedLayout />,
    children: [
      { path: "/", element: <Navigate to="/dashboard" replace /> },
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/profile", element: <Profile /> },
      { path: "/journal", element: <Journal /> },
      { path: "/chat", element: <Chat /> }
    ]
  }
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
