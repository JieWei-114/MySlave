# 🧠 MySlave – Local AI Chat System

A fully local, end-to-end chat application built with **Angular + FastAPI + MongoDB**, supporting:

- 💬 Multi-session chat
- ⚡ Real-time SSE streaming
- 🧠 Memory system (remember / forget)
- 📜 Pagination & lazy loading
- 🔒 Fully local (no data leaves your machine)

## 🏗 Project Structure
MySlave/
├─ frontend/ # Angular app
├─ backend/ # FastAPI backend
└─ README.md

## 🚀 Tech Stack

### Frontend
- Angular (standalone components)
- Signals-based state management
- SSE (Server-Sent Events)
- Lazy loading & pagination

### Backend
- FastAPI
- MongoDB
- SSE streaming API
- Ollama (local LLM, e.g. qwen2.5)

## 🧠 Key Features

### 1️⃣ Local-first
- No cloud
- No external API calls
- All chats stored in local MongoDB

### 2️⃣ Streaming Chat
- Token-by-token streaming via SSE
- Stop button to interrupt generation

### 3️⃣ Memory System (WIP)
- Mark messages as “remember”
- Only remembered + recent messages are sent to the model
- Manual memory management

### 4️⃣ Pagination & Lazy Load
- Load latest messages on open
- Scroll up to load older messages

## 🛠 Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB (local)
- Ollama

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
Backend runs at: http://localhost:8000

Frontend
bash
Copy code
cd frontend
npm install
ng serve
Frontend runs at: http://localhost:4200

🔐 Privacy
This project is 100% local:

No prompts are uploaded

No telemetry

No tracking

Your data stays on your machine.

📌 Roadmap
 Multi-session chat

 SSE streaming

 Pagination & lazy load

 Memory UI (🧠 remember toggle)

 Context window control

 Model switching

 Prompt templates