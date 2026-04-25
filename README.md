# Smart AI Study Companion 🎓

An AI-powered study tool that helps students understand dense lecture notes through explanations, quizzes, and voice Q&A — built to demonstrate **10 core Generative AI concepts**.

> **Final-Year Project** · Python 3.11.14 · FastAPI · Streamlit · Groq (Llama-3.3-70B) · ChromaDB · Whisper · gTTS

---

## Core GenAI Concepts Demonstrated

| # | Concept | Where Used |
|---|---|---|
| 1 | **LLM via API** | All text generation — Groq / Llama-3.3-70B-versatile |
| 2 | **Prompt Engineering** | Custom system prompts for explain, quiz, and Q&A |
| 3 | **RAG** | Every answer retrieved from ChromaDB before LLM call |
| 4 | **Embeddings** | `all-MiniLM-L6-v2` converts every chunk to a 384-dim vector |
| 5 | **Vector Database** | ChromaDB stores and similarity-searches all embeddings |
| 6 | **Text Chunking** | RecursiveCharacterTextSplitter (500 tok / 50 overlap) |
| 7 | **Speech-to-Text** | OpenAI Whisper (local, `base` model, runs on CPU) |
| 8 | **Text-to-Speech** | gTTS converts LLM answers to MP3 audio |
| 9 | **Structured Output** | LLM returns explain/quiz/Q&A as strict JSON |
| 10 | **Grounded Generation** | Q&A prompt forbids the LLM from using outside knowledge |

---

## Features

| Page | What it does |
|---|---|
| Home | Project overview, GenAI concepts table, backend health status |
| Upload | PDF / TXT / image to text extraction to chunking to embeddings to ChromaDB |
| Explain | RAG-grounded plain-language explanation with key points and analogy |
| Quiz | Auto-generated MCQs with scoring and per-question explanations |
| Voice Q&A | Speak a question, Whisper STT, RAG, Groq, gTTS MP3 answer |

---

## Project Structure

```
ai-study-companion/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes, startup model preload
│   │   ├── config.py            # All settings loaded from .env
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic request / response models
│   │   ├── routes/
│   │   │   ├── health.py        # GET /health
│   │   │   ├── upload.py        # POST /api/upload, GET /api/documents
│   │   │   ├── explain.py       # POST /api/explain
│   │   │   ├── ask.py           # POST /api/ask
│   │   │   ├── quiz.py          # POST /api/generate-quiz, /api/evaluate-quiz
│   │   │   └── voice.py         # POST /api/voice-query
│   │   ├── services/
│   │   │   ├── document_loader.py   # PDF / TXT / OCR text extraction
│   │   │   ├── chunker.py           # RecursiveCharacterTextSplitter
│   │   │   ├── embedder.py          # all-MiniLM-L6-v2 singleton
│   │   │   ├── vector_store.py      # ChromaDB PersistentClient singleton
│   │   │   ├── llm_service.py       # Groq client singleton
│   │   │   ├── rag_engine.py        # retrieve_context + build_context_string
│   │   │   ├── json_parser.py       # Robust JSON extraction from LLM output
│   │   │   ├── stt_service.py       # Whisper transcription
│   │   │   └── tts_service.py       # gTTS MP3 generation + cleanup
│   │   └── prompts/
│   │       ├── explain_prompt.py
│   │       ├── qa_prompt.py
│   │       └── quiz_prompt.py
│   ├── data/                    # Created at runtime (gitignored)
│   │   ├── uploads/
│   │   ├── chroma_db/
│   │   └── audio/
│   ├── .env.example             # Copy to .env and add your GROQ_API_KEY
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py         # Home page
│   ├── pages/
│   │   ├── 1_Upload.py
│   │   ├── 2_Explain.py
│   │   ├── 3_Quiz.py
│   │   └── 4_Voice_QA.py
│   └── .streamlit/
│       └── config.toml          # Black + #FCB800 theme
├── pyproject.toml               # All dependencies — install with uv sync
├── .python-version              # Pins Python 3.11.14 for uv
├── Procfile                     # For Render / Railway deployment
├── render.yaml                  # Render blueprint
└── README.md
```

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| **uv** | Python version manager + package installer | See below |
| **Tesseract OCR** | Image-to-text (only needed for image uploads) | https://github.com/UB-Mannheim/tesseract/wiki |
| **Groq API key** | Free LLM access (Llama-3.3-70B) | https://console.groq.com |

Install uv:

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv automatically downloads and manages Python 3.11.14 — no separate Python install needed.

---

## Setup and Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai-study-companion
```

### 2. Create the virtual environment (Python 3.11.14)

```bash
uv python install 3.11.14
uv venv --python 3.11.14
```

Activate the venv:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install all dependencies

```bash
# Windows CMD — set a longer timeout for large packages
set UV_HTTP_TIMEOUT=120
uv sync

# macOS / Linux
UV_HTTP_TIMEOUT=120 uv sync
```

All packages are listed in pyproject.toml with pinned versions.

### 4. Install OpenAI Whisper (one-time step after uv sync)

```bash
uv pip install wheel
uv pip install openai-whisper==20231117 --no-build-isolation
```

Why separately? Whisper uses a legacy setup.py that imports pkg_resources as a build tool
but never declares it. --no-build-isolation bypasses the clean build sandbox so the venv's
own setuptools (pinned below version 71) provides pkg_resources correctly.

### 5. Configure environment variables

```bash
# Windows
copy backend\.env.example backend\.env

# macOS / Linux
cp backend/.env.example backend/.env
```

Open backend/.env and set your Groq key:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Get a free key at https://console.groq.com (no credit card required).

### 6. Pre-download the embedding model (recommended)

Avoids a 90 MB download on the first upload request:

```bash
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 7. Start the FastAPI backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

- Health check: http://127.0.0.1:8000/health
- Swagger docs: http://127.0.0.1:8000/docs

### 8. Start the Streamlit frontend

Open a second terminal, activate the venv, then:

```bash
cd frontend
uv run streamlit run streamlit_app.py
```

App runs at http://localhost:8501

---

## Usage

1. Go to Upload and upload a PDF, TXT file, or image of your notes
2. Go to Explain to get a plain-language explanation with key points and analogy
3. Go to Quiz to generate and take a quiz, then see your score and explanations
4. Go to Voice Q&A to ask a question by voice and hear the answer spoken back

---

## Deployment Guide

### Option A — Render (recommended, free tier)

1. Push the repo to GitHub.
2. Go to https://render.com, click New, then Blueprint, and connect your repo.
3. Render reads render.yaml and creates the web service automatically.
4. Set GROQ_API_KEY in the Render dashboard under Environment.
5. The backend will be live at https://your-service.onrender.com.

Note: Whisper (~140 MB) and the embedding model (~90 MB) download on first startup.
This can take 3-5 minutes on the free tier.

### Option B — Railway

1. Push to GitHub.
2. Go to https://railway.app, click New Project, then Deploy from GitHub.
3. Add the environment variable GROQ_API_KEY.
4. Railway reads Procfile for the start command.

### Option C — Local network (demo / presentation)

Run both servers on your machine and share your local IP:

```bash
# Backend (accessible on LAN)
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (second terminal)
cd frontend
uv run streamlit run streamlit_app.py --server.address 0.0.0.0
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API — llama-3.3-70b-versatile (free) |
| Embeddings | sentence-transformers — all-MiniLM-L6-v2 (local) |
| Vector DB | ChromaDB (local, persistent) |
| STT | OpenAI Whisper — base model (local, CPU) |
| TTS | gTTS (Google TTS, online) |
| PDF parsing | pdfplumber |
| OCR | pytesseract + Pillow |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Package manager | uv |

---

## Build Phases

- [x] Phase 1 — Project setup (uv, pyproject.toml, folder structure, health endpoint)
- [x] Phase 2 — Document ingestion (PDF/TXT/OCR to chunking to embeddings to ChromaDB)
- [x] Phase 3 — LLM service + Explanation feature (RAG + Groq, plain-language output)
- [x] Phase 4 — RAG-based text Q&A (grounded generation, source chunk transparency)
- [x] Phase 5 — Quiz generation + evaluation (structured JSON output, MCQ scoring)
- [x] Phase 6 — Voice layer (Whisper STT + gTTS TTS, full voice Q&A pipeline)
- [x] Phase 7 — Polish (file validation, error handling, deployment config, README)

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| GROQ_API_KEY | required | Groq API key from console.groq.com |
| GROQ_MODEL | llama-3.3-70b-versatile | Groq model ID |
| CHROMA_DB_PATH | ./data/chroma_db | ChromaDB persistence directory |
| UPLOAD_DIR | ./data/uploads | Uploaded files directory |
| AUDIO_DIR | ./data/audio | TTS MP3 output directory |
| WHISPER_MODEL | base | Whisper model size (tiny/base/small) |
| EMBEDDING_MODEL | all-MiniLM-L6-v2 | SentenceTransformer model name |
| CHUNK_SIZE | 500 | Target tokens per chunk |
| CHUNK_OVERLAP | 50 | Overlap tokens between chunks |
| BACKEND_URL | http://127.0.0.1:8000 | Set on Streamlit if backend is remote |

---

## Screenshots

*(Add screenshots of each page after running the app)*

| Page | Screenshot |
|---|---|
| Home | home.png |
| Upload | upload.png |
| Explain | explain.png |
| Quiz | quiz.png |
| Voice Q&A | voice.png |

---

## Troubleshooting

**uvicorn is not recognized**
The venv is not activated. Run .venv\Scripts\activate on Windows first, then use uv run uvicorn.

**GROQ_API_KEY not set / 502 error from LLM**
Open backend/.env and paste your key from https://console.groq.com.

**Upload times out on first run**
The embedding model (~90 MB) is downloading. Wait 60 seconds and refresh — the document may already be indexed.

**Whisper build error about pkg_resources**
Run the one-time install: uv pip install wheel then uv pip install openai-whisper==20231117 --no-build-isolation

**No text could be extracted from the file**
For images, ensure Tesseract is installed and on PATH. For PDFs, check the file is not encrypted or image-only without OCR.

**File too large error**
Files must be under 50 MB. Split large PDFs into smaller sections before uploading.
