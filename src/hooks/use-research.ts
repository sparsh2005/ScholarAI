/**
 * Research Pipeline Hook
 *
 * Central state management for the ScholarAI research workflow.
 * Manages document uploads, processing, and research brief generation.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  uploadDocument,
  runResearchPipeline,
  checkBackendHealth,
  type Source,
  type Claim,
  type ResearchBrief,
  type PipelineProgress,
  type UploadResponse,
  APIError,
} from '@/lib/api';

// =============================================================================
// Types
// =============================================================================

export interface UploadedFile {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedAt: Date;
  status: 'uploading' | 'uploaded' | 'error';
  error?: string;
}

export interface AddedUrl {
  id: string;
  url: string;
  title?: string;
}

export interface ResearchState {
  // Backend status
  backendAvailable: boolean;
  checkBackend: () => Promise<void>;

  // Query
  query: string;
  setQuery: (query: string) => void;

  // Uploaded files
  files: UploadedFile[];
  addFile: (file: File) => Promise<void>;
  removeFile: (id: string) => void;
  isUploading: boolean;

  // URLs
  urls: AddedUrl[];
  addUrl: (url: string) => void;
  removeUrl: (id: string) => void;

  // Processing state
  isProcessing: boolean;
  progress: PipelineProgress | null;

  // Results
  sessionId: string | null;
  sources: Source[];
  claims: Claim[];
  brief: ResearchBrief | null;

  // Actions
  startResearch: () => Promise<void>;
  reset: () => void;

  // Error handling
  error: string | null;
  clearError: () => void;
}

// =============================================================================
// Helper Functions
// =============================================================================

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function inferUrlTitle(url: string): string {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    
    if (hostname.includes('pubmed')) return 'PubMed Article';
    if (hostname.includes('arxiv')) return 'arXiv Paper';
    if (hostname.includes('nature')) return 'Nature Article';
    if (hostname.includes('sciencedirect')) return 'ScienceDirect';
    if (hostname.includes('springer')) return 'Springer Article';
    if (hostname.includes('wiley')) return 'Wiley Article';
    if (hostname.includes('ieee')) return 'IEEE Paper';
    if (hostname.includes('acm')) return 'ACM Paper';
    if (hostname.includes('biorxiv')) return 'bioRxiv Preprint';
    if (hostname.includes('medrxiv')) return 'medRxiv Preprint';
    if (hostname.includes('github')) return 'GitHub Repository';
    if (hostname.includes('wikipedia')) return 'Wikipedia Article';
    
    // Use hostname as fallback
    return hostname.replace('www.', '');
  } catch {
    return 'Web Page';
  }
}

// =============================================================================
// Store
// =============================================================================

export const useResearch = create<ResearchState>()(
  persist(
    (set, get) => ({
      // Backend status
      backendAvailable: true, // Assume available initially
      checkBackend: async () => {
        const available = await checkBackendHealth();
        set({ backendAvailable: available });
        if (!available) {
          set({ error: 'Backend server is not available. Please start the backend server.' });
        }
      },

      // Query
      query: '',
      setQuery: (query) => set({ query, error: null }),

      // Files
      files: [],
      isUploading: false,
      
      addFile: async (file: File) => {
        const tempId = `temp_${Date.now()}`;
        
        // Add file with uploading status
        set((state) => ({
          files: [...state.files, {
            id: tempId,
            name: file.name,
            type: file.name.split('.').pop()?.toLowerCase() || 'unknown',
            size: formatFileSize(file.size),
            uploadedAt: new Date(),
            status: 'uploading' as const,
          }],
          isUploading: true,
          error: null,
        }));

        try {
          const response: UploadResponse = await uploadDocument(file);

          // Update file with real ID and uploaded status
          set((state) => ({
            files: state.files.map((f) =>
              f.id === tempId
                ? {
                    ...f,
                    id: response.id,
                    status: 'uploaded' as const,
                  }
                : f
            ),
            isUploading: false,
          }));
        } catch (error) {
          const errorMessage = error instanceof APIError 
            ? error.detail 
            : error instanceof Error 
              ? error.message 
              : 'Failed to upload file';

          // Update file with error status or remove it
          set((state) => ({
            files: state.files.map((f) =>
              f.id === tempId
                ? { ...f, status: 'error' as const, error: errorMessage }
                : f
            ),
            isUploading: false,
            error: errorMessage,
          }));
          
          throw error;
        }
      },
      
      removeFile: (id) =>
        set((state) => ({
          files: state.files.filter((f) => f.id !== id),
        })),

      // URLs
      urls: [],
      addUrl: (url) => {
        // Validate URL
        try {
          new URL(url);
        } catch {
          set({ error: 'Please enter a valid URL' });
          return;
        }

        const id = Date.now().toString();
        const title = inferUrlTitle(url);

        set((state) => ({
          urls: [...state.urls, { id, url, title }],
          error: null,
        }));
      },
      
      removeUrl: (id) =>
        set((state) => ({
          urls: state.urls.filter((u) => u.id !== id),
        })),

      // Processing
      isProcessing: false,
      progress: null,

      // Results
      sessionId: null,
      sources: [],
      claims: [],
      brief: null,

      // Actions
      startResearch: async () => {
        const { query, files, urls, backendAvailable } = get();

        // Validation
        if (!backendAvailable) {
          set({ error: 'Backend server is not available. Please start the backend.' });
          return;
        }

        if (!query.trim()) {
          set({ error: 'Please enter a research question' });
          return;
        }

        const uploadedFiles = files.filter(f => f.status === 'uploaded');
        if (uploadedFiles.length === 0 && urls.length === 0) {
          set({ error: 'Please add at least one document or URL' });
          return;
        }

        set({
          isProcessing: true,
          error: null,
          progress: {
            stage: 'processing',
            message: 'Starting research pipeline...',
            progress: 5,
          },
          // Clear previous results
          brief: null,
          sources: [],
          claims: [],
        });

        try {
          const brief = await runResearchPipeline(
            query,
            uploadedFiles.map((f) => f.id),
            urls.map((u) => u.url),
            (progress) => set({ progress }),
          );

          // Extract claims from brief for display
          const extractedClaims: Claim[] = [
            ...brief.consensus.map((c) => ({
              id: c.id,
              statement: c.statement,
              type: 'consensus' as const,
              confidence: c.confidence,
              supporting_sources: c.sources,
              contradicting_sources: 0,
              source_ids: c.source_ids || [],
              evidence: c.evidence_summary ? [c.evidence_summary] : [],
              metadata: {},
            })),
            ...brief.disagreements.map((d) => ({
              id: d.id,
              statement: d.claim,
              type: 'disagreement' as const,
              confidence: 50,
              supporting_sources: Math.ceil(d.sources / 2),
              contradicting_sources: Math.floor(d.sources / 2),
              source_ids: d.source_ids || [],
              evidence: [d.perspective1, d.perspective2],
              metadata: {},
            })),
          ];

          set({
            isProcessing: false,
            sessionId: brief.session_id,
            sources: brief.sources,
            claims: extractedClaims,
            brief,
            progress: {
              stage: 'complete',
              message: 'Research brief ready!',
              progress: 100,
            },
          });
        } catch (error) {
          const errorMessage = error instanceof APIError
            ? error.detail
            : error instanceof Error
              ? error.message
              : 'Research pipeline failed';

          set({
            isProcessing: false,
            error: errorMessage,
            progress: {
              stage: 'error',
              message: errorMessage,
              progress: 0,
            },
          });
        }
      },

      reset: () =>
        set({
          query: '',
          files: [],
          urls: [],
          isProcessing: false,
          progress: null,
          sessionId: null,
          sources: [],
          claims: [],
          brief: null,
          error: null,
        }),

      // Error handling
      error: null,
      clearError: () => set({ error: null }),
    }),
    {
      name: 'scholarai-research',
      partialize: (state) => ({
        // Only persist these fields
        query: state.query,
        sessionId: state.sessionId,
        brief: state.brief,
        sources: state.sources,
        claims: state.claims,
      }),
    }
  )
);

// =============================================================================
// Selector Hooks for Better Performance
// =============================================================================

export const useQuery = () => useResearch((state) => state.query);
export const useSetQuery = () => useResearch((state) => state.setQuery);
export const useFiles = () => useResearch((state) => state.files);
export const useUrls = () => useResearch((state) => state.urls);
export const useIsProcessing = () => useResearch((state) => state.isProcessing);
export const useProgress = () => useResearch((state) => state.progress);
export const useSources = () => useResearch((state) => state.sources);
export const useClaims = () => useResearch((state) => state.claims);
export const useBrief = () => useResearch((state) => state.brief);
export const useError = () => useResearch((state) => state.error);
