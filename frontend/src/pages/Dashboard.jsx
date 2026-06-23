import { useContext, useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import UploadDropzone from '../components/UploadDropzone';
import FileList from '../components/FileList';
import { getFiles } from '../services/api';

function Dashboard() {
  const { user, logout } = useContext(AuthContext);
  const [files, setFiles] = useState([]);
  const pollingRef = useRef(null);
  
  const navigate = useNavigate();

  const fetchFiles = async () => {
    try {
      const data = await getFiles();
      setFiles(data);
      return data;
    } catch (err) {
      console.error('Failed to load files:', err);
      return [];
    }
  };

  const startPollingIfNeeded = (fileList) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    const hasProcessing = fileList.some(
      (f) => !f.summary || f.summary === 'Processing...'
    );

    if (hasProcessing) {
      pollingRef.current = setInterval(async () => {
        const freshData = await fetchFiles();
        const stillProcessing = freshData.some(
          (f) => !f.summary || f.summary === 'Processing...'
        );
        if (!stillProcessing) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }, 3000);
    }
  };

  useEffect(() => {
    const init = async () => {
      const data = await fetchFiles();
      startPollingIfNeeded(data);
    };
    init();

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const handleListRefresh = async () => {
    const data = await fetchFiles();
    startPollingIfNeeded(data);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg">
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
        
        <div className="mt-8">
          <h2 className="text-xl font-bold text-slate-800 mb-3">{"Upload New Files"}</h2>
          <UploadDropzone onUploadSuccess={handleListRefresh} />
        </div>

        <div className="mt-10 border-t pt-8 border-slate-200">
          <h2 className="text-xl font-bold text-slate-800 mb-3">{"Your Uploaded Files"}</h2>
          <FileList files={files} onRefresh={handleListRefresh} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;