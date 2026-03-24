# F1 Navigator — TAMU

A full-stack web app for F-1 international students at TAMU. Provides AI-powered visa guidance, process timelines, document storage, email notifications, and USCIS form pre-filling.

---

### 🚀 `How to run repo`
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
#### Start the backend server
```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### Start the frontend server
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at: http://localhost:3000

---

### 🖥️ `Frontend`
- **Next.js 15** (App Router) with **TypeScript** and **Tailwind CSS**
- **shadcn/ui** component library
- ChatGPT-style interface: collapsible sidebar, session history, landing page
- Multiple simultaneous chat sessions (streams continue in background when switching chats)
- Session history persisted in browser `localStorage`

**Views:**
- **Chat** — AI assistant powered by RAG pipeline
- **Process Guides** — OPT, STEM OPT, CPT, H-1B flowcharts with key date timelines
- **Policy Updates** — real-time F-1 news feed
- **Documents** — document upload and storage
- **ISO Meeting** — meeting request scheduler
- **Profile** — student profile with 20+ fields
- **I-765 Form** — pre-filled USCIS Employment Authorization form (OPT / STEM OPT)

---

### 📁 `main.py`
- Defines all HTTP endpoints.
- Uses FastAPI **lifespan events** to initialize/close the database pool and start/stop the APScheduler on startup/shutdown.
- The `/api/chat` endpoint returns a **StreamingResponse** that streams Server-Sent Events (SSE) as the LLM generates tokens in real time.
- `/api/notifications` (GET/PUT) — manages per-user email notification preferences.

---

### 🗄️ `database.py`
- Manages the **PostgreSQL database (hosted on Render)** using `asyncpg`.
- Implements a connection pool for efficient concurrent access.
- Runs idempotent migrations on startup via `_migrate()` (adds new columns with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).
- Handles all SQL queries related to:
  - Users & authentication
  - Profiles (20+ fields including address, DOB, sex, marital status, SEVIS number, etc.)
  - Documents
  - Meeting requests
  - Notification preferences

- Pinecone — stores document chunks for the RAG pipeline.

---

### 🔐 `auth.py`
- Handles authentication and authorization.
- Uses:
  - `bcrypt` for password hashing
  - `PyJWT` for token creation and verification (30-day TTL)

---

### 🔔 `notifications.py`
- Sends **email notifications** to students 5 days before key visa deadlines.
- `compute_key_dates()` — mirrors the frontend timeline logic for OPT, STEM OPT, CPT, and H-1B.
- `send_notification_email()` — sends styled HTML email via SMTP (Gmail App Password).
- `run_daily_notifications()` — queries all users with notification preferences enabled, checks proximity to deadlines, and sends emails.
- Scheduled daily via **APScheduler** (`AsyncIOScheduler`) cron job in `main.py`.

**Required `.env` vars:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`

---

### 🤖 `How RAG Works`
The system uses a **hybrid Retrieval-Augmented Generation (RAG)** pipeline to answer user queries with high relevance and low hallucination.
### Flow
1. **Embed Query** - The user's question is converted into a vector using `text-embedding-3-large`.
2. **Semantic Search** - The query vector is used to retrieve the **top 30 relevant chunks** from Pinecone.
3. **BM25 Re-ranking** - These 30 results are re-ranked using **BM25 keyword scoring** to prioritize exact term matches.
4. **Deduplication** - Duplicate chunks are removed using:
     - Text hash
     - (URL + section) key
5. **Context Selection** - The top **7 most relevant chunks** are selected as final context.
6. **LLM Generation** - The selected context + query is sent to `GPT-4o` with a system prompt personalised with the student's profile.
7. **Streaming Response** - The response is streamed token-by-token using an `AsyncGenerator` via SSE.

**Sources indexed:** USCIS, ICE/SEVP, Study in the States (DHS)

---

### 📰 `How News Pipeline Works`
The system fetches and processes **real-time external news data** using a lightweight pipeline.
### Flow
1. **Parallel Searches** - Runs **7 DuckDuckGo searches** in parallel using a thread executor (to avoid blocking async execution).
2. **Aggregate Results** - Collects all results from the searches.
3. **Deduplicate** - Removes duplicate articles based on URL.
4. **LLM Filtering & Structuring** - Uses `gpt-4o-mini` to:
     - Filter irrelevant articles
     - Keep only domain-specific content (F-1 visa, immigration)
     - Structure the output
- Results are **cached in memory for 1 hour** to avoid redundant API calls.

---
