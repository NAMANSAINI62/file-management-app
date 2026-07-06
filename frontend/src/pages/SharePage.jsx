import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getSharedFile } from '../services/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function SharePage() {
  const { shareToken } = useParams();
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    async function loadFile() {
      try {
        const data = await getSharedFile(shareToken);
        setFile(data);
      } catch (err) {
        if (err.response?.status === 410) {
          setError('This share link has expired.');
        } else {
          setError('File not found or this link is invalid.');
        }
      } finally {
        setLoading(false);
      }
    }
    loadFile();
  }, [shareToken]);

  async function handleDownload() {
    setDownloading(true);
    try {
      const response = await fetch(`${API_BASE}/api/share/${shareToken}/download`);
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.original_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Download failed. Please try again.');
    } finally {
      setDownloading(false);
    }
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' Bytes';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function formatExpiry(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50">
        <p className="text-slate-500 text-lg animate-pulse">{"Loading shared file..."}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50">
        <div className="bg-white rounded-2xl shadow-lg p-10 text-center max-w-sm w-full mx-4">
          <div className="text-5xl mb-4">{"🔒"}</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">{"Access Denied"}</h2>
          <p className="text-gray-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50 p-6">
      <div className="bg-white rounded-2xl shadow-lg p-10 text-center max-w-md w-full mx-4">
        <div className="text-6xl mb-4">{"📄"}</div>
        <h1 className="text-2xl font-bold text-slate-800 mb-1">{file.original_name}</h1>
        <p className="text-slate-400 text-sm mb-1">{formatSize(file.file_size)}</p>
        <p className="text-amber-500 text-xs mb-6">
          {"⏳ Link expires: "}{formatExpiry(file.share_expires_at)}
        </p>

        {file.summary && (
          <div className="bg-gray-50 rounded-xl p-4 text-left text-sm text-gray-600 mb-6">
            {file.summary}
          </div>
        )}

        <button
          onClick={handleDownload}
          disabled={downloading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {downloading ? 'Downloading...' : '📥 Download File'}
        </button>
      </div>
    </div>
  );
}

export default SharePage;
