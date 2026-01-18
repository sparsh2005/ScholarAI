"""Vector store service using ChromaDB.

Handles document indexing, semantic search, and session management
for the RAG pipeline.

Features:
- Persistent vector storage with ChromaDB
- Session-based collection management
- Semantic similarity search
- Metadata filtering
- Session state management
"""

import json
import logging
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from models.schemas import (
    DocumentChunk,
    Source,
    Claim,
    ResearchBrief,
    ProcessedDocument,
)
from services.embedding_service import EmbeddingService
from config import get_settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector storage and retrieval using ChromaDB.
    
    Each research session gets its own ChromaDB collection,
    enabling isolation and easy cleanup. Session metadata
    is stored in-memory and persisted to disk.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self._client = None
        
        # Session data storage (in-memory with disk persistence)
        self._session_data: dict[str, dict] = {}
        self._session_file = Path(self.settings.chroma_persist_directory) / "sessions.json"
        self._load_sessions()
    
    @property
    def client(self):
        """Lazy-load ChromaDB client with persistent storage."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Ensure directory exists
            persist_dir = Path(self.settings.chroma_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
            logger.info(f"ChromaDB client initialized at {persist_dir}")
        
        return self._client
    
    def _get_collection_name(self, session_id: str) -> str:
        """Generate valid collection name from session ID."""
        # ChromaDB collection names must be 3-63 chars, alphanumeric with underscores
        clean_id = session_id.replace('-', '_')[:50]
        return f"session_{clean_id}"
    
    def _get_collection(self, session_id: str):
        """Get or create a collection for a session."""
        collection_name = self._get_collection_name(session_id)
        
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    async def index_chunks(
        self, 
        session_id: str, 
        chunks: list[DocumentChunk]
    ) -> list[str]:
        """
        Index document chunks into the vector store.
        
        Args:
            session_id: Session identifier for collection
            chunks: List of DocumentChunk objects to index
            
        Returns:
            List of chunk IDs that were indexed
        """
        if not chunks:
            return []
        
        collection = self._get_collection(session_id)
        
        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        
        # Prepare metadata (must be flat dict with primitive types)
        metadatas = []
        for chunk in chunks:
            meta = {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "source_title": chunk.metadata.get("source_title", ""),
                "authors": json.dumps(chunk.metadata.get("authors", [])),
                "date": chunk.metadata.get("date") or "",
                "section_title": chunk.metadata.get("section_title") or "",
                "file_type": chunk.metadata.get("file_type", ""),
            }
            metadatas.append(meta)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedding_service.embed_texts(documents)
        
        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        
        # Store chunks in session data
        if session_id not in self._session_data:
            self._session_data[session_id] = {
                "chunks": [],
                "sources": [],
                "claims": [],
                "processed_docs": [],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        # Store chunk data (without embeddings for memory efficiency)
        chunk_data = [
            {
                "id": c.id,
                "document_id": c.document_id,
                "content": c.content,
                "chunk_index": c.chunk_index,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        self._session_data[session_id]["chunks"].extend(chunk_data)
        self._save_sessions()
        
        logger.info(f"Indexed {len(chunks)} chunks for session {session_id}")
        
        return ids
    
    async def search(
        self,
        session_id: str,
        query: str,
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Perform semantic search for relevant chunks.
        
        Args:
            session_id: Session identifier
            query: Search query text
            top_k: Number of results to return (default: 10)
            filters: Optional metadata filters (e.g., {"document_id": "xyz"})
            
        Returns:
            List of retrieved chunks with relevance scores
        """
        collection = self._get_collection(session_id)
        
        # Embed query
        logger.info(f"Searching for: {query[:100]}...")
        query_embedding = self.embedding_service.embed_text(query)
        
        # Build where clause from filters
        where = None
        if filters:
            where = filters
        
        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),  # Don't request more than available
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        # Transform results
        retrieved = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity score
                # For cosine distance: similarity = 1 - distance
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = max(0, min(100, (1 - distance) * 100))  # Convert to 0-100 scale
                
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                # Parse authors from JSON string
                authors = []
                if metadata.get("authors"):
                    try:
                        authors = json.loads(metadata["authors"])
                    except json.JSONDecodeError:
                        authors = []
                
                retrieved.append({
                    "id": chunk_id,
                    "document_id": metadata.get("document_id", ""),
                    "source_title": metadata.get("source_title", ""),
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": round(similarity, 2),
                    "metadata": {
                        "authors": authors,
                        "date": metadata.get("date", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "section_title": metadata.get("section_title", ""),
                        "file_type": metadata.get("file_type", ""),
                    },
                })
        
        logger.info(f"Found {len(retrieved)} results for query")
        
        return retrieved
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._session_data
    
    async def save_session_metadata(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
        processed_docs: Optional[list[ProcessedDocument]] = None,
    ) -> None:
        """Save session metadata including sources and query."""
        if session_id not in self._session_data:
            self._session_data[session_id] = {
                "chunks": [],
                "sources": [],
                "claims": [],
                "processed_docs": [],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        self._session_data[session_id]["query"] = query
        
        # Convert Source objects to dicts for storage
        self._session_data[session_id]["sources"] = [
            s.model_dump() if hasattr(s, 'model_dump') else dict(s)
            for s in sources
        ]
        
        # Store processed doc metadata
        if processed_docs:
            self._session_data[session_id]["processed_docs"] = [
                {
                    "id": d.id,
                    "title": d.title,
                    "authors": d.authors,
                    "date": d.date,
                    "file_type": d.file_type,
                    "chunk_count": d.chunk_count,
                    "metadata": d.metadata,
                }
                for d in processed_docs
            ]
        
        self._save_sessions()
    
    async def get_session_sources(self, session_id: str) -> list[Source]:
        """Get sources for a session."""
        if session_id not in self._session_data:
            return []
        
        source_data = self._session_data[session_id].get("sources", [])
        
        # Convert back to Source objects
        sources = []
        for s in source_data:
            try:
                sources.append(Source(**s))
            except Exception as e:
                logger.warning(f"Error converting source: {e}")
        
        return sources
    
    async def get_session_chunks(self, session_id: str) -> list[DocumentChunk]:
        """Get all chunks for a session."""
        if session_id not in self._session_data:
            return []
        
        chunk_data = self._session_data[session_id].get("chunks", [])
        
        # Convert back to DocumentChunk objects
        chunks = []
        for c in chunk_data:
            try:
                chunks.append(DocumentChunk(**c))
            except Exception as e:
                logger.warning(f"Error converting chunk: {e}")
        
        return chunks
    
    async def get_chunks_by_ids(
        self, 
        session_id: str, 
        chunk_ids: list[str]
    ) -> list[DocumentChunk]:
        """Get specific chunks by ID."""
        all_chunks = await self.get_session_chunks(session_id)
        return [c for c in all_chunks if c.id in chunk_ids]
    
    async def save_session_claims(
        self, 
        session_id: str, 
        claims: list[Claim]
    ) -> None:
        """Save extracted claims for a session."""
        if session_id not in self._session_data:
            self._session_data[session_id] = {
                "chunks": [],
                "sources": [],
                "claims": [],
                "processed_docs": [],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        # Convert Claim objects to dicts
        self._session_data[session_id]["claims"] = [
            c.model_dump() if hasattr(c, 'model_dump') else dict(c)
            for c in claims
        ]
        
        # Update source claim counts
        source_claim_counts = {}
        for claim in claims:
            for source_id in claim.source_ids:
                source_claim_counts[source_id] = source_claim_counts.get(source_id, 0) + 1
        
        # Update sources with claim counts
        sources = self._session_data[session_id].get("sources", [])
        for source in sources:
            source_id = source.get("id")
            if source_id in source_claim_counts:
                source["claims_extracted"] = source_claim_counts[source_id]
        
        self._save_sessions()
    
    async def get_session_claims(self, session_id: str) -> list[Claim]:
        """Get claims for a session."""
        if session_id not in self._session_data:
            return []
        
        claim_data = self._session_data[session_id].get("claims", [])
        
        # Convert back to Claim objects
        claims = []
        for c in claim_data:
            try:
                claims.append(Claim(**c))
            except Exception as e:
                logger.warning(f"Error converting claim: {e}")
        
        return claims
    
    async def get_claims_by_ids(
        self, 
        session_id: str, 
        claim_ids: list[str]
    ) -> list[Claim]:
        """Get specific claims by ID."""
        all_claims = await self.get_session_claims(session_id)
        return [c for c in all_claims if c.id in claim_ids]
    
    async def save_research_brief(
        self, 
        session_id: str, 
        brief: ResearchBrief
    ) -> None:
        """Save generated research brief for a session."""
        if session_id not in self._session_data:
            self._session_data[session_id] = {
                "chunks": [],
                "sources": [],
                "claims": [],
                "processed_docs": [],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        self._session_data[session_id]["brief"] = (
            brief.model_dump() if hasattr(brief, 'model_dump') else dict(brief)
        )
        self._save_sessions()
    
    async def get_research_brief(
        self, 
        session_id: str
    ) -> Optional[ResearchBrief]:
        """Get research brief for a session."""
        if session_id not in self._session_data:
            return None
        
        brief_data = self._session_data[session_id].get("brief")
        if not brief_data:
            return None
        
        try:
            return ResearchBrief(**brief_data)
        except Exception as e:
            logger.warning(f"Error converting brief: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data."""
        try:
            # Delete ChromaDB collection
            collection_name = self._get_collection_name(session_id)
            try:
                self.client.delete_collection(collection_name)
            except Exception as e:
                logger.warning(f"Could not delete collection: {e}")
            
            # Delete session data
            if session_id in self._session_data:
                del self._session_data[session_id]
                self._save_sessions()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        try:
            if self._session_file.exists():
                with open(self._session_file, "r") as f:
                    self._session_data = json.load(f)
                logger.info(f"Loaded {len(self._session_data)} sessions from disk")
        except Exception as e:
            logger.warning(f"Could not load sessions: {e}")
            self._session_data = {}
    
    def _save_sessions(self) -> None:
        """Persist sessions to disk."""
        try:
            # Ensure directory exists
            self._session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._session_file, "w") as f:
                json.dump(self._session_data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save sessions: {e}")
