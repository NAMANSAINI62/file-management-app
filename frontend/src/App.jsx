import { Navigate, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} /> // If we write this line before any other routes then it matches everything, hence specific routes ignored. So we write it at the last.
    </Routes>
  );
}

export default App;

// replace React Router ke <Navigate> component mein ek boolean prop hai jo browser history stack ko control karta hai redirection ke waqt.
// Routes allow you to show different components at different URLs
// Routes handle browser history properly