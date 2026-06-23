import { useState, useRef } from 'react';
import { uploadFiles } from '../services/api';

const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.txt'];

function UploadDropzone({ onUploadSuccess }) {
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);
  const inputRef = useRef(null);

  const isAllowedFile = (filename) => {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return ALLOWED_EXTENSIONS.includes(ext);
  };

  const validateAndAdd = (fileList) => {
    const selectedFiles = Array.from(fileList || []);
    const validFiles = [];
    const newErrors = [];

    selectedFiles.forEach((f) => {
      if (!isAllowedFile(f.name)) {
        newErrors.push(`"${f.name}" rejected — sirf PNG, JPG, PDF, Word, TXT allowed hain.`);
      } else if (f.size === 0) {
        newErrors.push(
          `"${f.name}" khali hai (0 bytes). Pehle Notepad mein Ctrl+S se save karo, phir "Choose files" se upload karo — drag & drop mat use karo.`
        );
      } else {
        validFiles.push(f);
      }
    });

    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
    }
    if (newErrors.length > 0) {
      setErrors((prev) => [...prev, ...newErrors]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    validateAndAdd(e.dataTransfer.files);
  };

  const handleFileChange = (e) => {
    validateAndAdd(e.target.files);
    e.target.value = null;
  };

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

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

    const form = new FormData();
    files.forEach((f) => {
      form.append('files', f);
    });

    try {
      const data = await uploadFiles(form);

      if (data.errors && data.errors.length > 0) {
        setErrors((prev) => [...prev, ...data.errors]);
      }
      if (data.saved && data.saved.length > 0) {
        setFiles([]);
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
        {errors.length > 0 && (
          <div className="mb-3 rounded-md bg-red-50 p-2 text-sm text-red-700">
            {errors.map((err, i) => (
              <div key={i}>{err}</div>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between rounded-md bg-slate-50 p-2">
                <div className="text-sm text-slate-700">
                  {f.name}
                  <span className="ml-2 text-slate-400">
                    ({f.size < 1024 ? `${f.size} Bytes` : `${(f.size / 1024).toFixed(2)} KB`})
                  </span>
                </div>
                <button onClick={() => removeFile(i)} className="text-sm text-white bg-red-600 rounded-md px-2 py-1">{"Remove"}</button>
              </div>
            ))}
          </div>
        )}

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