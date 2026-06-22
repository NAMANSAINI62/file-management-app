import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Helper: JWT token ko localStorage se read karo aur Authorization header banao
function authHeader() {
  const token = localStorage.getItem('authToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// File upload
export async function uploadFiles(payload) {
  let form;
  if (payload instanceof FormData) {
    form = payload;
  } else if (Array.isArray(payload)) {
    form = new FormData();
    payload.forEach((f) => form.append('files', f));
  } else {
    throw new Error('uploadFiles expects FormData or File[]');
  }

  const resp = await axios.post(`${API_BASE}/api/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data', ...authHeader() },
  });
  return resp.data;
}

// Signup
export async function signupUser(email, password, name) {
  const resp = await axios.post(`${API_BASE}/api/signup`, { email, password, name });
  return resp.data;
}

// Login — returns { token, id, email, name }
export async function loginUser(email, password) {
  const resp = await axios.post(`${API_BASE}/api/login`, { email, password });
  return resp.data;
}

// Logout
export async function logoutUser() {
  const resp = await axios.post(`${API_BASE}/api/logout`, {}, {
    headers: authHeader(),
  });
  return resp.data;
}

// Get current user (verify token with backend)
export async function getCurrentUser() {
  const resp = await axios.get(`${API_BASE}/api/me`, {
    headers: authHeader(),
  });
  return resp.data;
}

// Fetch user files
export async function getFiles() {
  const resp = await axios.get(`${API_BASE}/api/files`, {
    headers: authHeader(),
  });
  return resp.data;
}

// Delete a file
export async function deleteFile(fileId) {
  const resp = await axios.delete(`${API_BASE}/api/files/${fileId}`, {
    headers: authHeader(),
  }); 
  return resp.data;
}

// app.py: Saara main logic, rules, database, aur brain yahan hota hai.
// api.js: Iska kaam bas un routes (/api/login, /api/upload) ko call lagana hai aur wahan se data laakar React components ko dena hai.
// authHeader(): Har protected request ke saath JWT token Authorization header mein bhejta hai.