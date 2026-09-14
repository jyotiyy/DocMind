import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/api";
import { MessageBubble } from "./MessageBubble";
import { EmptyState } from "./EmptyState";

interface ChatWindowProps {
  messages: ChatMessage[];
  isAsking: boolean;
  error: string | null;
  onAsk: (question: string) => void;
  onClear: () => void;
}

export function ChatWindow({ messages, isAsking, error, onAsk, onClear }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isAsking) return;
    onAsk(trimmed);
    setInput("");
  };

  return (
    <div className="flex h-full flex-1 flex-col bg-slate-50">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <h2 className="text-sm font-semibold text-slate-700">Chat</h2>
        <button onClick={onClear} className="text-xs text-slate-400 hover:text-slate-600">
          Clear history
        </button>
      </div>

      <div ref={scrollRef} className="scrollbar-thin flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState
            icon="chat"
            title="Ask anything about your documents"
            description="Answers are generated only from what you've uploaded, with page-level citations and a confidence score."
          />
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        )}
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your uploaded documents..."
            className="flex-1 rounded-full border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <button
            type="submit"
            disabled={isAsking || !input.trim()}
            className="rounded-full bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}
