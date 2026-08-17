# AI-Powered Smart Lost & Found Management System

A B.Tech CSE Final Year Project featuring **Agentic AI** (LangGraph & LangChain), **FastAPI**, **SQLite / SQLAlchemy**, **React (Vite)**, and **Tailwind CSS**.

---

## Architecture

- **Backend Framework**: Python FastAPI
- **Database**: SQLite3 (via SQLAlchemy 2.0 ORM)
- **Security**: JWT Bearer Token Authentication + Bcrypt password hashing
- **Frontend Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS with Glassmorphism Theme
- **Agentic AI Framework**: LangGraph & LangChain
- **LLM Integrations**: Groq API (`llama-3.3-70b-versatile`) / IBM watsonx.ai fallback
- **Vector Embeddings**: Sentence-Transformers cosine similarity

---

## Project Structure

```text
smart-lost-found/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   └── item.py
│   │   ├── schemas/
│   │   │   └── auth.py
│   │   ├── routers/
│   │   │   └── auth.py
│   │   └── utils/
│   │       └── security.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
├── uploads/
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Environment Configuration

Copy `.env.example` to `.env` in the root folder:

```bash
cp .env.example .env
```

### 2. Backend Setup

From the project root:

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI server
python -m uvicorn app.main:app --reload --app-dir backend --port 8000
```

FastAPI interactive documentation will be available at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

In a new terminal window:

```bash
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend application will open at: `http://localhost:5173`

---

## Phase Execution Checklist

- [x] **Phase 1: Foundation** — SQLite DB, FastAPI server, JWT Auth, React Vite scaffold & Landing/Login pages.
- [ ] **Phase 2: Lost & Found System** — Form submission, upload handling, item feed & search.
- [ ] **Phase 3: AI Extraction Agent** — Groq / WatsonX parsing of unstructured report text.
- [ ] **Phase 4: Semantic Matching Engine** — Multi-factor embedding matching & similarity scoring.
- [ ] **Phase 5: Agentic LangGraph Workflow** — Verification question generation & evaluation agent.
- [ ] **Phase 6: Admin Dashboard** — Human-in-the-loop review, approve/reject & item recovery.
- [ ] **Phase 7: Final Polish & Demo Packaging** — End-to-end verification scenario.
