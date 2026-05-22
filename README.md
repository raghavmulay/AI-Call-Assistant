# AI Call Assistant — Real-Time Voice AI Campus Assistant

A real-time voice-based AI assistant for college campuses. Students speak naturally into a microphone, the system understands their query, fetches accurate information, and responds with a human-like voice — all in under 3 seconds.

---

## Features

- Real-time voice input via microphone
- Speech-to-Text using faster-whisper (Whisper tiny model)
- Voice Activity Detection (VAD) — only processes actual speech
- Intent detection across 30+ campus query types
- Sub-100ms responses for structured queries (fees, hostel, documents, etc.)
- ~500ms responses for general chat via Groq LLM (llama-3.1-8b-instant)
- Text-to-Speech using Microsoft Edge Neural TTS
- Barge-in support — interrupt the AI mid-response
- Conversation memory via Redis (per-session history)
- JWT-based authentication (student / faculty / admin)
- REST API + WebSocket real-time audio pipeline
- Single command launch

---

## System Architecture

```
Microphone
    ↓
WebSocket Client (client_streamer.py)
    ↓  [PCM16 audio chunks @ 40ms]
WebSocket Server (/ws/audio/{session_id})
    ↓
VAD (webrtcvad) — detects speech vs silence
    ↓
Whisper STT (faster-whisper tiny) — ~800ms
    ↓
Intent Detector — keyword-based, 30+ intents
    ↓
Router — decides: Structured JSON / Database / LLM
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│ Structured JSON │  PostgreSQL DB   │   Groq LLM      │
│ (10-30ms)       │  (attendance,    │ (general chat,  │
│ fees, hostel,   │   timetable)     │  ~500ms)        │
│ docs, branches  │                  │                 │
└─────────────────┴──────────────────┴─────────────────┘
    ↓
Redis Memory — stores conversation history
    ↓
Edge TTS — synthesizes voice response
    ↓
WebSocket Client — plays audio via pygame
    ↓
Speaker Output
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy (async) |
| Conversation Memory | Redis |
| Speech-to-Text | faster-whisper (tiny, CPU) |
| Voice Activity Detection | webrtcvad |
| Text-to-Speech | edge-tts (Microsoft Neural) + pyttsx3 fallback |
| LLM | Groq API — llama-3.1-8b-instant |
| Authentication | JWT (python-jose) + bcrypt |
| Real-time Communication | WebSocket |
| Audio Playback | pygame |

---

## Prerequisites

Before running the project, install and set up the following:

### 1. Python 3.10 or 3.12
Download from https://www.python.org/downloads/

### 2. PostgreSQL
Download from https://www.postgresql.org/download/
- Create a database named `ai_assistant_db`
- Default user: `postgres`

### 3. Redis
**Windows:** Download from https://github.com/microsoftarchive/redis/releases
- Download `Redis-x64-3.0.504.msi` or similar
- Install and it will run as a Windows service
- Or run manually: `C:\Redis\redis-server.exe`

**Linux/Mac:**
```bash
sudo apt install redis-server   # Ubuntu
brew install redis              # Mac
```

### 4. Groq API Key (Free)
- Sign up at https://console.groq.com
- Create an API key (free tier: 14,400 requests/day)
- Copy the key — you'll need it in `.env`

### 5. Microsoft Visual C++ Build Tools (Windows only)
Required for webrtcvad compilation.
Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
Install "Desktop development with C++"

---

## Installation

### Step 1 — Clone the repository
```bash
git clone <repository-url>
cd AI-Call-Assistant
```

### Step 2 — Create and activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

> If `webrtcvad-wheels` fails on Windows, try:
> ```bash
> pip install webrtcvad-wheels --no-build-isolation
> ```

### Step 4 — Configure environment variables
Copy the example env file and fill in your values:
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

Edit `.env`:
```env
# PostgreSQL — update with your credentials
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ai_assistant_db

# Security — generate a random secret key
SECRET_KEY=your_random_secret_key_here

# Groq API — paste your key from console.groq.com
GROQ_API_KEY=gsk_your_groq_api_key_here

# Redis
REDIS_URL=redis://localhost:6379/0
MEMORY_TTL=3600
MAX_CONVERSATION_WINDOW=15

# Rate Limiting
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW=60
```

> To generate a SECRET_KEY:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Running the Project

### Step 1 — Start Redis
```bash
# Windows
C:\Redis\redis-server.exe

# Linux/Mac
redis-server
```
Keep this terminal open.

### Step 2 — Start everything with single command
Open a new terminal in the project root:
```bash
python run.py
```

This will:
1. Start the FastAPI backend on `http://localhost:8000`
2. Wait 5 seconds for backend to initialize
3. Start the microphone client streamer
4. Connect to WebSocket and begin listening

### Step 3 — Speak!
Once you see:
```
[client] Connected → ws://localhost:8000/ws/audio/test-1
```
You can start speaking. The system will:
- Show `[you] your transcript` when it hears you
- Show `[tts] response text` when it responds
- Play the response through your speakers

### Stop
Press `Ctrl+C` to stop both backend and client.

---

## Custom Session ID
```bash
python run.py --session student-123
```

---

## API Documentation
Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## REST API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/signup/student` | Register a new student |
| POST | `/signup/faculty` | Register a new faculty/admin |
| POST | `/login` | Login and get JWT token |

### AI Assistant
| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Text-based AI query |
| POST | `/voice-query` | Base64 audio AI query |
| POST | `/rag-query` | Direct document query |

### WebSocket
| Endpoint | Description |
|---|---|
| `ws://localhost:8000/ws/audio/{session_id}` | Real-time voice streaming |
| `ws://localhost:8000/ws/notifications` | Push notifications |

---

## Supported Query Types

| Category | Example Queries |
|---|---|
| Fees | "What are the fees for IT department?" |
| Hostel | "Tell me about hostel fees and facilities" |
| Documents | "What documents are required for admission?" |
| Branches | "Which branches are offered?" |
| Placements | "What is the average placement package?" |
| Admission Dates | "When does admission start?" |
| Cutoff | "What is the cutoff for computer engineering?" |
| Eligibility | "Am I eligible for admission?" |
| Scholarship | "What scholarships are available?" |
| Office Timing | "What are the office hours?" |
| Office Location | "Where is the admission office?" |
| Contact | "What is the helpline number?" |
| Greeting | "Hello", "Good morning" |
| General Chat | Any other campus-related question |

---

## Project Structure

```
AI-Call-Assistant/
├── run.py                          # Single launcher — starts everything
├── client_streamer.py              # Microphone WebSocket client
├── requirements.txt
├── .env                            # Environment variables (not committed)
├── .env.example                    # Template for .env
└── backend/
    └── app/
        ├── main.py                 # FastAPI app entrypoint
        ├── core/
        │   ├── config.py           # Settings from .env
        │   ├── logger.py           # Logging setup
        │   └── redis.py            # Redis client
        ├── api/                    # REST API routes
        │   ├── auth.py
        │   ├── ai.py
        │   ├── student.py
        │   ├── faculty.py
        │   ├── notices.py
        │   └── chat_history.py
        ├── ai/
        │   ├── orchestrator/       # Core AI pipeline
        │   │   ├── orchestrator.py # Main 8-step flow
        │   │   ├── router.py       # Intent → route mapping
        │   │   ├── services.py     # Data retrieval services
        │   │   ├── context_manager.py
        │   │   ├── memory_manager.py
        │   │   └── response_builder.py
        │   ├── intent/
        │   │   ├── intent_detector.py  # Keyword-based intent detection
        │   │   └── intent_handler.py
        │   ├── knowledge/          # JSON knowledge base
        │   │   ├── fees.json
        │   │   ├── documents.json
        │   │   ├── faq.json
        │   │   ├── admission_dates.json
        │   │   ├── hostel/hostel.json
        │   │   ├── office/office.json
        │   │   └── placements/placements.json
        │   ├── llm/
        │   │   └── async_llm.py    # Groq API client
        │   ├── memory/
        │   │   └── redis_memory.py # Redis conversation storage
        │   └── prompts/
        │       ├── system_prompts.py
        │       └── serializer.py   # Direct response generator
        ├── realtime/               # Real-time voice pipeline
        │   ├── websocket/
        │   │   ├── websocket_router.py  # WS endpoint
        │   │   ├── connection_manager.py
        │   │   └── session_manager.py
        │   ├── stt/
        │   │   ├── streaming_stt.py     # Whisper STT
        │   │   ├── vad_manager.py       # Voice activity detection
        │   │   └── transcript_manager.py
        │   ├── tts/
        │   │   ├── tts_engine.py        # Edge TTS + pyttsx3
        │   │   └── audio_response.py    # WS audio delivery
        │   ├── conversation/
        │   │   ├── conversation_coordinator.py  # Turn pipeline
        │   │   └── conversation_state.py
        │   └── audio/
        │       ├── audio_stream.py
        │       └── packet_processor.py
        ├── models/                 # SQLAlchemy ORM models
        ├── schemas/                # Pydantic schemas
        ├── services/               # Business logic
        ├── auth/                   # JWT + hashing
        ├── database/               # DB engine + session
        └── middleware/             # Logging + rate limiting
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | JWT signing key (32+ random chars) |
| `GROQ_API_KEY` | ✅ | Groq API key from console.groq.com |
| `REDIS_URL` | ✅ | Redis connection URL |
| `MEMORY_TTL` | ❌ | Conversation memory TTL in seconds (default: 3600) |
| `MAX_CONVERSATION_WINDOW` | ❌ | Max turns to keep in memory (default: 15) |
| `RATE_LIMIT_REQUESTS` | ❌ | Max requests per window (default: 20) |
| `RATE_LIMIT_WINDOW` | ❌ | Rate limit window in seconds (default: 60) |
| `ALLOWED_ORIGINS` | ❌ | CORS origins (default: localhost:3000,5173) |
| `DEBUG` | ❌ | Enable debug logging (default: False) |

---

## Troubleshooting

### "No module named 'groq'"
```bash
pip install groq
```

### "No module named 'webrtcvad'"
```bash
pip install webrtcvad-wheels
```
On Windows, ensure Visual C++ Build Tools are installed.

### Redis connection refused
Make sure Redis is running:
```bash
C:\Redis\redis-server.exe   # Windows
redis-server                # Linux/Mac
```

### Microphone not detected
Run the mic test utility:
```bash
python mic_test.py
```
This lists all available input devices and tests the default one.

### PostgreSQL connection failed
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env` matches your credentials
- Create the database if it doesn't exist:
```sql
CREATE DATABASE ai_assistant_db;
```

### TTS not playing audio
- Ensure pygame is installed: `pip install pygame`
- Check your system audio output device is set correctly

### Barge-in interrupting responses too early
This can happen if the TTS speaker audio is picked up by the microphone.
Use headphones to prevent audio feedback.

### High STT latency (>2s)
The Whisper tiny model runs on CPU. This is expected on low-end hardware.
Latency is typically 800ms–1.3s on modern CPUs.

---

## Performance Benchmarks

| Query Type | Typical Latency |
|---|---|
| Structured (fees, hostel, docs, etc.) | 10 – 30ms |
| Greeting / thanks / farewell | < 5ms |
| General chat (Groq LLM) | 400 – 750ms |
| STT (Whisper tiny, CPU) | 800ms – 1.3s |
| TTS first sentence (Edge TTS) | 600 – 900ms |
| Total turn (structured query) | ~2 – 3s |
| Total turn (general chat) | ~3 – 4s |

---

## Known Limitations

- Whisper STT occasionally mishears words (e.g. "hostel fee" → "hostile fee") — use a good quality microphone
- RAG pipeline (syllabus/policy queries) is currently disabled — falls back to Groq general chat
- Database queries (attendance, timetable) require JWT authentication — not available via voice WebSocket without login
- Barge-in may trigger from speaker audio if not using headphones

---

## License

This project was developed as part of the EDI (Entrepreneurship Development and Innovation) course at VIT Pune.
