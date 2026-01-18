🧠 1. Project Identity

Project Name: ScholarAI
Tagline:
An autonomous research engineer that synthesizes knowledge from arbitrary documents and sources using advanced RAG workflows powered by Docling.

One-Sentence:
ScholarAI ingests unstructured documents, structures them via Docling, retrieves relevant content, extracts claims, and reasons to produce a structured research brief with consensus, disagreements, and open questions.

🧾 2. Motivation & Problem

Real research isn’t just Q&A — it requires:

parsing diverse documents (PDFs, Word, PPTs, images),

synthesizing knowledge across sources,

detecting contradictions,

identifying open problems.

ScholarAI solves this by combining:

Docling for document processing, and

RAG + structured reasoning for claim extraction and synthesis.

This transforms messy inputs into research-ready knowledge.

🏗 3. What ScholarAI IS and IS NOT
ScholarAI IS

✔ a RAG-driven research synthesis system
✔ document-agnostic (PDF/Word/PPTX/HTML/Images) via Docling
✔ claim-level reasoning, not surface summarization
✔ structured output with consensus / disagreement / open questions

ScholarAI IS NOT

❌ a chatbot
❌ a simple Q&A app
❌ a “black-box” LLM prompt wrapper
❌ a tool that blindly summarizes text

📊 4. High-Level Architecture
User Query
    ↓
Document Upload + URL input
    ↓
Docling Processor → Structured Docs (JSON/Markdown)
    ↓
Embedding + Vector Store (Chroma/Milvus)
    ↓
RAG Retriever
    ↓
Claim Extraction
    ↓
Claim Clustering (Graph)
    ↓
Reasoning & Synthesis
    ↓
Structured Research Brief


Key addition vs earlier spec: Docling sits at the very beginning to convert arbitrary documents into RAG-ready structured content.

📥 5. Inputs
5.1 User Inputs

Text research question

File uploads (PDF, DOCX, PPTX, images)

Document URLs

5.2 Docling Inputs

Docling must process all document types and generate a unified structured representation. This includes:

text segments

layouts

tables

images (OCR where needed)

🛠 6. Docling Integration (WHY and HOW)
6.1 WHY Docling

Docling is ideal because:

It supports many document formats in one tool

It preserves structure (tables, layout, metadata) which improves retrieval quality

It outputs structured formats (JSON/Markdown) ready for RAG

6.2 HOW Docling Works

Install docling

Use Docling API or CLI to convert documents

Store structured output in local storage / vector database

Chunk content for embedding + indexing

This forms the ground truth knowledge base for ScholarAI.

📚 7. Retrieval Augmented Generation (RAG)

Once Docling has converted documents to structured text:

Chunk documents using token split strategy

Embed chunks (e.g., using OpenAI / local embeddings)

Index in vector database (Chroma or Milvus)

Retrieve relevant chunks per user query

Docling ensures retrieval works over rich, structured representations instead of raw OCR text.

🧠 8. Claim Extraction

Transforms retrieved chunks into normalized claims:

{
  "id": "...",
  "text": "...",
  "source": "...",
  "confidence": "...",
  "scope": "...",
  "metadata": {...}
}


You should use LLMs with strict formatting and verification layers to avoid hallucination.

🧠 9. Claim Clustering & Reasoning

Group claims semantically (consensus vs disagreement)

Build a claim graph

Identify support patterns, contradictions, and under-explored areas

Reason over these to produce the research brief

No free-form chat allowed — output must be structured JSON.

📘 10. Outputs (Structured Research Brief)

Format:

{
  "query": "...",
  "sources": [...],
  "consensus": [...],
  "disagreements": [...],
  "openQuestions": [...],
  "confidence": "...",
  "limitations": [...]
}


Each section must include:

claim text

sources that support or contradict

explanation metadata

🎨 11. UI (Lovable)

The initial UI will be built using Lovable.

ScholarAI UI must include:

11.1 Upload & Query Screen

Query input

Document upload area

URL input

“Process & Synthesize” button

11.2 Sources Panel

Shows list of processed documents

Previews (page thumbnails, file name)

11.3 Claims Panel

Claim clusters

Tagging or filters

11.4 Research Brief Panel

Consensus points

Disagreements

Open questions

Confidence bar

No “chat bubble” UI — this is a research workspace.

Prompt i used to feed into Lovable:
"Generate a professional research dashboard UI for ScholarAI with the following screens:
1. Upload & Query Screen
   - Query input box
   - Document upload area supporting PDF, DOCX, PPTX, images
   - URL input field
   - “Process & Synthesize” button
2. Sources Panel
   - List of processed documents
   - Thumbnail previews and metadata
3. Claims Panel
   - Displays extracted claim clusters
   - Filters by consensus/disagreement/uncertain
4. Research Brief Panel
   - Consensus section
   - Disagreements section
   - Open questions section
   - Confidence/limitations indicators

UI should feel like a **research workspace**, not a chatbot. Show panel layout, navigation, and typical interactions. Use neutral professional styling. Labels and components should be clear for an AI research tool."


🧠 12. API Endpoints (Backend)
POST /api/process-docs
POST /api/retrieve-chunks
POST /api/extract-claims
POST /api/synthesize-report


Each returns strict JSON with schema validation.

⚠️ 13. Non-Goals

Not a conversational agent

Not a generic answer bot

Not real-time collaborative research editor

The goal is reasoned research briefs, not dialogue.

📊 14. Evaluation Criteria

ScholarAI is considered successful if:

✅ Users can upload arbitrary document types
✅ Docling structured output improves retrieval quality
✅ Claims reflect distinct ideas
✅ Synthesis reveals consensus, contradiction, gaps
✅ UI feels like a research workstation

🧠 Interview Framing

One-liner:
“ScholarAI ingests documents via Docling, synthesizes structured research insights using RAG, and produces organized briefs exposing agreement, disagreement, and open questions.”