# ScholarAI - Autonomous Research Engineer

<div align="center">

![ScholarAI](https://img.shields.io/badge/ScholarAI-Research%20Assistant-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=flat-square&logo=typescript)

**An AI-powered research synthesis platform that extracts, analyzes, and synthesizes knowledge from academic documents.**

[Features](#features) • [Quick Start](#quick-start) • [API Documentation](#api-documentation) • [Architecture](#architecture)

</div>

---

## 🎯 What is ScholarAI?

ScholarAI is an **Autonomous Research Engineer** that helps researchers, students, and professionals synthesize knowledge from multiple documents. Unlike chatbots, ScholarAI provides structured research briefs that identify:

- **Areas of Consensus** - What sources agree on
- **Areas of Disagreement** - Conflicting findings and perspectives  
- **Open Questions** - Gaps in the literature that need further research

## ✨ Features

### Document Processing
- 📄 **Multi-format support**: PDF, DOCX, PPTX, images (PNG, JPG)
- 🔗 **URL processing**: Academic papers, web articles, arXiv links
- 🧠 **Intelligent chunking**: Semantic boundaries with configurable overlap
- 📊 **Metadata extraction**: Authors, dates, titles automatically detected

### RAG Pipeline
- 🔍 **Semantic search**: ChromaDB vector store with sentence transformers
- 🎯 **Query expansion**: Automatic synonym and concept expansion
- 📈 **Relevance scoring**: MMR-based re-ranking for diverse results

### Claim Extraction
- ✅ **Consensus detection**: Claims supported by multiple sources
- ⚡ **Disagreement identification**: Conflicting viewpoints highlighted
- ❓ **Uncertainty flagging**: Areas needing more research
- 🔗 **Source attribution**: Every claim linked to original sources

### Research Brief Synthesis
- 📋 **Structured output**: Organized sections for easy navigation
- 📊 **Confidence scoring**: Overall reliability assessment
- ⚠️ **Limitations noted**: Transparent about research gaps
- 📤 **Export ready**: Copy-to-clipboard functionality

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **OpenAI API Key** (for claim extraction and synthesis)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ScholarAI.git
cd ScholarAI
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Start the backend server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
# From project root
cd ..  # if you're in backend/

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Open the Application

Visit **http://localhost:5173** in your browser.

## 📖 Usage Guide

### Basic Workflow

1. **Enter Research Query**
   - Be specific: "What is the scientific consensus on exercise and depression?"
   - Include context: time periods, methodologies, populations

2. **Add Sources**
   - Upload PDF/DOCX files (up to 50MB each)
   - Add URLs to academic papers or articles
   - Recommended: 3-5 sources for comprehensive analysis

3. **Process Documents**
   - Click "Process & Synthesize"
   - Watch the pipeline progress through stages
   - Processing time depends on document length

4. **Review Results**
   - **Sources**: View processed documents and extraction stats
   - **Claims**: Filter by consensus/disagreement/uncertain
   - **Brief**: Read the synthesized research summary

### Tips for Best Results

- 📚 Include sources with **different perspectives** for richer disagreement analysis
- 🎯 Use **specific queries** rather than broad topics
- 📄 Academic papers (PDFs) typically yield **better results** than web pages
- 🔄 Process **related documents together** for cross-source analysis

## 🔧 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Health Check
```http
GET /health
```
Returns server status and version.

#### Upload Document
```http
POST /api/process-docs/upload
Content-Type: multipart/form-data

file: <binary>
```
Uploads a document for processing.

#### Process Documents
```http
POST /api/process-docs
Content-Type: application/json

{
  "document_ids": ["doc_001", "doc_002"],
  "urls": ["https://example.com/paper.pdf"],
  "query": "What are the effects of exercise on mental health?"
}
```
Processes documents through Docling and indexes them in the vector store.

#### Retrieve Chunks
```http
POST /api/retrieve-chunks
Content-Type: application/json

{
  "session_id": "sess_abc123",
  "query": "exercise depression",
  "top_k": 10
}
```
Retrieves relevant document chunks via semantic search.

#### Extract Claims
```http
POST /api/extract-claims
Content-Type: application/json

{
  "session_id": "sess_abc123",
  "query": "What are the effects of exercise on mental health?"
}
```
Extracts and classifies claims from retrieved content.

#### Synthesize Report
```http
POST /api/synthesize-report
Content-Type: application/json

{
  "session_id": "sess_abc123",
  "query": "What are the effects of exercise on mental health?"
}
```
Generates a comprehensive research brief.

### Sample Responses

See the `examples/` directory for complete sample responses:
- `sample_process_response.json`
- `sample_claims_response.json`
- `sample_brief_response.json`

## 🏗️ Architecture

```
ScholarAI/
├── backend/                 # FastAPI Backend
│   ├── api/
│   │   └── routes/          # API endpoint handlers
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── docling_service.py      # Document processing
│   │   ├── embedding_service.py    # Text embeddings
│   │   ├── vector_store.py         # ChromaDB operations
│   │   ├── claim_extractor.py      # LLM claim extraction
│   │   └── synthesizer.py          # Brief generation
│   ├── tests/               # Pytest test suite
│   ├── config.py            # Settings management
│   ├── main.py              # FastAPI application
│   └── requirements.txt
│
├── src/                     # React Frontend
│   ├── components/
│   │   ├── brief/           # Research brief display
│   │   ├── claims/          # Claims panel
│   │   ├── sources/         # Sources panel
│   │   ├── upload/          # Upload components
│   │   ├── layout/          # App layout
│   │   └── ui/              # shadcn/ui components
│   ├── hooks/
│   │   └── use-research.ts  # Zustand state management
│   ├── lib/
│   │   └── api.ts           # API client
│   └── pages/               # Route pages
│
├── examples/                # Sample documents & outputs
│   ├── sample_research_paper.md
│   ├── sample_meta_analysis.md
│   ├── sample_process_response.json
│   ├── sample_claims_response.json
│   └── sample_brief_response.json
│
└── public/                  # Static assets
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, shadcn/ui, Zustand |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2 |
| **Document Processing** | Docling, pypdf (fallback) |
| **Vector Store** | ChromaDB, sentence-transformers |
| **LLM** | OpenAI GPT-4 (claim extraction, synthesis) |

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│   Docling   │────▶│   Chunking  │
│  Documents  │     │  Processing │     │  & Embedding│
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Research   │◀────│    Claim    │◀────│   Vector    │
│    Brief    │     │  Extraction │     │   Search    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests

```bash
npm run test
```

### Test Coverage

```bash
# Backend
pytest tests/ --cov=. --cov-report=html

# Frontend
npm run test:coverage
```

## ⚙️ Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional - Defaults shown
UPLOAD_DIRECTORY=./data/uploads
PROCESSED_DIRECTORY=./data/processed
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_FILE_SIZE_MB=50
```

### Frontend Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Docling](https://github.com/DS4SD/docling) - Document processing
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework

---

<div align="center">

**Built with ❤️ for researchers everywhere**

</div>
