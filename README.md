# MySlave – Local AI Assistant Platform

A fully local, privacy-first AI assistant with advanced conversation management, persistent memory, custom rules, and intelligent web search. Built with **Angular 21 + FastAPI + MongoDB**, combining modern frontend architecture with a powerful, production-ready backend.

## Overview

MySlave is a comprehensive AI assistant platform designed for users who demand privacy, control, and customization. Chat with multiple local AI models via Ollama, define custom behavioral rules, maintain conversation memory, and optionally search the web—all while keeping your data completely local.

### Key Features

- **Multi-Model Chat** – Switch between Gemma, Llama, Qwen, Phi, and custom models
- ** Memory System** – Mark and retrieve important messages for context-aware conversations
- **Custom Rules** – Define system prompts and behavioral guidelines for AI responses
- **Web Search** – Integrated search via Serper, Tavily, DuckDuckGo, or local SearXNG
- **File Upload** – Extract and analyze content from documents (PDFs, DOCX, TXT, etc.)
- **Real-Time Streaming** – Token-by-token responses with stop-mid-generation control
- **Modern UI** – Clean, responsive interface with design system and smooth animations
- **100% Local** – No external services, no telemetry, complete data privacy

## Tech Stack

### Frontend

- **Framework**: Angular 21.1.0 (standalone components)
- **State Management**: Angular Signals with computed properties
- **Styling**: CSS Variables with design system
- **Real-time Communication**: Server-Sent Events (SSE)
- **Code Quality**: Prettier for formatting

### Backend

- **Framework**: FastAPI 0.128.0
- **Database**: MongoDB 4.16+ with connection pooling
- **LLM Integration**: Ollama (local models)
- **Streaming**: SSE for real-time responses
- **Config Management**: Pydantic Settings with .env support
- **Code Quality**: Ruff for linting and formatting

### Infrastructure

- **Node.js**: v20.19+ or v22.12+
- **Python**: 3.10+
- **MongoDB**: 4.6+ (local, Docker, or cloud)
- **Docker**: Optional for SearXNG and MongoDB

## Features

### Multi-Model Support

- Switch between AI models on the fly
- Models loaded from backend API with intelligent fallback
- Add new models by editing backend configuration
- Stream responses in real-time with generation control

### Modern UI/UX

- **Design System**: CSS variables for consistent theming (colors, spacing, shadows)
- **Smart Components**: Skeleton loaders, error boundaries, empty states
- **Smooth Animations**: Transitions, typing indicators, scroll effects
- **Responsive Layout**: Works seamlessly on desktop and tablet screens
- **Accessibility**: Semantic HTML and keyboard navigation

### Chat Features

- **Multi-session management** with persistent sidebar navigation
- **Real-time streaming** with token-by-token display
- **Stop generation mid-stream** to halt long responses
- **Message history** with infinite scroll and lazy loading
- **Session controls**: Rename, delete, and organize conversations
- **Markdown rendering** with syntax highlighting
- **File attachments**: Upload and analyze documents in conversations

### Memory System

- **Persistent memory panel** with drag-to-resize interface
- **Mark messages as memorable** for future context retrieval
- **Smart memory retrieval** using embeddings for semantic search
- **Context-aware AI responses** informed by retrieved memories
- **Memory management UI** to review and delete stored memories
- **Per-session memory isolation** for organized context

### Rules System

- **Custom system prompts** to define AI behavior and personality
- **Pre-configured rule templates** for common use cases
- **Multiple rules per session** with priority management
- **Rule library** to save and reuse across conversations
- **Dynamic rule injection** into AI context
- **Visual rule management UI** with create/edit/delete operations

### Web Search (Optional)

- **Multiple search providers**: Serper, Tavily, DuckDuckGo, SearXNG
- **Smart provider routing** based on keywords and availability
- **Quota tracking and management** for paid services
- **Automatic fallback** to local SearXNG when limits reached
- **Search result extraction** with context formatting
- **Integrated search UI** with provider selection

### Advanced Features

- **Connection Pooling**: Optimized MongoDB connections for performance
- **Professional Error Handling**: User-friendly error display with retry options
- **Computed Signals**: Fine-grained reactivity with minimal rerenders
- **SSR Compatible**: Server-side rendering support with browser API guards
- **Environment Configuration**: .env support for easy deployment
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

### Prerequisites

- **Node.js**: v20.19+ or v22.12+
- **Python**: 3.10+
- **MongoDB**: 4.6+ (local, Docker, or cloud)
- **Ollama**: For local LLM inference ([Download](https://ollama.ai))
- **Git**: For cloning the repository (optional)

### Setup

### Backend Setup

```bash
cd backend

# Clean up (optional but recommended)
rm -rf venv
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Start development server
python -m uvicorn app.main:app --reload
```

**Backend URL**: http://127.0.0.1:8000  
**API Docs**: http://127.0.0.1:8000/docs

### Database Setup

Choose one option:

**Option 1: MongoDB Service (Windows)**

```powershell
Get-Service | ? Name -like 'MongoDB*'
Start-Service MongoDB
```

**Option 2: Manual Start (Windows)**

```bash
mkdir C:\data\db
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
```

**Option 3: Docker**

```bash
docker run -d --name mongo -p 27017:27017 -v C:\data\db:/data/db mongo:7
```

**Collections Created Automatically**:

- `sessions`: Chat session metadata
- `memories`: Stored memories per session
- `serper_quota`: Serper API usage counter
- `tavily_quota`: Tavily API monthly usage counter

### Frontend Setup

```bash
cd frontend

# Clean up (optional but recommended)
rm -rf node_modules .angular package-lock.json
npm cache clean --force

# Install dependencies
npm install # --verbose /to see logs

# Start development server
npx ng serve
```

**Frontend URL**: http://localhost:4200

### Ollama Setup

```bash
# Install from https://ollama.ai

# Pull desired models
ollama pull gemma:7b
ollama pull llama2:7b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Optional: Local Web Search (SearXNG)

```bash
cd searxng

# Edit settings.yml and set a strong secret
# server.secret_key: "your-32-character-random-string"
docker --version

docker info
docker compose up -d
docker ps
docker compose logs -f
```

**SearXNG URL**: http://localhost:8080

## Configuration Guide

### Backend Environment Variables

Create `.env` in `backend/` directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://127.0.0.1:27017
DB_NAME=myslave

# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# CORS Settings
CORS_ORIGINS=["http://localhost:4200","http://127.0.0.1:4200"]

# Web Search API Keys (Optional)
SERPER_API_KEY=your_serper_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
SEARXNG_URL=http://localhost:8080

# Search Quotas
SERPER_TOTAL_LIMIT=2500
TAVILY_MONTHLY_LIMIT=1000
```

### Customizing AI Models

Edit [backend/app/config/ai_models.py](backend/app/config/ai_models.py):

```python
AVAILABLE_MODELS = [
    {
        "id": "gemma:7b",
        "name": "Gemma 7B",
        "description": "Google's efficient language model",
        "size": "7B",
        "context_length": 8192
    },
    {
        "id": "llama2:13b",
        "name": "Llama 2 13B",
        "description": "Meta's powerful open model",
        "size": "13B",
        "context_length": 4096
    },
    # Add your custom models here
]
```

### Adding Web Search Providers

Create new provider in [backend/app/config/web_providers/](backend/app/config/web_providers/):

```python
from .base import WebSearchProvider

class CustomProvider(WebSearchProvider):
    async def search(self, query: str) -> dict:
        # Implement your search logic
        pass
```

Register in [backend/app/services/web_search_service.py](backend/app/services/web_search_service.py).

## Development

### Frontend Development

**Run Development Server**

```bash
cd frontend
npx ng serve
# Access at http://localhost:4200
```

**Build for Production**

```bash
npm run build
# Output in frontend/dist/
```

**Code Quality**

```bash
# Format code with Prettier
npm run format:check  # Check formatting
npm run format:fix    # Auto-fix formatting

# Lint code
npx ng lint
```

**Testing**

```bash
npm test              # Run unit tests
npm run test:coverage # Generate coverage report
```

### Backend Development

**Run Development Server**

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m uvicorn app.main:app --reload
# Access at http://127.0.0.1:8000
```

**Code Quality**

```bash
# Lint with Ruff
ruff check --fix .

# Format code
ruff format .

# Run all checks
ruff check . && ruff format .
```

**Testing**

```bash
pytest                    # Run all tests
pytest --cov=app         # With coverage
pytest -v tests/         # Verbose output
```

## Privacy & Security

**MySlave is 100% local by design:**

- No cloud services or external dependencies (except optional web search)
- No telemetry, tracking, or analytics
- No data uploads to third-party servers
- All conversations stored locally in MongoDB
- Ollama models run entirely on your machine
- Full control over your data and AI interactions

**Optional External Services:**

- Web search providers (Serper, Tavily) – Only when explicitly used
- SearXNG & DuckDuckGo– Self-hosted, fully local alternative

**Security Best Practices:**

- Use HTTPS with reverse proxy (nginx, Caddy)
- Configure firewall rules if exposing to network
- Set strong `secret_key` for SearXNG

## Troubleshooting

### Models Not Loading

```bash
# Check backend health
curl http://127.0.0.1:8000/health

# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull a model
ollama pull gemma:7b

# Restart backend
python -m uvicorn app.main:app --reload
```

### Frontend Won't Connect

- Verify backend is running on port 8000
- Check browser console for errors (F12)
- Clear browser cache and reload (Ctrl+Shift+R)
- Ensure CORS_ORIGINS includes `http://localhost:4200`

### Database Connection Issues

```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Verify connection string in settings
# Default: mongodb://127.0.0.1:27017

# Create database (auto-created on first run)
mongosh myslave
```

### Memory Issues

- Start with smaller models (7B parameters)
- Increase system RAM if running multiple services
- Monitor with Task Manager or `top` command
- Consider using quantized model variants

### Web Search Not Working

- Verify API keys are set correctly
- Check SearXNG is running if using local search
- Review quotas in MongoDB: `serper_quota`, `tavily_quota`
- Check backend logs for API errors

### File Upload Issues

- Verify file extraction service is configured
- Check supported formats: PDF, DOCX, TXT, MD, CSV
- Review file size limits in backend configuration

## Additional Resources

- **Interactive API Docs**: http://127.0.0.1:8000/docs (Swagger UI)
- **Alternative API Docs**: http://127.0.0.1:8000/redoc (ReDoc)

## Acknowledgments

Built with incredible open-source projects:

- [Ollama](https://ollama.ai) – Local LLM inference engine
- [Angular](https://angular.dev) – Modern web framework
- [FastAPI](https://fastapi.tiangolo.com) – High-performance Python framework
- [MongoDB](https://www.mongodb.com) – Flexible document database
- [SearXNG](https://docs.searxng.org) – Privacy-respecting metasearch engine

## FAQ

**Q: Will my conversations be sent to external servers?**  
A: No. MySlave is 100% local. Optional web search is the only external component, and you can disable it or use the local SearXNG version.

**Q: How much RAM do I need?**  
A: Minimum 8GB recommended. Model memory usage varies:

- 7B models: ~6-8GB RAM
- 13B models: ~10-12GB RAM
- 33B+ models: 20GB+ RAM
- Multiple services running: 16GB+ recommended

**Q: Can I use different AI models?**  
A: Yes! Any Ollama-compatible model works. Pull models with `ollama pull <model>` and add them to [backend/app/config/ai_models.py](backend/app/config/ai_models.py).

**Q: How do I backup my conversations?**  
A: Use MongoDB backup tools:

```bash
mongodump --db myslave --out backup/
mongorestore --db myslave backup/myslave/
```

**Q: Can I deploy this to a server?**  
A: Yes, but ensure proper security:

- Enable authentication
- Use HTTPS (reverse proxy with nginx/Caddy)
- Configure firewall rules
- Set strong MongoDB passwords
- Update CORS settings in backend

**Q: Does this work offline?**  
A: Yes! Everything except web search works completely offline. For offline search, use SearXNG.

---