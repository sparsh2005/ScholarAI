# 🧠 ScholarAI

> An autonomous research engineer that synthesizes knowledge from arbitrary documents using advanced RAG workflows powered by Docling.

**One-liner:** ScholarAI ingests documents via Docling, synthesizes structured research insights using RAG, and produces organized briefs exposing agreement, disagreement, and open questions.

## 🎯 What ScholarAI Does

Real research isn't just Q&A — it requires:
- Parsing diverse documents (PDFs, Word, PPTs, images)
- Synthesizing knowledge across sources
- Detecting contradictions
- Identifying open problems

ScholarAI transforms messy inputs into research-ready knowledge.

## ✨ Features

- **Document-agnostic ingestion** - PDF, DOCX, PPTX, images via Docling
- **RAG-powered retrieval** - Semantic search with ChromaDB
- **Claim-level reasoning** - Not surface summarization
- **Structured output** - Consensus, disagreements, open questions
- **Research workspace UI** - Not a chatbot

## 🏗️ Architecture

```
User Query
    ↓
Document Upload + URL input
    ↓
Docling Processor → Structured Docs (Markdown)
    ↓
Embedding + Vector Store (ChromaDB)
    ↓
RAG Retriever
    ↓
Claim Extraction (LLM)
    ↓
Claim Clustering & Classification
    ↓
Reasoning & Synthesis (LLM)
    ↓
Structured Research Brief
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/bun
- Python 3.10+
- OpenAI API key

### 1. Clone and Install Frontend

```bash
cd ScholarAI
npm install
# or
bun install
```

### 2. Set Up Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 4. Run Both Services

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
# or
bun dev
```

Open http://localhost:5173

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/process-docs` | POST | Process documents through Docling |
| `/api/process-docs/upload` | POST | Upload a document file |
| `/api/retrieve-chunks` | POST | Retrieve relevant chunks via RAG |
| `/api/extract-claims` | POST | Extract structured claims |
| `/api/synthesize-report` | POST | Generate research brief |

## 🖥️ UI Screens

1. **Upload & Query** - Add documents, URLs, and research question
2. **Sources Panel** - View processed documents and metadata
3. **Claims Panel** - Explore extracted claims by consensus level
4. **Research Brief** - Synthesized findings with confidence indicators

## 🛠️ Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite
- TailwindCSS + shadcn/ui
- Zustand (state management)
- React Query

**Backend:**
- FastAPI
- Docling (document processing)
- ChromaDB (vector store)
- Sentence Transformers (embeddings)
- OpenAI GPT-4o-mini (LLM)

## 📊 Output Format

```json
{
  "query": "Research question",
  "sources": [...],
  "consensus": [
    {
      "statement": "...",
      "confidence": 95,
      "sources": 4
    }
  ],
  "disagreements": [
    {
      "claim": "...",
      "perspective1": "...",
      "perspective2": "..."
    }
  ],
  "open_questions": [
    {
      "question": "...",
      "context": "..."
    }
  ],
  "confidence_level": "high|medium|low",
  "limitations": [...]
}
```

## 🎓 Interview Framing

> "ScholarAI ingests documents via Docling, synthesizes structured research insights using RAG, and produces organized briefs exposing agreement, disagreement, and open questions."

This project demonstrates:
- Full-stack development (React + FastAPI)
- AI/ML integration (RAG, embeddings, LLMs)
- Complex system design (document processing pipeline)
- Modern engineering practices (TypeScript, async Python)

## ⚠️ What ScholarAI is NOT

- ❌ A chatbot
- ❌ A simple Q&A app
- ❌ A "black-box" LLM prompt wrapper
- ❌ A tool that blindly summarizes text

---

Built for demonstrating autonomous research synthesis capabilities.
