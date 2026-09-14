/**
 * Centralized Axios service layer for the DocMind API.
 *
 * All HTTP calls live here so components never construct requests directly
 * (per project requirements: "No inline API calls").
 */

import axios, { type AxiosInstance } from "axios";
import type {
  AskRequest,
  AskResponse,
  DeleteResponse,
  DocumentListResponse,
  HealthResponse,
  ReindexResponse,
  UploadResponse,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

const httpClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120_000,
});

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await httpClient.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function askQuestion(request: AskRequest): Promise<AskResponse> {
  const response = await httpClient.post<AskResponse>("/ask", {
    ...request,
    stream: false,
  });
  return response.data;
}

/**
 * Ask a question with a streamed answer via Server-Sent Events.
 *
 * Uses fetch directly (rather than Axios) since Axios does not natively
 * support incremental SSE consumption in the browser.
 */
export async function askQuestionStreaming(
  request: AskRequest,
  onToken: (token: string) => void,
  onDone: (final: Pick<AskResponse, "citations" | "confidence" | "documents_searched" | "retrieved_chunks">) => void,
  onError: (message: string) => void,
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok || !response.body) {
      onError(`Request failed with status ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const rawEvent of events) {
        const lines = rawEvent.split("\n");
        const eventLine = lines.find((l) => l.startsWith("event:"));
        const dataLine = lines.find((l) => l.startsWith("data:"));
        if (!eventLine || !dataLine) continue;

        const eventName = eventLine.replace("event:", "").trim();
        const payload = JSON.parse(dataLine.replace("data:", "").trim());

        if (eventName === "token") {
          onToken(payload.token as string);
        } else if (eventName === "done") {
          onDone(payload);
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err.message : "Streaming request failed.");
  }
}

export async function fetchDocuments(): Promise<DocumentListResponse> {
  const response = await httpClient.get<DocumentListResponse>("/documents");
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<DeleteResponse> {
  const response = await httpClient.delete<DeleteResponse>(`/documents/${documentId}`);
  return response.data;
}

export async function reindexDocuments(documentIds?: string[]): Promise<ReindexResponse> {
  const response = await httpClient.post<ReindexResponse>("/reindex", {
    document_ids: documentIds ?? null,
  });
  return response.data;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await httpClient.get<HealthResponse>("/health");
  return response.data;
}

export function extractApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string } | undefined;
    return data?.message ?? error.message;
  }
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}
