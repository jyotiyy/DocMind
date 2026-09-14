import type { Citation } from "../types/api";

interface CitationCardProps {
  citation: Citation;
}

export function CitationCard({ citation }: CitationCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-sm">
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className="truncate font-semibold text-slate-700" title={citation.document_name}>
          {citation.document_name}
        </span>
        <span className="whitespace-nowrap rounded bg-slate-100 px-1.5 py-0.5 text-slate-500">
          p. {citation.page_number}
        </span>
      </div>
      <p className="line-clamp-3 text-slate-500">{citation.snippet}</p>
      <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full bg-brand-500"
          style={{ width: `${Math.round(citation.relevance_score * 100)}%` }}
        />
      </div>
    </div>
  );
}
