# MySlave – Advanced Local AI Assistant Platform

**Your data. Your AI. Your rules.** A production-ready AI assistant platform engineered for privacy, reliability, and transparency. Built on Angular 21 + FastAPI + MongoDB with intelligent multi-source reasoning, real-time streaming, and zero-hallucination architecture.


## Why MySlave?

Most AI assistants are black boxes that **invent facts**, **leak your data**, and **hide their reasoning**. MySlave is different:

**100% Transparent Decision-Making** — See exactly why the AI answered what it did  
**Privacy-First Architecture** — Everything runs locally, no telemetry, no cloud dependencies  
**Anti-Hallucination System** — Multi-layer validation prevents fabricated responses  
**Real-Time Streaming** — Token-by-token streaming with stop-generation control  
**Intelligent Context Management** — Multi-source context fusion with confidence tracking  
**Production-Ready** — Clean architecture, comprehensive error handling, fully typed


## Core Capabilities

### **1. Multi-Source Intelligent Context**

The AI doesn't just answer—it **intelligently assembles context** from multiple sources:

#### **File Intelligence**

- **Supported Formats**: PDF, DOCX, TXT, MD, CSV, JSON, YAML, code files
- **Smart Extraction**: PyPDF2, python-docx, fallback encoding (UTF-8 → Latin-1)
- **Attachment Persistence**: Files stored in MongoDB with 30-day expiry
- **Context Injection**: File content automatically prioritized as authoritative source

#### **Multi-Provider Web Search**

- **Providers**: SearXNG (privacy), DuckDuckGo (free), Serper (Google proxy), Tavily (research)
- **Smart Routing & Fallback Chain**: Auto-detects research queries with graceful degradation
- **Advance Search Mode**: Distributes queries across all enabled providers, deduplicates results
- **Quota Tracking**: Real-time monitoring of API limits with automatic provider switching
- **Result Ranking**: Sentence-based scoring prioritizes most relevant snippets

#### **URL Content Extraction**

- **Smart Truncation**: Extracts key points for web search enrichment
- **Source Attribution**: Full URL tracking in metadata

#### **Semantic Memory System**

- **Embedding-Based Search**: Cosine similarity matching with configurable threshold (0.3 default)
- **Categorized Storage**: `preference/fact`, `important`, `other`
- **Auto-Memory**: Automatically saves important exchanges for future context
- **Confidence Scoring**: Each memory tracks confidence level (0.95 default)

#### **Conversation History**

- **Configurable Depth**: Default 10 messages, customizable per-session
- **Follow-Up Mode**: Resolves pronouns/references against previous assistant answer
- **Smart Truncation**: Per-message character limits prevent context overflow

### **2. Anti-Hallucination Validation Pipeline (fabricate facts)**

**Solution**: Multi-layer validation and model limitation

#### **Source Layer Separation**

MySlave separates **factual sources** and **contextual sources**:

**Factual (High Confidence)**

- Files (0.99) — User-uploaded, authoritative
- Memory (0.85) — Verified past knowledge
- Web (0.65) — External grounding

**Contextual (Supporting Only)**

- History (0.0) — Continuity, not facts
- Follow-Up (0.0) — Reference resolution

**Why this matters**: The AI **cannot cite conversation history as a fact source**. It must draw facts from verifiable sources.

#### **Entity Validation Service**

**Dual-Mode Extraction**:

1. **NLP Mode** (spaCy): Extracts PERSON, ORG, GPE, DATE, MONEY, etc.
2. **Pattern Mode** (Fallback): Regex-based with intelligent common-word filtering

**Strategy Fuzzy Matching**:

- **Exact Match**: Direct substring matching
- **Partial Match**: Lower-case fuzzy matching
- **Stem Match**: Handles plurals/tenses ("company" ↔ "companies")
- **Acronym Expansion**: "FBI" ↔ "Federal Bureau Investigation"

**Factual Guard**

- Risk Levels:
- HIGH: 6+ Unverified entities → Cap confidence to 0.4
- MED: 3-5 Unverified entities → Cap confidence to 0.5
- LOW: <3 Unverified entities → Cap confidence to 0.6
- NONE: All entities verified → No cap

#### **Source Conflict Detection**: 

- Identifies contradictions between information sources

#### **Reasoning Veto System**  (Shows why answers were refused or confidence capped)

**Hard Vetoes** 

- "cannot confirm", "no reliable source", "conflicting sources"
- "no access to", "not covered in context", "outside my knowledge"

**Soft Vetoes** 

- "uncertain", "speculative", "probably", "assuming", "might"
- "not sure", "unclear", "low confidence"

#### **Confidence Calculation**

```
Initial Confidence (from source type) : 85%
    ↓
Hard Veto? → REFUSE ANSWER
Soft Veto? → Cap at 0.6
    ↓
Factual Guard (unverified entities)? → Cap by risk level
    ↓
Final Confidence
```

All stages tracked in metadata for full transparency.

### **3. Streaming Architecture**

**Real-Time Event Streaming** via Server-Sent Events (SSE):

```typescript
Event Types:
├─ token             // Final answer generation
├─ reasoning_token   // AI's thinking process generation
├─ metadata          // Confidence, sources, validation results
├─ done              // Stream complete
└─ error             // Error with recovery suggestions
```

**Benefits**:

- Token-by-token rendering for perceived speed
- Stop-generation control (user can interrupt)
- Transparent reasoning display (see AI's thought process)


### **4. Centralized Configuration System**

**Single Source of Truth**: All limits defined in [`settings.py`](backend/app/config/settings.py)

```python
# Example: Web search limits
WEB_SEARCH_RESULTS_PER_PROVIDER: int = 10
CHAT_WEB_SNIPPET_MAX_CHARS: int = 800
CHAT_WEB_TOTAL_MAX_CHARS: int = 6000

# Memory limits
MEMORY_SEARCH_LIMIT: int = 10
MEMORY_SEARCH_THRESHOLD: float = 0.3

# Confidence levels
CONFIDENCE_FILE: float = 0.99
CONFIDENCE_MEMORY: float = 0.85
CONFIDENCE_WEB: float = 0.65
```

**No magic numbers in code** — everything configurable via environment variables.


### **5. Custom Rules Engine**

Per-session:

```json
{
   "searxng": true,
   "duckduckgo": true,
   "tavily": false,
   "serper": false,
   "advanceSearch": false,
   "followUpEnabled": true,
   "reasoningEnabled": false,
   "customInstructions": "You are a Python expert...",
   "webSearchLimit": 10,
   "memorySearchLimit": 10,
   "historyLimit": 10
}
```

**Use Cases**:

- Define AI behavior and personality via system prompts
- Pre-configured rule templates for common use cases
- Multiple rules per session with priority management
- Dynamic rule injection into AI context
- Disable web search for sensitive conversations
- Enable reasoning mode for complex problem-solving
- Custom system instructions per session (personality, expertise)

### **6. Modern UI/UX**

- Clean, responsive design with CSS design system
- Skeleton loaders and smooth animations
- Collapsible reasoning/validation panels
- Color-coded confidence and risk indicators
- Real-time typing indicators
- Displays comprehensive metadata for each AI response


## Technical Stack

### **Backend**

- **FastAPI** 0.128.0 — Async-first, type-safe REST API
- **MongoDB** 4.16+ — Document database with Motor async driver
- **Ollama** — Local LLM inference
- **spaCy** 3.7+ — NLP for entity extraction (optional, graceful fallback)
- **Pydantic** v2 — Strict data validation
- **PyPDF2** — PDF text extraction
- **Streaming**: Server-Sent Events (SSE)
- **python-docx** — DOCX text extraction

### **Frontend**

- **Angular** 21.1.0 — Standalone components
- **Vite** — Fast build tool
- **Signal-based State** — Signal-based reactive state management (no RxJS)
- **EventSource** — SSE for real-time streaming
- **Marked.js** — Markdown rendering
- **Styling**: CSS Variables design system
- **Build**: Angular CLI with SSR support

### **Infrastructure**

- **Node.js** 20+ / **Python** 3.10+
- **MongoDB** 4.6+ (local/Docker/cloud)
- **Docker** (for MongoDB + SearXNG)

## Quick Start

### **1. Prerequisites**

```bash
# Check versions
node --version    # v20.19+ or v22.12+
python --version  # 3.10+
mongod --version  # 4.6+

# Install Ollama (https://ollama.ai)
ollama pull llama2:7b
ollama pull [model]
```

### **2. Backend Setup**

```bash
cd backend

# Clean up (optional but recommended)
rm -rf venv
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy for NLP entity extraction (Python 3.10-3.13 only)
pip install spacy
python -m spacy download en_core_web_sm

# Create .env
cp .env.example .env
Edit .env with your settings

# Start server
uvicorn app.main:app --reload
```

**API**: http://127.0.0.1:8000  
**API Docs**: http://127.0.0.1:8000/docs

### **3. Frontend Setup**

```bash
cd frontend

# Clean up (optional but recommended)
rm -rf node_modules .angular package-lock.json
npm cache clean --force

# Install dependencies
npm install

# Start development server
npx ng serve # --verbose /to see logs
```

**Frontend URL**: http://localhost:4200

### **4. Database Setup**

**Option A: MongoDB Service (Windows)**

```powershell
Start-Service MongoDB
```

**Option B: Docker**

```bash
docker run -d --name mongo -p 27017:27017 -v C:\data\db:/data/db mongo:7
```

**Option C: Manual Start**

```bash
mongod --dbpath /data/db
```

### **5. Local Web Search (SearXNG)**

```bash
cd searxng

# Edit settings.yml - set a strong secret_key
docker compose up -d
```

**SearXNG URL**: http://localhost:8080

## Configuration

### **Backend Environment (.env)**

Create `backend/.env`:
```env
# MongoDB
MONGO_URI=mongodb://127.0.0.1:27017
DB_NAME=myslave

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# CORS
CORS_ORIGINS=["http://localhost:4200"]

# Web Search (Optional)
SERPER_API_KEY=your_serper_key
TAVILY_API_KEY=your_tavily_key
SEARXNG_URL=http://localhost:8080

# Quotas
SERPER_TOTAL_LIMIT=2500
TAVILY_MONTHLY_LIMIT=1000

# Logging
LOG_LEVEL=INFO  # DEBUG for development
```

### **AI Models Configuration**

Edit `backend/app/config/ai_models.py`:
```python
AVAILABLE_MODELS = [
    {
        "id": "llama2:13b",
        "name": "Llama 2 13B",
        "description": "Powerful reasoning",
        "context_length": 4096
    },
    # Add custom models
]
```

## 🛠️ Development

### **Backend Development**

- Backend: Ruff for linting/formatting

**Code Quality**

```bash
cd backend

# Lint and format with Ruff
ruff check --fix .
ruff format .
```

**Testing**

```bash
pytest
pytest --cov=app
pytest -v tests/....
pytest -v
```

### **Frontend Development**

- Frontend: Prettier + ESLint

**Code Quality**

```bash
cd frontend

# Format with Prettier
npm run format:check
npm run format:fix

# Linting (ESLint)
ng eslint src --fix
```

**Testing**

```bash
npm test
npm run test:coverage
```

## Troubleshooting

### **MongoDB Connection Failed**

```bash
# Check MongoDB running
mongosh --eval "db.adminCommand('ping')"

# Verify connection string in settings
# Default: mongodb://127.0.0.1:27017

# Start MongoDB service
Start-Service MongoDB  # Windows
sudo systemctl start mongod  # Linux

# Or use Docker
docker start mongo

# Create database (auto-created on first run)
mongosh myslave
```

### **Ollama Not Responding**

```bash
# Check Ollama running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull missing models
ollama pull gemma:7b
```

### **Web search no results**

- Check SearXNG is running if using local search
- Review quotas in: serper_quota, tavily_quota
- Check backend logs for API errors
- Check provider settings in Rules UI. Verify API keys in `.env` are set correctly.

### **Entity extraction errors**

```bash
# Install spaCy: 
pip install spacy 
python -m spacy download en_core_web_sm
```

## Privacy & Security

### **Privacy Guarantees**

**100% Local Processing**: All AI inference runs on your machine  
**No Telemetry**: Zero tracking, analytics, or data collection  
**Local Data Storage**: All conversations stay in your MongoDB  
**No Cloud Dependencies**: Works completely offline (except optional web search)  
**Optional Web** — Serper/Tavily only when you enable/trigger search  
**Open Source**: Full code transparency, audit at any time
**No Third-Party CDNs** — All assets bundled

### **External Services**

**Web Search Providers** (Serper, Tavily):
- Only used when explicitly requested
- Can be disabled in settings
- Local alternative: SearXNG (fully private)

### **Security Best Practices**

1. **MongoDB**

```bash
# Enable MongoDB authentication
mongod --auth --bind_ip 127.0.0.1
# Set strong MongoDB passwords
```

2. **Reverse Proxy** (Nginx/Caddy)

```nginx
# Use HTTPS with reverse proxy (nginx/Caddy)
location /api {
    proxy_pass http://127.0.0.1:8000;
}
```

3. **Firewall Rules**

```bash
ufw allow 4200/tcp  # Frontend
ufw allow 8000/tcp  # Backend (localhost only recommended)
```

4. **CORS Restrictions**

```env
CORS_ORIGINS=["http://localhost:4200"]  # Whitelist only
```

5. **Set strong `secret_key` for SearXNG**

```
<random 32-64 chars>
```

6. **Update dependencies regularly**

## 📈 Performance

### **System Requirements**

**Minimum**:

- 8GB RAM
- 4-core CPU
- 20GB disk space
- MongoDB 4.6+

**Recommended**:

- 16GB+ RAM (for larger models)
- 8-core CPU
- SSD for MongoDB
- GPU for faster inference (optional)

### **Model Memory Usage**

- 7B parameters: ~6-8GB RAM
- 13B parameters: ~10-12GB RAM
- 33B+ parameters: 20GB+ RAM

### **Optimizations**

- MongoDB connection pooling
- Async I/O throughout
- Efficient embedding caching
- Lazy loading in frontend
- SSE streaming reduces memory
- Signal-based reactivity (minimal rerenders)
- Configure Ollama GPU acceleration (CUDA/ROCm)
- Limit concurrent sessions (1-3 for 7B models on 8GB RAM)

## Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **README**: files in major directories

---

## Contributing

Built with best-in-class open-source tools:

- [**Ollama**](https://ollama.ai) — Local LLM inference engine
- [**FastAPI**](https://fastapi.tiangolo.com) — Modern Python web framework
- [**Angular**](https://angular.dev) — Enterprise web framework
- [**MongoDB**](https://www.mongodb.com) — Document database
- [**spaCy**](https://spacy.io) — Industrial-strength NLP
- [**SearXNG**](https://docs.searxng.org) — Privacy-respecting metasearch

---


## FAQ 

**Q: Is my data truly private?**  
A: Yes. All LLM inference runs locally via Ollama. Web search is optional and only triggers when you enable it. MongoDB is local. Zero telemetry.

**Q: Do I need a GPU?**  
A: No, but it helps. Ollama works on CPU, just slower.

**Q: Can I use custom models?**  
A: Yes! Any Ollama-compatible model. Add to `ai_models.py`.

**Q: Why is reasoning separate from answer?**  
A: Separating internal thoughts from user-facing response improves quality and enables validation.

**Q: What's the veto system?**  
A: AI checks its own reasoning. If it said "cannot confirm" internally but generated a confident answer externally, veto system catches this inconsistency.

**Q: How does entity validation work?**  
A: Extracts names/places from answer, checks if they appear in source documents. Flags unverified entities.

**Q: Why fuzzy matching?**  
A: Exact matching fails on plurals ("APIs" vs "API"), partial phrases ("John Smith" in "Dr. John Smith"), etc.

**Q: How does follow-up mode work?**  
A: When enabled, the AI treats the **previous assistant answer** as the **primary context**. Pronouns/references resolve against it first, then fall back to conversation history.

**Q: Do I need spaCy?**  
A: Recommended. System falls back to pattern-based extraction.

## Roadmap

### **Planned Features**
1. Plugin system for custom model providers
2. Docker Compose (Single-command Docker startup)
3. Vector database abstraction layer (Qdrant / Weaviate support)
4. Collaborative sessions (shared conversations)
5. Prompt preset / lightweight fine-tuning interface
6. Voice input & output
7. Advanced RAG (Graph-enhanced retrieval / GraphRAG - experimental)
8. Kubernetes deployment configs

---

**Built with ❤️ for privacy-conscious developers**