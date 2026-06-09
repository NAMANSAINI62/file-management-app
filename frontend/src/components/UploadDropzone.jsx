import { useState, useRef } from 'react';
import { uploadFiles } from '../services/api';

// Allowed file extensions ki list (frontend validation ke liye)
const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt'];

function UploadDropzone({ onUploadSuccess }) {
  // files: user ne jo files select ki hain unki list
  // errors: agar koi file reject hui toh uska message
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);
  const inputRef = useRef(null); // hidden file input ko control karne ke liye

  // File extension check karne ka function
  const isAllowedFile = (filename) => {
    const ext = '.' + filename.split('.').pop().toLowerCase(); // e.g. "resume.pdf" => ".pdf"
    return ALLOWED_EXTENSIONS.includes(ext);
  };

  // Files ko validate karke state mein add karna
  const validateAndAdd = (fileList) => {
    const selectedFiles = Array.from(fileList || []);
    const validFiles = [];
    const newErrors = [];

    selectedFiles.forEach((f) => {
      if (isAllowedFile(f.name)) {
        validFiles.push(f); // Allowed hai toh add karo
      } else {
        newErrors.push(`"${f.name}" rejected — sirf PNG, JPG, PDF, Word, TXT allowed hain.`);
      }
    });

    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
    }
    if (newErrors.length > 0) {
      setErrors((prev) => [...prev, ...newErrors]);
    }
  };

  // Jab user file drag karke drop kare
  const handleDrop = (e) => {
    e.preventDefault(); // Browser ka default behavior rokna (file open hone se)
    validateAndAdd(e.dataTransfer.files); // Drop ki gayi files ko validate karo
  };

  // Jab user "Choose files" button se files select kare
  const handleFileChange = (e) => {
    validateAndAdd(e.target.files);
    e.target.value = null; // Same file dobara select kar sake isliye reset kiya
  };

  // Kisi ek file ko list se hatana
  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx)); // Use _ when we don't need the first parameter of the callback function.
  };

  // Backend par files bhejne ka function
  const handleUpload = async () => {
    if (files.length === 0) {
      setErrors((prev) => {
        if (prev.includes('No files to upload')) {
          return prev;
        }
        return [...prev, 'No files to upload'];
      });
      return;
    }

    // FormData = ek special package jisme files pack hoti hain backend ke liye
    const form = new FormData();
    files.forEach((f) => {
      form.append('files', f); // Har file ko package mein daalo
    });

    try { 
      const data = await uploadFiles(form); // api.js ke through backend ko bhejo

      if (data.errors && data.errors.length > 0) {
        setErrors((prev) => [...prev, ...data.errors]);
      }
      if (data.saved && data.saved.length > 0) {
        setFiles([]); // Upload ke baad selected list clear karo

        // Dashboard ko batao ki refresh kare file list
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      }
    } catch (err) {
      setErrors((prev) => [...prev, 'Upload failed']);
      console.error(err);
    }
  };

  return (
    <div>
      {/* Drag & Drop Area */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="min-h-25 flex flex-col items-center justify-center gap-6 rounded-2xl border-2 border-dashed border-slate-500 bg-white p-6"
      >
        <p className="text-slate-600">{"Drag & drop files here"}</p>
        <p className="text-sm text-slate-400">{"Allowed: png, jpg, pdf, doc, docx, txt."}</p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => inputRef.current?.click()}
            className="rounded-md bg-blue-600 px-3 py-1 text-white active:scale-95 cursor:pointer"
          > 
            {"Choose files"}
          </button>
          <input
            ref={inputRef}
            type="file"
            multiple
            onChange={handleFileChange}
            className="hidden"
            accept=".png,.jpg,.jpeg,.pdf,.doc,.docx,.txt"
          />
        </div>
      </div>

      <div className="mt-4">
        {/* Error messages display */}
        {errors.length > 0 && (
          <div className="mb-3 rounded-md bg-red-50 p-2 text-sm text-red-700">
            {errors.map((err, i) => (
              <div key={i}>{err}</div>
            ))}
          </div>
        )}

        {/* Selected files ki list */}
        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between rounded-md bg-slate-50 p-2">
                <div className="text-sm text-slate-700">{f.name}</div>
                <button onClick={() => removeFile(i)} className="text-sm text-white bg-red-600 rounded-md px-2 py-1">{"Remove"}</button>
              </div>
            ))}
          </div>
        )}

        {/* Upload aur Clear buttons */}
        <div className="mt-4 flex gap-2">
          <button 
            onClick={handleUpload} 
            disabled={files.length === 0}
            className={`rounded-md px-3 py-1 text-white transition-all ${
              files.length === 0 
                ? 'bg-green-400 opacity-50 cursor-not-allowed' 
                : 'bg-green-600 active:scale-95 cursor-pointer'
            }`}
          >
            {"Upload"}
          </button>
          <button
            onClick={() => { setFiles([]); setErrors([]); }}
            className="rounded-md bg-gray-200 px-3 py-1 active:scale-95">
            {"Clear"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadDropzone;