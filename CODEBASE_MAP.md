# Codebase Architecture Map

This map outlines the folder structure, PostgreSQL schemas, API endpoints, and component hierarchy to help the AI assistant understand the codebase immediately without scanning multiple files.

---

## 📁 Folder Structure

```
File_Management/
├── backend/
│   ├── app.py                  # Main Flask app, DB setup, AI workers
│   └── uploads/                # Stores uploaded physical files
└── frontend/
    └── src/
        ├── components/
        │   ├── FileList.jsx    # Table displaying user files, download, delete
        │   ├── ProtectedRoute.jsx # Authentication route guard
        │   └── UploadDropzone.jsx # File upload drag-and-drop zone
        ├── context/
        │   └── AuthContext.jsx # User session & login state provider
        ├── pages/
        │   ├── Dashboard.jsx   # Logged-in page displaying list + upload
        │   ├── Login.jsx       # Login view
        │   └── Signup.jsx      # Signup view
        ├── services/
        │   └── api.js          # Axios API communication helpers
        ├── App.jsx             # React route configs
        └── main.jsx            # React mounting point
```

---

## 🗄️ PostgreSQL Database Schema

### 1. `users` Table
* `id`: `SERIAL PRIMARY KEY`
* `email`: `TEXT UNIQUE NOT NULL`
* `name`: `TEXT`
* `password_hash`: `TEXT NOT NULL`
* `created_at`: `TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`

### 2. `files` Table
* `id`: `SERIAL PRIMARY KEY`
* `user_id`: `INTEGER NOT NULL (FK -> users.id)`
* `original_name`: `TEXT NOT NULL`
* `stored_name`: `TEXT NOT NULL`
* `file_size`: `INTEGER NOT NULL`
* `created_at`: `TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`
* `summary`: `TEXT`
* `category`: `VARCHAR(50)`

---

## 🔌 API Endpoints (Flask backend on port 5000)

| Endpoint | Method | Authentication | Payload / Parameters | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/api/signup` | `POST` | None | `{email, password, name}` | Register a new user |
| `/api/login` | `POST` | None | `{email, password}` | Login and start session (Cookie-based) |
| `/api/logout` | `POST` | Session | None | End active user session |
| `/api/me` | `GET` | Session | None | Fetch logged-in user profile details |
| `/api/upload` | `POST` | Session | `Multipart FormData` (`file` or `files`) | Upload files and trigger async AI summaries |
| `/api/files` | `GET` | Session | None | List files uploaded by the logged-in user |
| `/api/files/<id>/download` | `GET` | None | `file_id` (URL path) | Direct file download as attachment |
| `/api/files/<id>` | `DELETE` | Session | `file_id` (URL path) | Delete file metadata and physical storage file |

---

## 🤖 AI Summary Processing Pipeline
* **Trigger**: Triggers on successful `/api/upload` in a background thread.
* **API Target**: Groq API (`llama-3.1-8b-instant` with fallback to `llama-3.3-70b-versatile` under a 2.0-second join timeout).
* **Fallback**: High-performance local text processor (or lightweight Hugging Face pipeline `sshleifer/distilbart-cnn-6-6` if transformers installed) if API times out or fails.
* **Output**: Updates the `summary` column in the database.
