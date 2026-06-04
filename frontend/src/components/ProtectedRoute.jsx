import { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

// Yeh component ek "security guard" ki tarah kaam karta hai. or yeh children sirf dashboard hh 
// Agar user logged-in hai, toh andar waala page (dashboard.jsx) dikhayega.
// Agar logged-in NAHI hai, toh seedha /login page par redirect krr dega.

function ProtectedRoute({ children }) {
  // 1. AuthContext se check karo ki user logged in hai ya nahi
  const { isAuthenticated } = useContext(AuthContext);

  // 2. Agar user logged-in NAHI hai, toh login page par redirect karo
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
    // 'replace' ka matlab: browser ki back button history mein dashboard ka URL save nahi hoga
  }

  // 3. Agar user logged-in HAI, toh jo bhi page iske andar wrap kiya hai (Dashboard), use dikhao
  return children;
}
export default ProtectedRoute;

// Kaise use hota hai yeh component? App.jsx mein:
// <ProtectedRoute>
// Dashboard page yeh pages hh <-- yeh "children" hai
// app.py: Saara main logic, rules, database, aur brain yahan hota hai.
// api.js: Iska kaam bas un routes (/api/login, /api/upload) ko call lagana hai aur wahan se data laakar React components ko dena hai.
// with credentials true acts as a bridge for sending sensitive data across different network addresses.
// Cross-Origin Permission: It allows the browser to send cookies/session data between different addresses this helps browser to identify who is making request.