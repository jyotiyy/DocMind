import type { ConfidenceScore } from "../types/api";

const LABEL_STYLES: Record<ConfidenceScore["label"], string> = {
  high: "bg-emerald-100 text-emerald-800 border-emerald-300",
  medium: "bg-amber-100 text-amber-800 border-amber-300",
  low: "bg-red-100 text-red-800 border-red-300",
};

const LABEL_TEXT: Record<ConfidenceScore["label"], string> = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
};

interface ConfidenceBadgeProps {
  confidence: ConfidenceScore;
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  return (
    <div className="group relative inline-flex">
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${LABEL_STYLES[confidence.label]}`}
      >
        {LABEL_TEXT[confidence.label]} · {Math.round(confidence.score * 100)}%
      </span>
      <div className="pointer-events-none absolute bottom-full left-0 mb-2 hidden w-64 rounded-lg bg-slate-900 p-2.5 text-xs text-white shadow-lg group-hover:block">
        {confidence.reason}
      </div>
    </div>
  );
}
