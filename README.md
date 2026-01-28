# MySlave – Local AI Chat System

A fully local, privacy-first chat application that puts your data in your hands. Built with **Angular + FastAPI + MongoDB**, combining modern frontend architecture with a powerful, scalable backend.

## Overview

MySlave is a multi-session AI chat platform designed for users who value privacy and control. Chat with multiple AI models running locally via Ollama, access optional web search capabilities, and manage conversation memory—all without any data leaving your machine.

### Key Capabilities

- **Multi-session chat** with persistent sidebar navigation
- **Real-time streaming** responses with stop-mid-generation functionality
- **Multi-model support**: Switch between Gemma, Llama, Qwen, Phi, and custom models
- **Memory system**: Mark important messages for context-aware follow-ups
- **Web search integration**: Optional search via Serper, Tavily, or local SearXNG with quota tracking
- **Infinite scroll & lazy loading** for smooth conversation browsing
- **Modern, responsive UI** with design system and smooth animations
- **100% local execution**: No external services, no telemetry, no data uploads

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

- **Multi-session management** with persistent sidebar
- **Real-time streaming responses** with token-by-token display
- **Stop generation mid-stream** to halt long responses
- **Message history** with infinite scroll and lazy loading
- **Session controls**: Rename, delete, and organize conversations
- **Markdown rendering** for formatted responses

### Memory System

- **Memory panel** - Review and manage remembered messages
- **Drag-to-resize** interface for flexible layout
- **Mark messages as memorable** for future context
- **Context-aware prompts** - Retrieved memories inform AI responses
- **Visual connections** between sidebar and memory panel

### Web Search (Optional)

- **Smart provider routing**: Use Serper, Tavily, or local SearXNG
- **Explicit search commands**: Control when search is triggered
- **Keyword-based routing**: Automatic provider selection
- **Provider fallbacks**: Seamlessly switch between services
- **Quota tracking**: Monitor usage limits for paid services
- **Local-first option**: SearXNG for privacy-focused search

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
ollama pull neural-chat:7b
ollama pull phi:latest

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Optional: Local Web Search (SearXNG)

```bash
cd searxng

# Edit settings.yml and set a strong secret
# server.secret_key: "your-32-character-random-string"

docker compose up -d
docker compose logs -f
```

**SearXNG URL**: http://localhost:8080

## Configuration

## Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# MongoDB
MONGO_URI=mongodb://127.0.0.1:27017
DB_NAME=myslave

# Ollama
OLLAMA_URL=http://localhost:11434

# CORS
CORS_ORIGINS=["http://localhost:4200"]

# Optional: Web Search API Keys
SERPER_API_KEY=your_serper_key_here
TAVILY_API_KEY=your_tavily_key_here
SEARXNG_URL=http://localhost:8080

# Quotas
SERPER_TOTAL_LIMIT=2500
TAVILY_MONTHLY_LIMIT=1000
```

Or edit [backend/app/config/settings.py](backend/app/config/settings.py) directly.

### Add Custom AI Models

Edit [backend/app/config/ai_models.py](backend/app/config/ai_models.py):

```python
AVAILABLE_MODELS = [
    {
        "id": "gemma:7b",
        "name": "Gemma 7B",
        "description": "Google's lightweight model",
        "size": "7B"
    },
    {
        "id": "llama2:7b",
        "name": "Llama 2 7B",
        "description": "Meta's general-purpose model",
        "size": "7B"
    },
    # Add your custom models here
]
```

### Web Search Configuration

Set API keys for optional web search providers:

**Serper** (Google Search)

- Get key at: https://serper.dev
- Set `SERPER_API_KEY` in `.env`
- Default quota: 2500 requests/month

**Tavily** (Real-time search)

- Get key at: https://tavily.com
- Set `TAVILY_API_KEY` in `.env`
- Default quota: 1000 requests/month

**SearXNG** (Self-hosted, no keys needed)

- Run locally with Docker Compose
- Set `SEARXNG_URL=http://localhost:8080`
- Fallback when other providers are unavailable

## 🛠️ Development & Code Quality

### Frontend

**Prettier** - Code formatting

```bash
cd frontend

# Check formatting
npm run format:check

# Auto-fix formatting
npm run format:fix
```

### Backend

**Ruff** - Linting and formatting

```bash
cd backend

# Lint and sort imports
ruff check --fix .

# Format code
ruff format .
```

Settings configured in [backend/pyproject.toml](backend/pyproject.toml).

## Privacy & Security

**MySlave is 100% local by design:**

- No cloud services
- No external API calls (except optional web search)
- No telemetry or tracking
- No data uploads
- All data stored locally in MongoDB
- No third-party analytics
- Full encryption-ready with MongoDB

**Data Storage**:

- Chat history: Local MongoDB
- Session data: Local MongoDB
- Memory markers: Local MongoDB
- User preferences: Browser local storage
- Web search quotas: Local MongoDB

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

## API Documentation

**Interactive Swagger UI**:  
http://127.0.0.1:8000/docs

**Main Endpoints**:

- `POST /api/chat/message` - Send message and get streaming response
- `GET /api/chat/sessions` - List all chat sessions
- `POST /api/chat/sessions` - Create new session
- `DELETE /api/chat/sessions/{id}` - Delete session
- `GET /api/memory` - Get session memories
- `POST /api/memory` - Mark message as memorable
- `GET /api/search` - Perform web search

See Swagger docs for full endpoint details and request/response schemas.

## Project Structure

```
MySlave/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   ├── services/          # Business logic
│   │   ├── models/            # Data models & DTOs
│   │   ├── config/            # Settings & configuration
│   │   └── core/              # Database & utilities
│   ├── requirements.txt        # Python dependencies
│   └── pyproject.toml         # Project configuration
│
├── frontend/                   # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── features/      # Feature modules (chat, memory, tools)
│   │   │   ├── shared/        # Shared components & pipes
│   │   │   ├── core/          # Guards, interceptors, services
│   │   │   └── shell/         # App shell/layout
│   │   └── styles.css         # Global styles & variables
│   ├── angular.json           # Angular build config
│   └── package.json           # NPM dependencies
│
├── searxng/                    # Optional local search setup
│   ├── docker-compose.yml
│   └── settings.yml
│
└── README.md                   # This file
```

## Roadmap & Future Features

- [ ] User authentication & multi-user support
- [ ] Export conversations (PDF, Markdown)
- [ ] Conversation search & filtering
- [ ] Custom system prompts per session
- [ ] Voice input/output
- [ ] Plugin system for custom tools
- [ ] RAG (Retrieval Augmented Generation) integration
- [ ] Model fine-tuning interface

## Contributing

Contributions are welcome! Areas for improvement:

- Performance optimizations
- Additional web search providers
- UI/UX enhancements
- Documentation improvements
- Bug fixes and edge cases
- Test coverage expansion

Please ensure code follows the style guide (Prettier/Ruff) before submitting.

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
A: Minimum 8GB recommended. Model size varies:

- 7B models: ~6-8GB
- 13B models: ~10-12GB
- Running multiple services: 16GB+ recommended

**Q: Can I use cloud-hosted models instead of Ollama?**  
A: Currently no, but it's planned for a future version to support OpenAI API-compatible endpoints.

**Q: How do I backup my conversations?**  
A: All data is in MongoDB. Backup your MongoDB data directory or use `mongodump`/`mongorestore`.

**Q: Can I deploy this to a server?**  
A: Yes, but ensure security (authentication, HTTPS, firewalls). See backend configuration for CORS and security settings.