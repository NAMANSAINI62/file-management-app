import { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Login() {
  // 1. Local state (Memory) to keep track of what the user is typing
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(''); // To show error messages
  const [loading, setLoading] = useState(false); // To show loading state

  // 2. Consume global auth function
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault(); // Prevents page reload
    setError('');
    setLoading(true);

    try {
      // Call the login function from our AuthContext
      await login(email, password);
      // Redirect to Dashboard if credentials are correct
      navigate('/dashboard');
    } catch (err) {
      // Backend status code validation response error or fallback
      let serverMessage = 'Login failed. Please try again.';
      if (err.response && err.response.data && err.response.data.error) {
        serverMessage = err.response.data.error;
      }
      setError(serverMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    // 'flex items-center justify-center' puts the login box exactly in the middle
    <div className="min-h-screen flex items-center justify-center bg-blue-100">
      
      {/* This is the white box in the middle holding the form */}
      <div className="bg-white p-8 rounded-3xl shadow-2xl w-96">
        
        <h2 className="text-2xl font-bold mb-6 text-center text-yellow-400">
          {"Welcome Back"}
        </h2>

        {/* Error Message Alert (if any error occurs) */}
        {error && (
          <div className="mb-4 bg-red-100 border border-red-200 text-red-700 text-sm px-3 py-2 rounded-lg text-center font-medium">
            {error}
          </div>
        )}

        {/* The actual form */}
        <form onSubmit={handleLogin} className="flex flex-col space-y-4">
          
          {/* Email Input */}
          <div>
            <label className="block text-gray-600 text-sm font-medium mb-1">
              {"Email Address"}
            </label>
            <input 
              type="email" 
              placeholder="Enter your email"
              value={email} // Connects input to our 'email' state
              onChange={(e) => setEmail(e.target.value)} // Updates the state when typing
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
              required
            />
          </div>

          {/* Password Input */}
          <div>
            <label className="block text-gray-600 text-sm font-medium mb-1">
              {"Password"}
            </label>
            <input 
              type="password" 
              placeholder="Enter your password"
              value={password} // Connects input to our 'password' state
              onChange={(e) => setPassword(e.target.value)} // Updates the state when typing
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
              required
            />
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-yellow-400 text-white py-2 rounded-2xl hover:bg-yellow-500 active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <p className="text-sm text-center text-gray-600">
            {"Don't have an account? "}
            <Link to="/signup" className="text-yellow-600 font-medium">
              {"Sign up Now"}
            </Link>
          </p>

        </form>

      </div>
    </div>
  );
}

export default Login;
