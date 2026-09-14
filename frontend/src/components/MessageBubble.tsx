import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../types/api";
import { CitationCard } from "./CitationCard";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { LoadingIndicator } from "./LoadingIndicator";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 ${
          isUser ? "bg-brand-600 text-white" : "border border-slate-200 bg-white text-slate-800"
        }`}
      >
        {message.content ? (
          <div className="prose prose-sm max-w-none prose-p:my-1.5 prose-slate">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : message.isStreaming ? (
          <LoadingIndicator label="Thinking" />
        ) : null}

        {!isUser && message.confidence && (
          <div className="mt-3">
            <ConfidenceBadge confidence={message.confidence} />
          </div>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {message.citations.map((citation) => (
              <CitationCard key={citation.chunk_id} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
