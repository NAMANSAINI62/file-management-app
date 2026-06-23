import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function authHeader() {
  const token = localStorage.getItem('authToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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
    headers: { ...authHeader() },
  });
  return resp.data;
}

export async function signupUser(email, password, name) {
  const resp = await axios.post(`${API_BASE}/api/signup`, { email, password, name });
  return resp.data;
}

export async function loginUser(email, password) {
  const resp = await axios.post(`${API_BASE}/api/login`, { email, password });
  return resp.data;
}

export async function logoutUser() {
  const resp = await axios.post(`${API_BASE}/api/logout`, {}, {
    headers: authHeader(),
  });
  return resp.data;
}

export async function getCurrentUser() {
  const resp = await axios.get(`${API_BASE}/api/me`, {
    headers: authHeader(),
  });
  return resp.data;
}

export async function getFiles() {
  const resp = await axios.get(`${API_BASE}/api/files`, {
    headers: authHeader(),
  });
  return resp.data;
}

export async function deleteFile(fileId) {
  const resp = await axios.delete(`${API_BASE}/api/files/${fileId}`, {
    headers: authHeader(),
  });
  return resp.data;
}