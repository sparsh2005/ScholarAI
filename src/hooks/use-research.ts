/**
 * Research Pipeline Hook
 *
 * Central state management for the ScholarAI research workflow.
 * Manages document uploads, processing, and research brief generation.
 */

import { create } from 'zustand';
import {
  uploadDocument,
  runResearchPipeline,
  type Source,
  type Claim,
  type ResearchBrief,
  type PipelineProgress,
  type UploadResponse,
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
}

export interface AddedUrl {
  id: string;
  url: string;
  title?: string;
}

export interface ResearchState {
  // Query
  query: string;
  setQuery: (query: string) => void;

  // Uploaded files
  files: UploadedFile[];
  addFile: (file: File) => Promise<void>;
  removeFile: (id: string) => void;

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

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return ext;
}

// =============================================================================
// Store
// =============================================================================

export const useResearch = create<ResearchState>((set, get) => ({
  // Query
  query: '',
  setQuery: (query) => set({ query }),

  // Files
  files: [],
  addFile: async (file: File) => {
    try {
      const response: UploadResponse = await uploadDocument(file);

      const uploadedFile: UploadedFile = {
        id: response.id,
        name: response.filename,
        type: response.file_type,
        size: formatFileSize(response.file_size),
        uploadedAt: new Date(),
      };

      set((state) => ({
        files: [...state.files, uploadedFile],
        error: null,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to upload file',
      });
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
    const id = Date.now().toString();
    // Extract title from URL or use generic
    let title = 'Webpage';
    try {
      const urlObj = new URL(url);
      if (urlObj.hostname.includes('pubmed')) title = 'PubMed Article';
      else if (urlObj.hostname.includes('arxiv')) title = 'arXiv Paper';
      else if (urlObj.hostname.includes('nature')) title = 'Nature Article';
      else if (urlObj.hostname.includes('sciencedirect')) title = 'ScienceDirect';
      else title = urlObj.hostname;
    } catch {
      // Invalid URL, use default title
    }

    set((state) => ({
      urls: [...state.urls, { id, url, title }],
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
    const { query, files, urls } = get();

    if (!query.trim()) {
      set({ error: 'Please enter a research question' });
      return;
    }

    if (files.length === 0 && urls.length === 0) {
      set({ error: 'Please add at least one document or URL' });
      return;
    }

    set({
      isProcessing: true,
      error: null,
      progress: {
        stage: 'uploading',
        message: 'Starting research pipeline...',
        progress: 0,
      },
    });

    try {
      const brief = await runResearchPipeline(
        query,
        files.map((f) => f.id),
        urls.map((u) => u.url),
        (progress) => set({ progress }),
      );

      set({
        isProcessing: false,
        sessionId: brief.session_id,
        sources: brief.sources,
        brief,
        progress: {
          stage: 'complete',
          message: 'Research brief ready!',
          progress: 100,
        },
      });
    } catch (error) {
      set({
        isProcessing: false,
        error: error instanceof Error ? error.message : 'Research pipeline failed',
        progress: {
          stage: 'error',
          message: error instanceof Error ? error.message : 'Failed',
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
}));
