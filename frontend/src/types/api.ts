/**
 * TypeScript interfaces mirroring the backend's Pydantic schemas.
 * Keeping these in one file makes it obvious when the API contract changes.
 */

export type ConfidenceLabel = "high" | "medium" | "low";

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_id: string;
  snippet: string;
  relevance_score: number;
}

export interface ConfidenceScore {
  score: number;
  label: ConfidenceLabel;
  reason: string;
}

export interface AskRequest {
  question: string;
  document_ids?: string[] | null;
  top_k?: number | null;
  stream?: boolean;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  confidence: ConfidenceScore;
  question: string;
  documents_searched: number;
  retrieved_chunks: number;
}

export interface UploadedDocumentInfo {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  ocr_pages: number;
  status: string;
}

export interface UploadResponse {
  documents: UploadedDocumentInfo[];
  message: string;
}

export interface DocumentSummary {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  ocr_pages: number;
  file_size_bytes: number;
  uploaded_at: string;
  status: string;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  total: number;
}

export interface DeleteResponse {
  document_id: string;
  message: string;
}

export interface ReindexResponse {
  reindexed_documents: number;
  total_chunks: number;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  ollama_reachable: boolean;
  embedding_model_loaded: boolean;
  reranker_model_loaded: boolean;
  total_documents: number;
  total_chunks: number;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

/** A single message in the chat transcript, as rendered by the UI. */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: ConfidenceScore;
  isStreaming?: boolean;
  createdAt: string;
}
