# MySlave – Local AI Chat System (Still in progress)

A fully local, end-to-end chat application built with **Angular + FastAPI + MongoDB**, supporting:

- Multi-session chat with sidebar
- Real-time SSE streaming with stop functionality
- Multiple AI model support (Gemma, Llama, Qwen, Phi)
- Memory system panel
- Infinite scroll & lazy loading
- Modern, responsive UI
- Fully local (no data leaves your machine)

## Tech Stack

### Frontend

- **Framework**: Angular 21.1.0 (standalone components)
- **State Management**: Angular Signals
- **Styling**: CSS Variables with design system
- **Real-time**: Server-Sent Events (SSE)

### Backend

- **Framework**: FastAPI 0.128.0
- **Database**: MongoDB 4.16+ with connection pooling
- **LLM**: Ollama (local models)
- **Streaming**: SSE for real-time responses
- **Config**: Pydantic Settings with .env support

## Features

### Multi-Model Support

- Switch between AI models on the fly
- Models loaded from backend API with fallback
- Add new models by updating backend config

### Modern UI/UX

- **Design System**: CSS variables for colors, spacing, shadows
- **Components**: Skeleton loaders, error boundaries, empty states
- **Animations**: Smooth transitions, typing indicators

### Chat Features

- Multi-session management
- Real-time streaming responses
- Stop generation mid-stream
- Message history with lazy loading
- Session rename & delete

### Memory System

- Memory panel
- Drag-to-resize from left edge
- Mark messages as "remember"
- Context-aware prompts
- Visual connection to sidebar

### Advanced Features

- **Connection Pooling**: Optimized MongoDB connections
- **Error Handling**: Professional error display with retry
- **Computed Signals**: Optimized reactivity
- **SSR Compatible**: Platform checks for browser APIs

## Setup

### Prerequisites

- **Node.js**: v20.19+ or v22.12+
- **Python**: 3.10+
- **MongoDB**: 4.6+ (local or Docker)
- **Ollama**: For LLM inference

### Backend Setup with troubleshoot

```bash
cd backend

# Delete venv
rm -rf venv

# Delete cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv/Scripts/activate

# Install dependencies
python -m pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload

```

Backend runs at: **http://127.0.0.1:8000**  
API Docs: **http://127.0.0.1:8000/docs**

### Frontend Setup with troubleshoot

```bash
cd frontend

# Delete node_modules
rm -rf node_modules

# Delete Angular cache
rm -rf .angular

# Delete local file
rm -rf package-lock.json

# Clear npm cache
npm cache clean --force

# Install dependencies
npm install # --verbose "view log"

# Start development server
npx ng serve
```

Frontend runs at: **http://localhost:4200**

### Database Setup

**Option 1: MongoDB Service (Windows)**

```powershell
Get-Service | ? Name -like 'MongoDB*'
Start-Service MongoDB
```

**Option 2: Manual Start**

```bash
mkdir C:\data\db
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

**Option 3: Docker**

```bash
docker run -d --name mongo -p 27017:27017 -v C:\data\db:/data/db mongo:7
```

### Ollama Setup

```bash
# Install Ollama from https://ollama.ai

# Pull models
ollama pull <model>

```

## Configuration

### Backend Config

Edit `backend/app/config/settings.py`:

```python
MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "myslave"
OLLAMA_URL = "http://localhost:11434/api/generate"
CORS_ORIGINS = ["http://localhost:4200"]
```

### Add New Models

Edit `backend/app/config/models.py`:

```python
AVAILABLE_MODELS = [
    {"id": "model-name", "name": "Display Name", "description": "Description", "size": "7B"},
    # Add more models here
]
```

## Code Quality & Formatting Guide

```Frontend - Prettier
Check for issues: npm run format:check
Fix all files: npm run format:fix
```

```Backend - Ruff
Lint & Sort Imports: ruff check --fix .
Format Style: ruff format .

Settings are located in pyproject.toml
```

## Privacy

This project is **100% local**:

- No cloud services
- No external API calls
- No telemetry or tracking
- No data uploads
- All data stays on your machine

**Models not loading**

- Check backend is running: http://127.0.0.1:8000/health
- Check Ollama is running: http://localhost:11434
- Pull models: `ollama pull gemma3:4b`

## Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM inference
- [Angular](https://angular.dev) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [MongoDB](https://www.mongodb.com) - Database

## App screenshot

![App screenshot](/frontend/src/assets/images/app_screenshot.png)
