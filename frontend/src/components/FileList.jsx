import { useState } from 'react';
import { deleteFile, shareFile, unshareFile } from '../services/api';

function FileList(props) {
  const files = props.files;
  const onRefresh = props.onRefresh;

  const [fileToDelete, setFileToDelete] = useState(null);
  const [summaryFile, setSummaryFile] = useState(null);
  const [sharingFile, setSharingFile] = useState(null);
  const [copied, setCopied] = useState(false);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  async function handleShareBtn(file) {
    try {
      if (file.share_token) {
        setSharingFile(file);
      } else {
        const updatedFile = await shareFile(file.id);
        setSharingFile(updatedFile);
        if (onRefresh) onRefresh();
      }
    } catch (error) {
      alert("Error sharing file");
    }
  }

  async function handleUnshare() {
    try {
      await unshareFile(sharingFile.id);
      setSharingFile(null);
      if (onRefresh) onRefresh();
    } catch (error) {
      alert("Error unsharing file");
    }
  }

  function handleCopyLink() {
    const shareUrl = `${window.location.origin}/share/${sharingFile.share_token}`;
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function formatSize(bytes) {
    if (bytes === 0) {
      return "0 Bytes";
    }
    
    if (bytes < 1024) {
      return bytes + " Bytes";
    } else if (bytes < 1024 * 1024) {
      const kb = bytes / 1024;
      return kb.toFixed(2) + " KB";
    } else {
      const mb = bytes / (1024 * 1024);
      return mb.toFixed(2) + " MB";
    }
  }

  function formatDate(dateString) {
    if (dateString === null) {
      return "No Date";
    }
    const dateObj = new Date(dateString);
    return dateObj.toLocaleString();
  }

  function handleDeleteBtn(file) {
    setFileToDelete(file); 
  }

  async function confirmDelete() {
    try {
      await deleteFile(fileToDelete.id);
      setFileToDelete(null);
      
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      console.log("Delete error:", error);
    }
  }

  async function handleDownloadBtn(file) {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/files/${file.id}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        redirect: 'follow',
      });
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
    } catch (error) {
      alert("Error downloading file");
      console.error(error);
    }
  }

  if (files.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-2xl border border-gray-200">
        {"No files uploaded yet. Please upload a file from above."}
      </div>
    );
  }

  return (
    <div>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden overflow-x-auto">
        <table className="w-full text-left border-collapse">
        <thead className="bg-gray-100 border-b border-gray-200">
          <tr>
            <th className="p-4 font-semibold text-gray-600 text-sm">{"File Name"}</th>
            <th className="p-4 font-semibold text-gray-600 text-sm">{"Size"}</th>
            <th className="p-4 font-semibold text-gray-600 text-sm">{"Upload Date"}</th>
            <th className="p-4 font-semibold text-gray-600 text-sm text-center">{"Actions"}</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => {
            return (
              <tr key={file.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="p-4 text-gray-800 font-medium">
                  {file.original_name}
                </td>
                <td className="p-4 text-gray-500 text-sm">
                  {formatSize(file.file_size)}
                </td>
                <td className="p-4 text-gray-500 text-sm">
                  {formatDate(file.created_at)}
                </td>
                <td className="p-4 flex justify-center space-x-2">
                  <button 
                    onClick={() => setSummaryFile(file)}
                    disabled={!file.summary || file.summary === 'Processing...'}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${
                      !file.summary || file.summary === 'Processing...'
                        ? 'bg-amber-50 text-amber-500 animate-pulse cursor-not-allowed'
                        : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                    }`}
                  >
                    {!file.summary || file.summary === 'Processing...' ? '⏳ Processing...' : '📄 Summary'}
                  </button>
                   <button 
                    onClick={() => handleDownloadBtn(file)}
                    className="bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-blue-200 cursor-pointer"
                  >
                    {"Download"}
                  </button>
                  <button 
                    onClick={() => handleShareBtn(file)}
                    className="bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-200 cursor-pointer"
                  >
                    {file.share_token ? "🔗 Shared" : "🔗 Share"}
                  </button>
                  <button 
                    onClick={() => handleDeleteBtn(file)}
                    className="bg-red-100 text-red-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-red-200 cursor-pointer"
                  >
                    {"Delete"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>

    {fileToDelete && (
      <div className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-xl shadow-lg text-center max-w-sm w-full mx-4">
          <div className="text-red-500 text-4xl mb-3">⚠️</div>
          <h3 className="text-lg font-bold text-gray-800 mb-2">{"Delete File?"}</h3>
          <p className="text-gray-600 text-sm mb-6">
            {"Are you sure you want to delete "}<span className="font-semibold">{`"${fileToDelete.original_name}"`}</span>{"? This action cannot be undone."}
          </p>
          <div className="flex justify-center space-x-3">
            <button 
              onClick={() => setFileToDelete(null)} 
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium transition duration-200"
            >
              {"Cancel"}
            </button>
            <button 
              onClick={confirmDelete} 
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium shadow-sm transition duration-200 active:scale-95"
            >
              {"Yes, Delete"}
            </button>
          </div>
        </div>
      </div>
    )}

    {summaryFile && (
      <div className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-xl shadow-lg text-center max-w-md w-full mx-4">
          <div className="text-purple-500 text-4xl mb-3">{"📄"}</div>
          <h3 className="text-lg font-bold text-gray-800 mb-1">{"AI Summary"}</h3>
          <p className="text-xs text-gray-400 mb-4">{summaryFile.original_name}</p>
          <div className="bg-gray-50 rounded-lg p-4 text-left text-sm text-gray-700 leading-relaxed mb-6 max-h-60 overflow-y-auto">
            {summaryFile.summary || 'No summary available.'}
          </div>
          <button 
            onClick={() => setSummaryFile(null)} 
            className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium shadow-sm transition duration-200 active:scale-95 cursor-pointer"
          >
            {"Close"}
          </button>
        </div>
      </div>
    )}

    {sharingFile && (
      <div className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-xl shadow-lg text-center max-w-md w-full mx-4">
          <div className="text-emerald-500 text-4xl mb-3">🔗</div>
          <h3 className="text-lg font-bold text-gray-800 mb-1">{"Share File"}</h3>
          <p className="text-xs text-gray-400 mb-4">{sharingFile.original_name}</p>
          
          <div className="mb-4">
            <div className="flex items-center bg-gray-50 border border-gray-200 rounded-lg overflow-hidden p-1">
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/share/${sharingFile.share_token}`}
                className="w-full bg-transparent px-3 py-1.5 text-xs text-gray-600 focus:outline-none"
              />
              <button
                onClick={handleCopyLink}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-md text-xs font-semibold transition active:scale-95 whitespace-nowrap cursor-pointer"
              >
                {copied ? 'Copied!' : 'Copy Link'}
              </button>
            </div>
            <p className="text-amber-500 text-[11px] mt-2 font-medium">
              {"⏳ Automatically expires in 24 hours"}
            </p>
          </div>

          <div className="flex flex-col space-y-2 mt-6">
            <button
              onClick={handleUnshare}
              className="w-full py-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-bold transition duration-200 active:scale-95 cursor-pointer"
            >
              {"Unshare File (Make Private)"}
            </button>
            <button 
              onClick={() => setSharingFile(null)} 
              className="w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-bold transition duration-200 active:scale-95 cursor-pointer"
            >
              {"Close"}
            </button>
          </div>
        </div>
      </div>
    )}
    </div>
  );
}

export default FileList;
