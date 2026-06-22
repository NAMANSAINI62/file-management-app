# 🚀 AI-Powered File Management System

A modern, full-stack web application that allows users to securely upload, manage, and analyze their files. It features an integrated AI assistant that automatically reads uploaded documents (like PDFs and Text files) and generates concise summaries instantly.

## ✨ Features

- **🔐 Secure Authentication:** User signup and login system with encrypted password hashing.
- **📁 Smart File Upload:** Drag-and-drop file uploading with strict extension and MIME-type validation.
- **🤖 Automated AI Summarization:** Uses blazing-fast Groq API (Llama 3 models) to read documents and generate smart summaries automatically.
- **⚡ Real-time Polling:** Dashboard automatically updates when the AI summary is ready without needing a page refresh.
- **📄 Summary Modal:** Click on the "Summary" button to read the full AI-generated summary of your documents in a clean pop-up modal.
- **⬇️ Download & Manage:** Easily download original files or delete them with confirmation modals.

---

## 📸 Screenshots

*Note: Add your screenshots to the `screenshots` folder in the root directory.*

### 1. Login Page
![Login Page](./screenshots/login.png)

### 2. Signup Page
![Signup Page](./screenshots/signup.png)

### 3. User Dashboard
![User Dashboard](./screenshots/dashboard.png)

### 4. Uploading a File
![Upload Dropzone](./screenshots/upload.png)

### 5. AI Summary Modal
![AI Summary Modal](./screenshots/summary-modal.png)

---

## 🛠️ Technology Stack

**Frontend:**
- React.js (Vite)
- Tailwind CSS (for modern UI styling)
- React Router (for navigation)
- Axios (for API requests)

**Backend:**
- Python 3
- Flask (Web Framework)
- PostgreSQL (Database for storing users and file metadata)
- Groq API (`llama-3.1-8b-instant` & `llama-3.3-70b-versatile` for AI summarization)
- PyPDF (for extracting text from PDFs)

---

## 🚀 How to Run the Project Locally

### Prerequisites
- Node.js installed
- Python 3.x installed
- PostgreSQL installed and running

### 1. Database Setup
Ensure PostgreSQL is running. The backend automatically creates the required tables (`users` and `files`) on startup, but you need to make sure the database exists. By default, it looks for a database named `file_management` with user `postgres` and password `root`. 

### 2. Backend Setup
Navigate to the backend directory:
```bash
cd backend
```
Install the required dependencies:
```bash
pip install -r requirements.txt
```
Create a `.env` file in the `backend` directory and add your Groq API key:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=file_management
DB_USER=postgres
DB_PASS=root
GROQ_API_KEY=your_api_key_here
```
Run the Flask server:
```bash
python app.py
```
*The server will run on http://localhost:5000*

### 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```
Install dependencies:
```bash
npm install
```
Start the development server:
```bash
npm run dev
```
*The React app will typically run on http://localhost:5173*

---

## 🤝 Contributing
Feel free to fork the project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.
