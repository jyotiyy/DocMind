import { useDocuments } from "../hooks/useDocuments";
import { PDFUploader } from "./PDFUploader";
import { EmptyState } from "./EmptyState";
import { LoadingIndicator } from "./LoadingIndicator";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function Sidebar() {
  const { documents, isLoading, error, refresh, removeDocument, reindexAll } = useDocuments();

  return (
    <aside className="flex h-full w-80 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h1 className="text-lg font-bold text-brand-700">DocMind</h1>
        <p className="text-xs text-slate-400">Private, offline document Q&amp;A</p>
      </div>

      <div className="border-b border-slate-200 p-4">
        <PDFUploader onUploaded={refresh} />
      </div>

      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Documents ({documents.length})
        </h2>
        <button
          onClick={reindexAll}
          className="text-xs font-medium text-brand-600 hover:text-brand-700"
        >
          Reindex all
        </button>
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto px-4 pb-4">
        {isLoading && <LoadingIndicator label="Loading documents" />}
        {error && <p className="text-xs text-red-600">{error}</p>}
        {!isLoading && documents.length === 0 && (
          <EmptyState
            title="No documents yet"
            description="Upload a PDF above to start asking questions about it."
          />
        )}

        <ul className="space-y-2">
          {documents.map((doc) => (
            <li
              key={doc.document_id}
              className="group rounded-lg border border-slate-200 p-3 transition-colors hover:border-brand-300"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="truncate text-sm font-medium text-slate-700" title={doc.filename}>
                  {doc.filename}
                </p>
                <button
                  onClick={() => removeDocument(doc.document_id)}
                  className="text-xs text-slate-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
                  aria-label={`Delete ${doc.filename}`}
                >
                  ✕
                </button>
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {doc.page_count} pages · {doc.chunk_count} chunks
                {doc.ocr_pages > 0 && ` · ${doc.ocr_pages} OCR'd`}
              </p>
              <p className="text-xs text-slate-400">{formatBytes(doc.file_size_bytes)}</p>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
