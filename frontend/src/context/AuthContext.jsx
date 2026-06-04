import { createContext, useState, useEffect } from 'react';
import { loginUser, signupUser, logoutUser, getCurrentUser } from '../services/api';

// 1. Ek context box banaya jiske andar data share hoga
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  // States (Components ki Memory)
  const [user, setUser] = useState(null); // User ka data store karne ke liye
  const [isAuthenticated, setIsAuthenticated] = useState(false); // Logged in status (true/false)
  const [loading, setLoading] = useState(true); // Page load hote waqt checking status

  // 2. useEffect: Page load hote hi automatically backend se check karega ki user logged in hai ya nahi
  useEffect(() => {
    // : Async functions without try/catch will throw unhandled promise rejections.
    async function checkSession() {
      try {
        const data = await getCurrentUser();
        // Agar backend user data return karta hai (session active hai)
        if (data.user) {
          setUser(data.user);
          setIsAuthenticated(true);
        } 
      } catch (err) {
        console.log("No active session found.");
      } finally {
        setLoading(false); // Checking finish ho gayi
      }
    }
    checkSession();
  }, []); // [] khali hai, matlab yeh sirf page load par 1 baar chalega

  // 3. Login function: page isko call karega
  const login = async (email, password) => {
    // api.js se direct axios call karenge
    const userData = await loginUser(email, password);
    setUser(userData); // State update
    setIsAuthenticated(true); // User ko log in mark kiya
  };

  // 4. Signup function: registration page isko call karega
  const signup = async (email, password, name) => {
    await signupUser(email, password, name);
    // Ab yahan direct login set nahi karenge, user khud login page par jayega
  };

  // 5. Logout function
  const logout = async () => {
    try {
      await logoutUser(); // Backend session remove karega
    } catch (err) {
      console.error("Logout error", err);
    } finally {
      setUser(null); // User reset
      setIsAuthenticated(false); // Logout status mark kiya
    }
  };

  // 6. Loader Screen: Agar checks chal rahe hain, toh simple message dikhao
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-100 text-slate-600 font-semibold">
        Checking session...
      </div>
    );
  }

  // 7. Jab checking complete ho jaye, tab children pages (Login, Signup, Dashboard) render karo
  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};