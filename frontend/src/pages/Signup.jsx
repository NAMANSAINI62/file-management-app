import { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { signup } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signup(email, password, name);
      navigate('/login');
    } catch (err) {
      let serverMessage = 'Signup failed. Please try again.';
      if (err.response && err.response.data && err.response.data.error) {
        serverMessage = err.response.data.error;
      }
      setError(serverMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-100">
      <div className="bg-white p-8 rounded-3xl shadow-md w-96">
        <h2 className="text-2xl font-bold mb-6 text-center text-green-400">
          {"Create an Account"}
        </h2>

        {error && (
          <div className="mb-4 bg-red-100 border border-red-200 text-red-700 text-sm px-3 py-2 rounded-lg text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSignup} className="flex flex-col space-y-4">
          <div>
            <label className="block text-gray-600 text-sm font-medium mb-1">
              {"Full Name"}
            </label>
            <input 
              type="text" 
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-600 text-sm font-medium mb-1">
              {"Email Address"}
            </label>
            <input 
              type="email" 
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div>
            <label className="block text-gray-600 text-sm font-medium mb-1">
              {"Password"}
            </label>
            <input 
              type="password" 
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-2xl hover:bg-green-700 transition duration-200 mt-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>

          <p className="text-sm text-center text-gray-600">
            {"Already have an account? "}
            <Link to="/login" className="text-green-600 font-medium">
              {"Login"}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default Signup;