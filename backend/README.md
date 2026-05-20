# 🎓 Real-Time AI Campus Assistant — Backend API

A production-style FastAPI backend powering the AI Campus Assistant.  
Supports authentication, student/faculty management, attendance tracking, timetables, notices, assignments, AI chat, and real-time WebSocket notifications.

---

## 📁 Folder Structure

```
backend/
├── main.py                  ← FastAPI app entrypoint
├── database.py              ← Async SQLAlchemy engine + session
├── config.py                ← Pydantic BaseSettings (.env config)
├── requirements.txt         ← All Python dependencies
├── .env.example             ← Environment variable template
│
├── models/                  ← SQLAlchemy ORM models (8 tables)
│   ├── student.py
│   ├── faculty.py
│   ├── subject.py
│   ├── attendance.py
│   ├── timetable.py
│   ├── notice.py
│   ├── chat_history.py
│   └── assignment.py
│
├── schemas/                 ← Pydantic v2 request/response schemas
│   ├── auth.py
│   ├── student.py
│   ├── notice.py
│   ├── assignment.py
│   ├── attendance.py
│   ├── timetable.py
│   └── chat.py
│
├── routes/                  ← FastAPI route handlers
│   ├── auth.py              ← /signup, /login
│   ├── student.py           ← /student/...
│   ├── faculty.py           ← /faculty/...
│   ├── notices.py           ← /notices
│   ├── ai.py                ← /chat, /voice-query, /rag-query
│   └── chat_history.py      ← /chat-history/{student_id}
│
├── services/                ← Business logic (DB queries)
│   ├── student_service.py
│   ├── faculty_service.py
│   ├── notice_service.py
│   ├── assignment_service.py
│   ├── chat_service.py
│   └── ai_service.py        ← Bridges to RAG/LLM/STT modules
│
├── auth/                    ← JWT + passlib security
│   ├── hashing.py
│   ├── jwt_handler.py
│   └── dependencies.py      ← get_current_user, require_role()
│
├── websocket/
│   └── notification_ws.py   ← WS /ws/notifications (JWT-protected)
│
├── middleware/
│   └── logging_middleware.py
│
└── utils/
    └── responses.py         ← success_response(), error_response()
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+
- (Optional) Ollama running locally for LLM

### 2. PostgreSQL Setup

Open `psql` and run:

```sql
CREATE DATABASE campus_assistant_db;
CREATE USER campus_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE campus_assistant_db TO campus_user;
```

### 3. Environment Variables

```bash
# From the AI-Call-Assistant/ project root:
cd backend
copy .env.example .env
```

Edit `.env` and fill in:

```env
DATABASE_URL=postgresql+asyncpg://campus_user:yourpassword@localhost:5432/campus_assistant_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

### 4. Install Dependencies

```bash
# From the AI-Call-Assistant/ project root:
pip install -r backend/requirements.txt
```

### 5. Run the Server

```bash
# From the AI-Call-Assistant/ project root:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will automatically create all database tables on first startup.

### 6. Open API Docs

- **Swagger UI**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 Authentication Flow

```
Client                              Backend
  │                                    │
  ├──POST /signup/student ─────────────►  Creates student, returns JWT
  │                                    │
  ├──POST /login ──────────────────────►  Verifies credentials, returns JWT
  │                                    │
  ├──GET /student/profile/{id}         │
  │  Authorization: Bearer <token> ────►  Validates JWT, returns profile
  │                                    │
```

### Roles
| Role      | Can Access                                      |
|-----------|-------------------------------------------------|
| `student` | Own profile, attendance, timetable, chat        |
| `faculty` | Upload notices/assignments, view all students   |
| `admin`   | Everything faculty can do                       |

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint            | Description              | Auth |
|--------|---------------------|--------------------------|------|
| POST   | `/signup/student`   | Register student         | ❌   |
| POST   | `/signup/faculty`   | Register faculty/admin   | ❌   |
| POST   | `/login`            | Login, get JWT token     | ❌   |

### Student
| Method | Endpoint                       | Description              | Auth |
|--------|--------------------------------|--------------------------|------|
| GET    | `/student/profile/{id}`        | Get student profile      | ✅   |
| GET    | `/student/attendance/{id}`     | Get attendance summary   | ✅   |
| GET    | `/student/timetable/{id}`      | Get weekly timetable     | ✅   |
| GET    | `/student/assignments/{id}`    | Get upcoming assignments | ✅   |

### Faculty
| Method | Endpoint                    | Description              | Auth (faculty+) |
|--------|-----------------------------|--------------------------|-----------------|
| POST   | `/faculty/upload-notice`    | Create a campus notice   | ✅              |
| POST   | `/faculty/upload-assignment`| Post an assignment       | ✅              |
| GET    | `/faculty/students`         | List all students        | ✅              |

### AI Assistant
| Method | Endpoint        | Description                  | Auth |
|--------|-----------------|------------------------------|------|
| POST   | `/chat`         | Text chat with AI assistant  | ✅   |
| POST   | `/voice-query`  | Voice (base64 audio) query   | ✅   |
| POST   | `/rag-query`    | Direct RAG document query    | ✅   |

### Notices & Chat History
| Method | Endpoint                       | Description                    | Auth |
|--------|--------------------------------|--------------------------------|------|
| GET    | `/notices`                     | Get all campus notices         | ❌   |
| GET    | `/chat-history/{student_id}`   | Get AI chat history            | ✅   |

### WebSocket
| Protocol  | Endpoint               | Description                        |
|-----------|------------------------|------------------------------------|
| WebSocket | `/ws/notifications`    | Real-time push notifications       |

Connect: `ws://localhost:8000/ws/notifications?token=<JWT>`

---

## 🧪 Sample API Requests & Responses

### POST /signup/student
```json
// Request
{
  "name": "Yashraj Nagargoje",
  "email": "yash@college.edu",
  "password": "securepass123",
  "branch": "Computer Engineering",
  "year": 4,
  "division": "A",
  "cgpa": 8.5
}

// Response 201
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "role": "student",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /student/attendance/{id}
```json
// Response 200
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "overall_average": 78.5,
  "records": [
    { "subject_name": "Data Structures", "attendance_percent": 85.0 },
    { "subject_name": "DBMS", "attendance_percent": 72.0 }
  ]
}
```

### POST /chat
```json
// Request
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is my attendance in Data Structures?"
}

// Response 200
{
  "student_id": "550e8400-...",
  "user_message": "What is my attendance in Data Structures?",
  "ai_response": "Your attendance in Data Structures is 85%, which is above the required 75% threshold.",
  "created_at": "2026-05-20T17:30:00Z"
}
```

---

## 🛠️ Database Schema

```
students ──────────────────────── attendance (student_id FK)
    │                              │
    └── chat_history               └── subjects (subject_id FK)
                                         │
faculty ────────────────────────── subjects (faculty_id FK)
    │                              │
    ├── notices                    ├── timetable
    └── assignments                └── assignments
```

---

## 🔄 AI Integration Architecture

```
Client Voice/Text
      │
      ▼
POST /chat or /voice-query
      │
      ▼
ai_service.py
  ├── Fetch student attendance + timetable from DB (context)
  ├── Build enriched prompt
  └── Call app/rag/rag_pipeline.py → Ollama LLM
      │
      ▼
Save to chat_history table
      │
      ▼
Return AI response to client
```

---

## 🚀 Production Tips

1. **Generate a strong `SECRET_KEY`:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Use Alembic for DB migrations** (instead of `create_all` in production):
   ```bash
   alembic init alembic
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

3. **Run with multiple workers:**
   ```bash
   uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

4. **Set `DEBUG=False`** in `.env` for production (hides SQL query logs).
