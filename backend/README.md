# ScholarAI Backend

FastAPI backend for the ScholarAI autonomous research engineer.

## Setup

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

### 3. Configure Environment

Create a `.env` file in the backend directory:

```env
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional: Vector Store Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional: File Storage
UPLOAD_DIRECTORY=./data/uploads
PROCESSED_DIRECTORY=./data/processed
MAX_FILE_SIZE_MB=50

# Optional: Chunking
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

## API Endpoints

### POST /api/process-docs
Process uploaded documents through Docling and index them.

```json
{
  "document_ids": ["uuid-1", "uuid-2"],
  "urls": ["https://example.com/paper.pdf"],
  "query": "Research question here"
}
```

### POST /api/process-docs/upload
Upload a document file.

### POST /api/retrieve-chunks
Retrieve relevant chunks via semantic search.

```json
{
  "session_id": "session-uuid",
  "query": "Specific question",
  "top_k": 10
}
```

### POST /api/extract-claims
Extract structured claims from chunks.

```json
{
  "session_id": "session-uuid",
  "query": "Research question"
}
```

### POST /api/synthesize-report
Generate research brief from claims.

```json
{
  "session_id": "session-uuid",
  "query": "Research question"
}
```

## Architecture

```
backend/
├── main.py                 # FastAPI application
├── config.py               # Configuration management
├── api/
│   └── routes/
│       ├── documents.py    # /api/process-docs
│       ├── retrieval.py    # /api/retrieve-chunks
│       ├── claims.py       # /api/extract-claims
│       └── synthesis.py    # /api/synthesize-report
├── services/
│   ├── docling_service.py  # Docling document processing
│   ├── vector_store.py     # ChromaDB vector storage
│   ├── embedding_service.py # Sentence transformers
│   ├── claim_extractor.py  # LLM claim extraction
│   └── synthesizer.py      # Research brief synthesis
└── models/
    └── schemas.py          # Pydantic models
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Docling** - Document processing (PDF, DOCX, PPTX, images)
- **ChromaDB** - Vector database for RAG
- **Sentence Transformers** - Local embeddings
- **OpenAI** - LLM for claim extraction and synthesis
