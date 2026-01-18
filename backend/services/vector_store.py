"""Vector store service using ChromaDB.

Handles document indexing, semantic search, and session management
for the RAG pipeline.
"""

import json
from pathlib import Path
from typing import Optional, Any

from models.schemas import (
    DocumentChunk,
    Source,
    Claim,
    ResearchBrief,
)
from services.embedding_service import EmbeddingService
from config import get_settings


class VectorStoreService:
    """Service for vector storage and retrieval using ChromaDB."""
    
    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self._client = None
        self._session_data: dict[str, dict] = {}  # In-memory session storage
    
    @property
    def client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        return self._client
    
    def _get_collection(self, session_id: str):
        """Get or create a collection for a session."""
        collection_name = f"session_{session_id.replace('-', '_')}"
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    async def index_chunks(
        self, 
        session_id: str, 
        chunks: list[DocumentChunk]
    ) -> int:
        """
        Index document chunks into the vector store.
        
        Args:
            session_id: Session identifier
            chunks: List of chunks to index
            
        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0
        
        collection = self._get_collection(session_id)
        
        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "source_title": chunk.metadata.get("source_title", ""),
                "authors": json.dumps(chunk.metadata.get("authors", [])),
                "date": chunk.metadata.get("date", ""),
            }
            for chunk in chunks
        ]
        
        # Generate embeddings
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
            self._session_data[session_id] = {"chunks": [], "sources": [], "claims": []}
        self._session_data[session_id]["chunks"].extend(chunks)
        
        return len(chunks)
    
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
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of retrieved chunks with relevance scores
        """
        collection = self._get_collection(session_id)
        
        # Embed query
        query_embedding = self.embedding_service.embed_text(query)
        
        # Build where clause from filters
        where = None
        if filters:
            where = filters
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        # Transform results
        retrieved = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity score (cosine distance to similarity)
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance  # For cosine distance
                
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                retrieved.append({
                    "id": chunk_id,
                    "document_id": metadata.get("document_id", ""),
                    "source_title": metadata.get("source_title", ""),
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "relevance_score": round(similarity * 100, 2),
                    "metadata": {
                        "authors": json.loads(metadata.get("authors", "[]")),
                        "date": metadata.get("date", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                    },
                })
        
        return retrieved
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        try:
            collection_name = f"session_{session_id.replace('-', '_')}"
            collections = self.client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False
    
    async def save_session_metadata(
        self,
        session_id: str,
        query: str,
        sources: list[Source],
    ) -> None:
        """Save session metadata."""
        if session_id not in self._session_data:
            self._session_data[session_id] = {"chunks": [], "sources": [], "claims": []}
        
        self._session_data[session_id]["query"] = query
        self._session_data[session_id]["sources"] = sources
    
    async def get_session_sources(self, session_id: str) -> list[Source]:
        """Get sources for a session."""
        if session_id in self._session_data:
            return self._session_data[session_id].get("sources", [])
        return []
    
    async def get_session_chunks(self, session_id: str) -> list[DocumentChunk]:
        """Get all chunks for a session."""
        if session_id in self._session_data:
            return self._session_data[session_id].get("chunks", [])
        return []
    
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
            self._session_data[session_id] = {"chunks": [], "sources": [], "claims": []}
        self._session_data[session_id]["claims"] = claims
    
    async def get_session_claims(self, session_id: str) -> list[Claim]:
        """Get claims for a session."""
        if session_id in self._session_data:
            return self._session_data[session_id].get("claims", [])
        return []
    
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
            self._session_data[session_id] = {"chunks": [], "sources": [], "claims": []}
        self._session_data[session_id]["brief"] = brief
    
    async def get_research_brief(
        self, 
        session_id: str
    ) -> Optional[ResearchBrief]:
        """Get research brief for a session."""
        if session_id in self._session_data:
            return self._session_data[session_id].get("brief")
        return None
