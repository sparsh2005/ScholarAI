# ScholarAI Backend

FastAPI backend for the ScholarAI research synthesis platform.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start server
uvicorn main:app --reload --port 8000
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for LLM operations |
| `UPLOAD_DIRECTORY` | No | `./data/uploads` | Directory for uploaded files |
| `PROCESSED_DIRECTORY` | No | `./data/processed` | Directory for processed documents |
| `CHROMA_PERSIST_DIRECTORY` | No | `./data/chroma` | ChromaDB persistence directory |
| `CHUNK_SIZE` | No | `1000` | Maximum chunk size in characters |
| `CHUNK_OVERLAP` | No | `200` | Overlap between chunks |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum upload file size |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/process-docs/upload` | Upload a document |
| POST | `/api/process-docs` | Process documents |
| GET | `/api/process-docs/status/{session_id}` | Get processing status |
| POST | `/api/retrieve-chunks` | Retrieve relevant chunks |
| POST | `/api/extract-claims` | Extract claims from content |
| GET | `/api/extract-claims/{session_id}` | Get session claims |
| POST | `/api/synthesize-report` | Generate research brief |
| GET | `/api/synthesize-report/{session_id}` | Get existing brief |

## Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── documents.py      # Document upload/processing
│       ├── retrieval.py      # Chunk retrieval
│       ├── claims.py         # Claim extraction
│       └── synthesis.py      # Brief synthesis
├── models/
│   ├── __init__.py
│   └── schemas.py            # Pydantic models
├── services/
│   ├── __init__.py
│   ├── docling_service.py    # Document processing
│   ├── embedding_service.py  # Text embeddings
│   ├── vector_store.py       # ChromaDB operations
│   ├── claim_extractor.py    # LLM claim extraction
│   └── synthesizer.py        # Brief generation
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures
│   ├── test_documents.py
│   ├── test_retrieval.py
│   ├── test_claims.py
│   ├── test_synthesis.py
│   └── test_health.py
├── config.py                 # Settings management
├── main.py                   # FastAPI application
├── requirements.txt
├── pytest.ini
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_documents.py -v

# Run tests matching a pattern
pytest -k "test_upload" -v
```

## Development

### Adding a New Endpoint

1. Create or update route file in `api/routes/`
2. Add Pydantic schemas in `models/schemas.py`
3. Implement service logic in `services/`
4. Register route in `main.py`
5. Add tests in `tests/`

### Code Style

- Use type hints for all functions
- Follow PEP 8 guidelines
- Document functions with docstrings
- Use async/await for I/O operations

## Troubleshooting

### Docling Installation Issues

If Docling fails to install, the backend includes a fallback PDF processor using pypdf:

```bash
pip install pypdf
```

### ChromaDB Persistence

If you encounter ChromaDB errors, try clearing the persistence directory:

```bash
rm -rf ./data/chroma
```

### Memory Issues with Large Documents

For large documents, consider:
- Reducing `CHUNK_SIZE` 
- Processing fewer documents at once
- Using a smaller embedding model

## API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
