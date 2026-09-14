import { useCallback, useEffect, useState } from "react";
import {
  deleteDocument,
  extractApiErrorMessage,
  fetchDocuments,
  reindexDocuments,
} from "../services/api";
import type { DocumentSummary } from "../types/api";

interface UseDocumentsResult {
  documents: DocumentSummary[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  removeDocument: (documentId: string) => Promise<void>;
  reindexAll: () => Promise<void>;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchDocuments();
      setDocuments(response.documents);
    } catch (err) {
      setError(extractApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeDocument = useCallback(
    async (documentId: string) => {
      setError(null);
      try {
        await deleteDocument(documentId);
        setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId));
      } catch (err) {
        setError(extractApiErrorMessage(err));
      }
    },
    [],
  );

  const reindexAll = useCallback(async () => {
    setError(null);
    try {
      await reindexDocuments();
      await refresh();
    } catch (err) {
      setError(extractApiErrorMessage(err));
    }
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { documents, isLoading, error, refresh, removeDocument, reindexAll };
}
