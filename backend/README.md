# ScholarAI Backend

FastAPI backend for the ScholarAI autonomous research engineer.

## 📋 Overview

The backend handles the complete document processing pipeline:

1. **Document Ingestion** - Accept uploads (PDF, DOCX, PPTX, images) and URLs
2. **Docling Processing** - Convert to structured Markdown/JSON
3. **Chunking** - Semantic splitting with overlap
4. **Embedding** - Generate vectors with sentence-transformers
5. **Indexing** - Store in ChromaDB for RAG retrieval
6. **Claim Extraction** - LLM-powered claim identification
7. **Synthesis** - Generate structured research briefs

## 🚀 Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: Docling installation may take a few minutes as it downloads ML models.

### 3. Configure Environment

Create a `.env` file in the backend directory:

```env
# Required: OpenAI API Key for claim extraction and synthesis
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional: Vector Store Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: File Storage
UPLOAD_DIRECTORY=./data/uploads
PROCESSED_DIRECTORY=./data/processed
MAX_FILE_SIZE_MB=50

# Optional: Chunking Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Or run directly
python main.py
```

The server starts at http://localhost:8000

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📡 API Endpoints

### Document Processing

#### `POST /api/process-docs/upload`
Upload a document file for processing.

**Request**: `multipart/form-data` with `file` field

**Supported formats**:
- PDF (`application/pdf`)
- DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
- PPTX (`application/vnd.openxmlformats-officedocument.presentationml.presentation`)
- PNG (`image/png`)
- JPG (`image/jpeg`)

**Response**:
```json
{
  "id": "uuid-string",
  "filename": "paper.pdf",
  "file_type": "pdf",
  "file_size": 1234567,
  "upload_path": "data/uploads/uuid.pdf"
}
```

#### `POST /api/process-docs`
Process uploaded documents through Docling and index them.

**Request**:
```json
{
  "document_ids": ["uuid-1", "uuid-2"],
  "urls": ["https://arxiv.org/pdf/1234.5678.pdf"],
  "query": "What is the relationship between X and Y?"
}
```

**Response**:
```json
{
  "success": true,
  "session_id": "session-uuid",
  "sources": [
    {
      "id": "uuid-1",
      "title": "Document Title",
      "authors": ["Author 1", "Author 2"],
      "date": "2024",
      "type": "pdf",
      "status": "processed",
      "claims_extracted": 0,
      "relevance_score": 0,
      "thumbnail_color": "hsl(210, 70%, 55%)"
    }
  ],
  "total_chunks": 42,
  "processing_time_ms": 3500,
  "errors": []
}
```

### Retrieval

#### `POST /api/retrieve-chunks`
Retrieve relevant chunks via semantic search.

**Request**:
```json
{
  "session_id": "session-uuid",
  "query": "Specific question about the documents",
  "top_k": 10
}
```

### Claim Extraction

#### `POST /api/extract-claims`
Extract structured claims from retrieved chunks.

**Request**:
```json
{
  "session_id": "session-uuid",
  "query": "Research question"
}
```

### Synthesis

#### `POST /api/synthesize-report`
Generate a structured research brief.

**Request**:
```json
{
  "session_id": "session-uuid",
  "query": "Research question"
}
```

## 🏗️ Architecture

```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management (Pydantic settings)
├── requirements.txt           # Python dependencies
│
├── api/
│   └── routes/
│       ├── documents.py       # /api/process-docs endpoints
│       ├── retrieval.py       # /api/retrieve-chunks endpoint
│       ├── claims.py          # /api/extract-claims endpoint
│       └── synthesis.py       # /api/synthesize-report endpoint
│
├── services/
│   ├── docling_service.py     # Docling document processing
│   │   ├── process_document() - Convert uploaded files
│   │   ├── process_url()      - Fetch and convert URLs
│   │   └── chunk_document()   - Semantic chunking
│   │
│   ├── vector_store.py        # ChromaDB operations
│   │   ├── index_chunks()     - Store embeddings
│   │   ├── search()           - Semantic search
│   │   └── Session management
│   │
│   ├── embedding_service.py   # Sentence transformers
│   │   ├── embed_text()       - Single text
│   │   └── embed_texts()      - Batch embedding
│   │
│   ├── claim_extractor.py     # LLM claim extraction
│   │   ├── extract_claims()   - Extract from chunks
│   │   └── classify_claims()  - Consensus/disagreement
│   │
│   └── synthesizer.py         # Research brief generation
│       └── synthesize()       - Full brief generation
│
└── models/
    └── schemas.py             # Pydantic models for API contracts
```

## 🔧 Docling Integration

### What Docling Does

Docling is a document conversion library that:

- **Parses multiple formats**: PDF, DOCX, PPTX, HTML, images
- **Extracts structure**: Headings, paragraphs, tables, figures
- **Performs OCR**: For scanned documents and images
- **Preserves layout**: Maintains document organization
- **Outputs Markdown/JSON**: RAG-ready structured text

### Document Processing Pipeline

```
Input Document
     ↓
┌─────────────────────────────────────┐
│           Docling Converter          │
│  - Layout analysis                   │
│  - Text extraction                   │
│  - Table detection                   │
│  - OCR (if needed)                   │
│  - Metadata extraction               │
└─────────────────────────────────────┘
     ↓
Structured Markdown + JSON
     ↓
┌─────────────────────────────────────┐
│         Semantic Chunker             │
│  - Split by sections                 │
│  - Respect sentence boundaries       │
│  - Apply overlap for context         │
└─────────────────────────────────────┘
     ↓
Document Chunks (512 chars each)
     ↓
┌─────────────────────────────────────┐
│       Embedding Service              │
│  - sentence-transformers             │
│  - all-MiniLM-L6-v2 (384 dims)      │
└─────────────────────────────────────┘
     ↓
Vector Embeddings
     ↓
┌─────────────────────────────────────┐
│           ChromaDB                   │
│  - Persistent storage                │
│  - Cosine similarity search          │
│  - Metadata filtering                │
└─────────────────────────────────────┘
```

### Fallback Mode

If Docling is unavailable, the service falls back to:
- `pypdf` for PDF text extraction
- Basic HTML parsing for web pages
- Raw text reading for text files

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## 📊 Data Storage

```
data/
├── uploads/           # Temporary upload storage
│   └── {uuid}.pdf
├── processed/         # Processed markdown/JSON
│   ├── {uuid}.md
│   └── {uuid}.json
└── chroma/           # Vector database
    ├── chroma.sqlite3
    └── sessions.json  # Session metadata
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for LLM |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for claim extraction |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model |
| `CHUNK_SIZE` | No | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | No | `50` | Overlap between chunks |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum upload size |

## 🐛 Troubleshooting

### Docling Installation Issues

If Docling fails to install:
```bash
# Try installing with specific extras
pip install "docling[all]"

# Or install without ML models for faster setup
pip install docling --no-deps
pip install docling-core docling-parse
```

### ChromaDB Errors

If ChromaDB throws errors about collections:
```bash
# Reset the database (deletes all data!)
rm -rf data/chroma
```

### Memory Issues

For large documents, increase chunk overlap:
```env
CHUNK_SIZE=256
CHUNK_OVERLAP=25
```
