import { createContext, useState, useEffect } from 'react';
import { loginUser, signupUser, logoutUser, getCurrentUser } from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkSession() {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await getCurrentUser();
        if (data.user) {
          setUser(data.user);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('authToken');
        }
      } catch (err) {
        console.log("Session check failed, clearing token.");
        localStorage.removeItem('authToken');
      } finally {
        setLoading(false);
      }
    }
    checkSession();
  }, []);

  const login = async (email, password) => {
    const userData = await loginUser(email, password);
    localStorage.setItem('authToken', userData.token);
    setUser({ id: userData.id, email: userData.email, name: userData.name });
    setIsAuthenticated(true);
  };

  const signup = async (email, password, name) => {
    await signupUser(email, password, name);
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.error("Logout error", err);
    } finally {
      localStorage.removeItem('authToken');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-100 text-slate-600 font-semibold">
        {"Checking session..."}
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};