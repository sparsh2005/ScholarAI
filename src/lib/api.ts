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
// API Error Class
// =============================================================================

export class APIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public retryable: boolean = false,
  ) {
    super(detail);
    this.name = 'APIError';
  }
}

// =============================================================================
// API Client with Retry Logic
// =============================================================================

interface RequestOptions extends RequestInit {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    retries = 2,
    retryDelay = 1000,
    timeout = 120000, // 2 minutes for long operations
    ...fetchOptions
  } = options;

  const url = `${API_BASE_URL}${endpoint}`;
  
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const isRetryable = response.status >= 500 || response.status === 429;
        throw new APIError(response.status, error.detail || 'Request failed', isRetryable);
      }

      return response.json();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry client errors or non-retryable errors
      if (error instanceof APIError && !error.retryable) {
        throw error;
      }
      
      // Don't retry on last attempt
      if (attempt < retries) {
        console.log(`Request failed, retrying in ${retryDelay}ms... (attempt ${attempt + 1}/${retries})`);
        await sleep(retryDelay * (attempt + 1)); // Exponential backoff
      }
    }
  }
  
  throw lastError || new Error('Request failed after retries');
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Check if backend is available.
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

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
    timeout: 300000, // 5 minutes for document processing
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
    timeout: 180000, // 3 minutes for LLM processing
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
    timeout: 180000, // 3 minutes for LLM processing
  });
}

/**
 * Get existing research brief for a session.
 */
export async function getResearchBrief(
  sessionId: string,
): Promise<{ session_id: string; brief: ResearchBrief }> {
  return apiRequest<{ session_id: string; brief: ResearchBrief }>(
    `/api/synthesize-report/${sessionId}`,
    { method: 'GET' }
  );
}

/**
 * Get claims for a session.
 */
export async function getSessionClaims(
  sessionId: string,
  claimType?: ClaimType,
): Promise<{ session_id: string; claims: Claim[]; total_claims: number }> {
  const params = claimType ? `?claim_type=${claimType}` : '';
  return apiRequest<{ session_id: string; claims: Claim[]; total_claims: number }>(
    `/api/extract-claims/${sessionId}${params}`,
    { method: 'GET' }
  );
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
  stage: 'idle' | 'uploading' | 'processing' | 'retrieving' | 'extracting' | 'synthesizing' | 'complete' | 'error';
  message: string;
  progress: number; // 0-100
  details?: string;
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
      details: `Processing ${documentIds.length} files and ${urls.length} URLs`,
    });

    const processResult = await processDocs({
      document_ids: documentIds,
      urls,
      query,
    });

    if (!processResult.success && processResult.errors.length > 0) {
      throw new Error(`Document processing failed: ${processResult.errors.join(', ')}`);
    }

    const sessionId = processResult.session_id;

    onProgress?.({
      stage: 'processing',
      message: 'Documents processed successfully',
      progress: 25,
      details: `Created ${processResult.total_chunks} chunks from ${processResult.sources.length} sources`,
    });

    // Stage 2: Retrieve relevant chunks
    onProgress?.({
      stage: 'retrieving',
      message: 'Finding relevant content...',
      progress: 35,
      details: 'Performing semantic search over document chunks',
    });

    const retrieveResult = await retrieveChunks({
      session_id: sessionId,
      query,
      top_k: 20,
    });

    onProgress?.({
      stage: 'retrieving',
      message: 'Retrieved relevant passages',
      progress: 45,
      details: `Found ${retrieveResult.total_results} relevant chunks`,
    });

    // Stage 3: Extract claims
    onProgress?.({
      stage: 'extracting',
      message: 'Extracting claims from sources...',
      progress: 55,
      details: 'Using LLM to identify factual claims',
    });

    const claimsResult = await extractClaims({
      session_id: sessionId,
      query,
    });

    onProgress?.({
      stage: 'extracting',
      message: 'Claims extracted and classified',
      progress: 70,
      details: `${claimsResult.consensus_count} consensus, ${claimsResult.disagreement_count} disagreements, ${claimsResult.uncertain_count} uncertain`,
    });

    // Stage 4: Synthesize report
    onProgress?.({
      stage: 'synthesizing',
      message: 'Generating research brief...',
      progress: 80,
      details: 'Synthesizing findings into structured brief',
    });

    const synthesisResult = await synthesizeReport({
      session_id: sessionId,
      query,
    });

    onProgress?.({
      stage: 'complete',
      message: 'Research brief ready!',
      progress: 100,
      details: `Generated in ${synthesisResult.processing_time_ms}ms`,
    });

    return synthesisResult.brief;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Pipeline failed';
    onProgress?.({
      stage: 'error',
      message: errorMessage,
      progress: 0,
      details: 'Please try again or check the backend logs',
    });
    throw error;
  }
}
