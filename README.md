# 📄 ResumeScore — AI-Powered Resume Intelligence Platform

> End-to-end resume screening and career preparation platform built with FastAPI + Streamlit.
> Combines a dual-provider LLM pipeline (Groq/Qwen 3.6 27B primary, NVIDIA/LLaMA 3.3 70B fallback) with TF-IDF cosine similarity to deliver 6 AI features across a production-grade three-tier architecture.

---

## 🚀 Features

| Feature | Endpoint | Description |
|--------|----------|-------------|
| 🔍 **Full Resume Analysis** | `POST /api/analysis/full` | ATS match score, strengths, gaps, and missing keywords vs. a job description |
| ✉️ **Cover Letter Generator** | `POST /api/cover-letter` | Tailored, company-specific cover letter drafted from resume + JD |
| 🎤 **Interview Prep Simulator** | `POST /api/interview-prep` | High-signal technical, behavioral, and resume-specific questions |
| 🗺️ **90-Day Career Roadmap** | `POST /api/roadmap` | Phased skill-gap plan with curated cross-sector resources |
| ⚖️ **AI Job Matching** | `POST /api/job-matcher` | Ranks multiple JDs by fit and provides deep analysis on the best match |
| 📋 **Batch Candidate Ranking** | `POST /api/batch-ranking` | Ranks up to 10 resumes against one JD — the recruiter-side view |

---

## 🏗️ Architecture

ResumeScore implements a strict **3-layer design** and a **Retriever-Reader cascade** for AI-heavy features:

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit Frontend (frontend/app.py)                       │
│  Plotly gauge charts · Expandable question cards · Tabs     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (multipart/form-data)
┌────────────────────────▼────────────────────────────────────┐
│  FastAPI Backend (backend/)                                 │
│                                                             │
│  Layer 1 — Routers (6 files)                                │
│  · Thin HTTP handlers: validate input, return responses     │
│  · Shared PDF dependency via FastAPI Depends()              │
│  · Global exception handlers: ValueError→422, Runtime→502   │
│                                                             │
│  Layer 2 — Services (domain logic per feature)              │
│  · Pydantic v2 schemas as strict data contracts             │
│  · Nested model validation for complex AI outputs           │
│                                                             │
│  Layer 3 — Shared Infrastructure                            │
│  · ai_client.py: dual-provider failover + JSON cleaning     │
│  · scorer.py: TF-IDF vectorization + cosine similarity      │
│  · pdf_parser.py: pdfplumber text extraction                │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  Groq API — PRIMARY (qwen/qwen3.6-27b)                      │
│  LPU hardware · ~2-5s typical · non-thinking mode           │
└────────────────────────┬────────────────────────────────────┘
                         │ on failure/timeout, falls back to
┌────────────────────────▼────────────────────────────────────┐
│  NVIDIA API — FALLBACK (meta/llama-3.3-70b-instruct)        │
│  OpenAI-compatible endpoint · Async httpx · 120s timeout    │
└─────────────────────────────────────────────────────────────┘
```

**Retriever-Reader Cascade** (Sections 5 & 6): TF-IDF scores all candidates/jobs instantly (local, free). The LLM runs deep analysis only on the top result — avoiding N redundant AI calls and cutting response time significantly.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | FastAPI 0.111, REST API design (semantic HTTP status codes, multipart/form-data), Python 3.11, Pydantic v2, uvicorn |
| **Frontend** | Streamlit 1.38, Plotly 5.22 |
| **AI Provider** | Dual-provider failover: Groq → `qwen/qwen3.6-27b` (primary) · NVIDIA → `meta/llama-3.3-70b-instruct` (fallback) |
| **NLP / Scoring** | scikit-learn 1.5 (TF-IDF + cosine similarity), NumPy 1.26 |
| **PDF Parsing** | pdfplumber 0.11 |
| **HTTP Client** | httpx 0.27 (async) |
| **Config** | python-dotenv |

---

## 📁 Project Structure

```
ResumeScore/
│
├── README.md
├── requirements.txt          # Pinned versions — no broken deployments
├── .env.example              # Template — copy to .env and fill in keys
├── .gitignore
│
├── backend/
│   ├── main.py               # FastAPI app init, CORS, global exception handlers, router registration
│   ├── dependencies.py       # Shared PDF validation via FastAPI Depends()
│   │
│   ├── routers/              # Layer 1 — thin HTTP handlers
│   │   ├── __init__.py
│   │   ├── analysis.py       # POST /api/analysis/full
│   │   ├── cover_letter.py   # POST /api/cover-letter
│   │   ├── interview.py      # POST /api/interview-prep
│   │   ├── roadmap.py        # POST /api/roadmap
│   │   ├── job_matcher.py    # POST /api/job-matcher
│   │   └── batch_ranking.py  # POST /api/batch-ranking
│   │
│   └── services/             # Layer 2 & 3 — domain logic + shared infrastructure
│       ├── __init__.py
│       ├── ai_client.py               # Dual-provider AI client: Groq primary, NVIDIA fallback (call_and_validate)
│       ├── pdf_parser.py              # pdfplumber text extraction
│       ├── scorer.py                  # TF-IDF cosine similarity engine
│       ├── ai_analyzer.py             # Resume analysis domain service
│       ├── cover_letter_generator.py  # Cover letter domain service
│       ├── interview_generator.py     # Interview questions domain service
│       ├── roadmap_generator.py       # Career roadmap domain service
│       ├── job_matcher.py             # Job matching domain service
│       └── batch_ranker.py            # Batch candidate ranking domain service
│
└── frontend/
    └── app.py                # Streamlit multi-tab UI
```

---

## ⚙️ Setup & Run

### 1. Clone and install dependencies
```bash
git clone https://github.com/ankithudda/resumescore.git
cd resumescore
pip install -r requirements.txt
```

### 2. Configure environment variables
```bash
cp .env.example .env
# Open .env and add both API keys
# Groq (primary):    https://console.groq.com
# NVIDIA (fallback):  https://build.nvidia.com
```

### 3. Start the backend
```bash
python -m uvicorn backend.main:app --reload --reload-dir backend
# Interactive API docs at: http://localhost:8000/docs
```

### 4. Start the frontend (new terminal)
```bash
streamlit run frontend/app.py
# App opens at: http://localhost:8501
```

---

## 🔑 Environment Variables

```bash
# .env
GROQ_API_KEY=gsk_your-key-here
NVIDIA_API_KEY=nvapi-your-key-here
ALLOWED_ORIGINS='["http://localhost:8501", "http://127.0.0.1:8501"]'
LOG_LEVEL=INFO
```

All variables are documented in `.env.example`. Never commit `.env` to version control.

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| AI-powered endpoints | 6 |
| Supported resume formats | PDF (text-based) |
| Max batch ranking size | 10 resumes |
| AI model context window | 128K tokens |
| TF-IDF n-gram range | Unigrams + bigrams (1,2) |
| Score boost multiplier | 3.5× (capped at 98.5) |
| Primary provider response time (Groq) | ~2-5 seconds typical |
| AI call timeout (NVIDIA fallback) | 120 seconds |
| Batch AI analysis depth | Top 5 candidates |

---

## 🧠 Key Architecture Decisions

| Decision | Reasoning |
|----------|-----------|
| **3-layer design** (Router → Service → Infrastructure) | Separation of concerns — routers handle HTTP, services own domain logic, `ai_client.py` owns all AI provider communication (Groq + NVIDIA). Each layer is independently testable. |
| **`call_and_validate()` in `ai_client.py`** | Centralizes LLM call + JSON cleaning + Pydantic validation in one function. Eliminates per-service try/except boilerplate across all 6 features. |
| **Pydantic v2 schemas as data contracts** | Every AI response is validated against a strict schema including nested models. If the LLM returns a malformed structure, the error is caught and handled before it reaches the frontend. |
| **FastAPI `Depends()` for PDF validation** | `valid_pdf_text` in `dependencies.py` is injected into all relevant routers, eliminating repeated validation code per endpoint. |
| **Global exception handlers** | `ValueError → 422`, `RuntimeError → 502`, `Exception → 500` handled once in `main.py` — routers stay thin with no redundant try/except blocks. |
| **Retriever-Reader cascade** | TF-IDF scores all candidates/jobs cheaply (local, instant). LLM analysis runs only on the top result — avoids N redundant API calls at exactly the scale where cost matters. |
| **`raw_similarity` vs `match_score`** | `match_score` (boosted ×3.5, capped 98.5) is UX-friendly for display but saturates above ~28% raw similarity. `raw_similarity` (unboosted) is used as the sort key to preserve correct relative ordering in ranking features. |
| **Async `httpx`** | Non-blocking AI API calls — server stays responsive to other requests while waiting for AI responses under concurrent load. |
| **Dual-provider failover** (Groq primary, NVIDIA fallback) | NVIDIA's free tier showed ~50% request failure and 20–120s latency variance under real load testing. `call_and_validate()` tries Groq (`qwen/qwen3.6-27b`, LPU hardware, ~2–5s typical) first; only falls back to NVIDIA if Groq fails. Zero changes required in any router or service file — all 6 features funnel through this single function. |

---

## 🔜 Planned Improvements

- [ ] Deploy backend to Railway / Render
- [ ] Deploy frontend to Streamlit Cloud
- [x] Add rate limiting via `slowapi`
- [x] Add secondary AI provider (Groq/Qwen 3.6 27B) for failover + speed
- [ ] Add resume scoring history (SQLite)
- [ ] Add API key authentication for multi-user deployment
- [x] Duplicate filename handling in batch ranking
- [ ] *...and more ideas currently in the pipeline!*

---

## 🔗 Links

- **LinkedIn:** [linkedin.com/in/ankithudda](https://linkedin.com/in/ankithudda)
- **Groq API:** [console.groq.com](https://console.groq.com)
- **NVIDIA API:** [build.nvidia.com](https://build.nvidia.com)

---

*Built by [Ankit Hudda] | B.Tech CSE*