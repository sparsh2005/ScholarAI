/**
 * ScholarAI API Client
 *
 * Type-safe client for interacting with the FastAPI backend.
 * Handles document processing, retrieval, claim extraction, and synthesis.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// =============================================================================
// Types - Matching backend Pydantic schemas
// =============================================================================

export type SourceStatus = 'pending' | 'processing' | 'processed' | 'error';
export type ClaimType = 'consensus' | 'disagreement' | 'uncertain';
export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface Source {
  id: string;
  title: string;
  authors: string[];
  date: string | null;
  type: string;
  status: SourceStatus;
  claims_extracted: number;
  relevance_score: number;
  thumbnail_color: string;
}

export interface ProcessDocsRequest {
  document_ids: string[];
  urls: string[];
  query: string;
}

export interface ProcessDocsResponse {
  success: boolean;
  session_id: string;
  sources: Source[];
  total_chunks: number;
  processing_time_ms: number;
  errors: string[];
}

export interface RetrievedChunk {
  id: string;
  document_id: string;
  source_title: string;
  content: string;
  relevance_score: number;
  metadata: Record<string, unknown>;
}

export interface RetrieveChunksRequest {
  session_id: string;
  query: string;
  top_k?: number;
  filters?: Record<string, unknown>;
}

export interface RetrieveChunksResponse {
  success: boolean;
  query: string;
  chunks: RetrievedChunk[];
  total_results: number;
}

export interface Claim {
  id: string;
  statement: string;
  type: ClaimType;
  confidence: number;
  supporting_sources: number;
  contradicting_sources: number;
  source_ids: string[];
  evidence: string[];
  metadata: Record<string, unknown>;
}

export interface ExtractClaimsRequest {
  session_id: string;
  query: string;
  chunk_ids?: string[];
}

export interface ExtractClaimsResponse {
  success: boolean;
  query: string;
  claims: Claim[];
  total_claims: number;
  consensus_count: number;
  disagreement_count: number;
  uncertain_count: number;
}

export interface ConsensusItem {
  id: string;
  statement: string;
  confidence: number;
  sources: number;
  source_ids: string[];
  evidence_summary: string | null;
}

export interface DisagreementItem {
  id: string;
  claim: string;
  perspective1: string;
  perspective2: string;
  sources: number;
  source_ids: string[];
}

export interface OpenQuestion {
  id: string;
  question: string;
  context: string;
  related_claim_ids: string[];
}

export interface ResearchBrief {
  query: string;
  session_id: string;
  sources: Source[];
  consensus: ConsensusItem[];
  disagreements: DisagreementItem[];
  open_questions: OpenQuestion[];
  confidence_level: ConfidenceLevel;
  confidence_score: number;
  limitations: string[];
  generated_at: string;
}

export interface SynthesizeReportRequest {
  session_id: string;
  query: string;
  claim_ids?: string[];
}

export interface SynthesizeReportResponse {
  success: boolean;
  brief: ResearchBrief;
  processing_time_ms: number;
}

export interface UploadResponse {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
}

// =============================================================================
// API Client
// =============================================================================

class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = 'APIError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Upload a document file for processing.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/process-docs/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new APIError(response.status, error.detail);
  }

  return response.json();
}

/**
 * Process documents through Docling and index them.
 */
export async function processDocs(
  request: ProcessDocsRequest,
): Promise<ProcessDocsResponse> {
  return apiRequest<ProcessDocsResponse>('/api/process-docs', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Retrieve relevant chunks via semantic search.
 */
export async function retrieveChunks(
  request: RetrieveChunksRequest,
): Promise<RetrieveChunksResponse> {
  return apiRequest<RetrieveChunksResponse>('/api/retrieve-chunks', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Extract structured claims from retrieved chunks.
 */
export async function extractClaims(
  request: ExtractClaimsRequest,
): Promise<ExtractClaimsResponse> {
  return apiRequest<ExtractClaimsResponse>('/api/extract-claims', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Synthesize a research brief from extracted claims.
 */
export async function synthesizeReport(
  request: SynthesizeReportRequest,
): Promise<SynthesizeReportResponse> {
  return apiRequest<SynthesizeReportResponse>('/api/synthesize-report', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Health check endpoint.
 */
export async function healthCheck(): Promise<{ status: string }> {
  return apiRequest<{ status: string }>('/health');
}

// =============================================================================
// Full Pipeline Helper
// =============================================================================

export interface PipelineProgress {
  stage: 'uploading' | 'processing' | 'retrieving' | 'extracting' | 'synthesizing' | 'complete' | 'error';
  message: string;
  progress: number; // 0-100
}

export type PipelineProgressCallback = (progress: PipelineProgress) => void;

/**
 * Run the full research pipeline from documents to brief.
 */
export async function runResearchPipeline(
  query: string,
  documentIds: string[],
  urls: string[],
  onProgress?: PipelineProgressCallback,
): Promise<ResearchBrief> {
  try {
    // Stage 1: Process documents
    onProgress?.({
      stage: 'processing',
      message: 'Processing documents through Docling...',
      progress: 10,
    });

    const processResult = await processDocs({
      document_ids: documentIds,
      urls,
      query,
    });

    if (!processResult.success && processResult.errors.length > 0) {
      throw new Error(processResult.errors.join(', '));
    }

    const sessionId = processResult.session_id;

    // Stage 2: Retrieve relevant chunks
    onProgress?.({
      stage: 'retrieving',
      message: 'Finding relevant content...',
      progress: 35,
    });

    await retrieveChunks({
      session_id: sessionId,
      query,
      top_k: 20,
    });

    // Stage 3: Extract claims
    onProgress?.({
      stage: 'extracting',
      message: 'Extracting and classifying claims...',
      progress: 60,
    });

    await extractClaims({
      session_id: sessionId,
      query,
    });

    // Stage 4: Synthesize report
    onProgress?.({
      stage: 'synthesizing',
      message: 'Generating research brief...',
      progress: 85,
    });

    const synthesisResult = await synthesizeReport({
      session_id: sessionId,
      query,
    });

    onProgress?.({
      stage: 'complete',
      message: 'Research brief ready!',
      progress: 100,
    });

    return synthesisResult.brief;
  } catch (error) {
    onProgress?.({
      stage: 'error',
      message: error instanceof Error ? error.message : 'Pipeline failed',
      progress: 0,
    });
    throw error;
  }
}
