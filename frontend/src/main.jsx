import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

createRoot(document.getElementById('root')).render(
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
)

// Maine app ko AuthProvider se wrap kiya taaki auth state globally available ho jaye bina props pass kiye and to avoid props drilling.  
// aur BrowserRouter se isliye wrap kiya taaki routing aur redirects proper kaam karein bina page reload ke.