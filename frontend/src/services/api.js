import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'; // lets you read .env file variable inside your JavaScript/React code and check if VITE_API_URL
// is set in the .env file. If yes, use it. If not, use localhost:5000 as default.

// Original file upload function
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
    withCredentials: true,
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return resp.data;
}

// Direct axios helper for Signup
export async function signupUser(email, password, name) {
  const resp = await axios.post(`${API_BASE}/api/signup`, { email, password, name }, {
    withCredentials: true,
  });
  return resp.data;
}

// Direct axios helper for Login
export async function loginUser(email, password) {
  const resp = await axios.post(`${API_BASE}/api/login`, { email, password }, {
    withCredentials: true,
  });
  return resp.data;
}

// Direct axios helper for Logout
export async function logoutUser() {
  const resp = await axios.post(`${API_BASE}/api/logout`, {}, {
    withCredentials: true,
  });
  return resp.data;
}

// Direct axios helper for Checking session
export async function getCurrentUser() {
  const resp = await axios.get(`${API_BASE}/api/me`, {
    withCredentials: true,
  });
  return resp.data;
}

// Direct axios helper for fetching user files
export async function getFiles() {
  const resp = await axios.get(`${API_BASE}/api/files`, {
    withCredentials: true,  // browser se session cookie request saath jaaye jisse flask ko pta chle ki konsa user logged in hai.
  });
  return resp.data;
}

// Direct axios helper for deleting a file
export async function deleteFile(fileId) {
  const resp = await axios.delete(`${API_BASE}/api/files/${fileId}`, {
    withCredentials: true,
  });
  return resp.data;
}

// app.py: Saara main logic, rules, database, aur brain yahan hota hai.
// api.js: Iska kaam bas un routes (/api/login, /api/upload) ko call lagana hai aur wahan se data laakar React components ko dena hai.
// with credentials true acts as a bridge for sending sensitive data across different network addresses.
// Cross-Origin Permission: It allows the browser to send cookies/session data between different addresses this helps browser to identify who is making request.