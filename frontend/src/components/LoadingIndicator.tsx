interface LoadingIndicatorProps {
  label?: string;
}

export function LoadingIndicator({ label = "Loading" }: LoadingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <span className="flex gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
      </span>
      <span>{label}...</span>
    </div>
  );
}
