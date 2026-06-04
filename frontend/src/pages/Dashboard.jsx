import { useContext, useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import UploadDropzone from '../components/UploadDropzone';
import FileList from '../components/FileList';
import { getFiles } from '../services/api';

function Dashboard() {
  const { user, logout } = useContext(AuthContext); // Global logout aur user info
  const [files, setFiles] = useState([]); // User ki files ki memory (state)
  const pollingRef = useRef(null); // Polling interval ka reference
  
  const navigate = useNavigate();

  // 1. Backend se files check karke state mein dalne ka function hh
  const fetchFiles = async () => {
    try {
      const data = await getFiles();
      setFiles(data); // State update ho gayi
      return data;
    } catch (err) {
      console.error('Failed to load files:', err);
      return [];
    }
  };

  // 2. Polling start karo — har 3 second mein check karo jab tak koi file "Processing..." hai
  const startPollingIfNeeded = (fileList) => {
    // Pehle purana interval saaf karo agar chal raha ho
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    // Check karo koi file abhi bhi processing mein hai ya nahi
    const hasProcessing = fileList.some(
      (f) => !f.summary || f.summary === 'Processing...'
    );

    if (hasProcessing) {
      pollingRef.current = setInterval(async () => {
        const freshData = await fetchFiles();
        const stillProcessing = freshData.some(
          (f) => !f.summary || f.summary === 'Processing...'
        );
        // Jab sab summaries aa gayi, polling band karo
        if (!stillProcessing) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }, 3000); // Har 3 second mein check karo
    }
  };

  // 3. Page load hote hi files fetch karo + polling start karo
  useEffect(() => {
    const init = async () => {
      const data = await fetchFiles();
      startPollingIfNeeded(data);
    };
    init();

    // Component unmount hone par polling saaf karo
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // 4. Wrapper function for manual actions (upload/delete)
  const handleListRefresh = async () => {
    const data = await fetchFiles();
    startPollingIfNeeded(data);
  };

  // 5. Logout action
  const handleLogout = async () => {
    await logout();
    navigate('/login'); // Wapas login page par bhejdo
  };

  return (
    // Background style: Light grey background and full height
    <div className="min-h-screen bg-slate-100 p-6">
      
      {/* Container Card */}
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
        
        {/* Header/Navbar Section */}
        <div className="flex items-center justify-between border-b pb-6 border-slate-200">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">{"File Dashboard"}</h1>
            <p className="mt-1 text-slate-500 text-sm">
              {"Welcome back, "}<span className="font-semibold text-slate-700">{user?.name || 'User'}</span>
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="rounded-xl bg-red-500 hover:bg-red-600 text-white px-5 py-2 font-medium transition duration-200 active:scale-95 cursor-pointer"
          >
            {"Logout"}
          </button>
        </div>
        
        {/* Upload Dropzone Section */}
        <div className="mt-8">
          <h2 className="text-xl font-bold text-slate-800 mb-3">{"Upload New Files"}</h2>
          {/* We pass 'handleListRefresh' so dropzone can trigger list refresh AND polling after uploading */}
          <UploadDropzone onUploadSuccess={handleListRefresh} />
        </div>

        {/* Files List Section */}
        <div className="mt-10 border-t pt-8 border-slate-200">
          <h2 className="text-xl font-bold text-slate-800 mb-3">{"Your Uploaded Files"}</h2>
          {/* We pass 'files' state and 'handleListRefresh' refresh callback to the table */}
          <FileList files={files} onRefresh={handleListRefresh} />
        </div>

      </div>
    </div>
  );
}

export default Dashboard;

// onClick={handleLogout} (without parentheses): → This passes the function reference.
// The function does NOT execute until the user clicks the button and When the user clicks the button, React calls handleLogout()

// onClick={handleLogout()} (with parentheses): → It executes the function IMMEDIATELY when the component renders.
// The function returns undefined, so nothing happens and the user gets redirected to /login immediately after page loads.