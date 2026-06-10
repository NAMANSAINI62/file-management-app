import { createContext, useState, useEffect } from 'react';
import { loginUser, signupUser, logoutUser, getCurrentUser } from '../services/api';

// 1. Context box banaya jiske andar user data share hoga
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  // States (Components ki Memory)
  const [user, setUser] = useState(null); // User ka data store karne ke liye
  const [isAuthenticated, setIsAuthenticated] = useState(false); // Logged in status (true/false)
  const [loading, setLoading] = useState(true); // Page load hote waqt checking status

  // 2. Page load hote hi check karo ki localStorage mein token hai ya nahi
  useEffect(() => {
    async function checkSession() {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        // Token hai toh backend se user data verify karo
        const data = await getCurrentUser();
        if (data.user) {
          setUser(data.user);
          setIsAuthenticated(true);
        } else {
          // Token invalid ya expired hai toh hata do
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

  // 3. Login: token ko localStorage mein save karo
  const login = async (email, password) => {
    const userData = await loginUser(email, password);
    // Backend se token aaya — use localStorage mein store karo
    localStorage.setItem('authToken', userData.token);
    setUser({ id: userData.id, email: userData.email, name: userData.name });
    setIsAuthenticated(true);
  };

  // 4. Signup
  const signup = async (email, password, name) => {
    await signupUser(email, password, name);
  };

  // 5. Logout: token ko localStorage se hata do
  const logout = async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.error("Logout error", err);
    } finally {
      localStorage.removeItem('authToken'); // Token delete — user logged out
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  // 6. Loader screen while checking token
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-100 text-slate-600 font-semibold">
        Checking session...
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};