import { Link } from "react-router-dom";
import { useDocuments } from "../hooks/useDocuments";
import { PDFUploader } from "../components/PDFUploader";
import { EmptyState } from "../components/EmptyState";

export function HomePage() {
  const { documents, refresh } = useDocuments();

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-6 text-center">
      <h1 className="text-3xl font-bold text-brand-700">DocMind</h1>
      <p className="mt-2 max-w-lg text-slate-500">
        Upload your PDFs and ask questions answered strictly from their content — fully
        private, fully offline, with page-level citations and confidence scoring.
      </p>

      <div className="mt-8 w-full max-w-md">
        <PDFUploader onUploaded={refresh} />
      </div>

      {documents.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="No documents yet"
            description="Upload a PDF to get started, then head to the chat to ask questions."
          />
        </div>
      ) : (
        <p className="mt-6 text-sm text-slate-500">
          {documents.length} document{documents.length === 1 ? "" : "s"} indexed and ready.
        </p>
      )}

      <Link
        to="/chat"
        className="mt-6 rounded-full bg-brand-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700"
      >
        Go to Chat →
      </Link>
    </div>
  );
}
