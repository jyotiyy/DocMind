import { useCallback, useState } from "react";
import { askQuestionStreaming, extractApiErrorMessage } from "../services/api";
import type { ChatMessage } from "../types/api";

interface UseChatResult {
  messages: ChatMessage[];
  isAsking: boolean;
  error: string | null;
  askQuestion: (question: string, documentIds?: string[]) => Promise<void>;
  clearHistory: () => void;
}

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const askQuestion = useCallback(
    async (question: string, documentIds?: string[]) => {
      setError(null);
      const userMessage = createMessage("user", question);
      const assistantMessage: ChatMessage = {
        ...createMessage("assistant", ""),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsAsking(true);

      try {
        await askQuestionStreaming(
          { question, document_ids: documentIds ?? null },
          (token) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id ? { ...m, content: m.content + token } : m,
              ),
            );
          },
          (final) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? {
                      ...m,
                      isStreaming: false,
                      citations: final.citations,
                      confidence: final.confidence,
                    }
                  : m,
              ),
            );
          },
          (message) => {
            setError(message);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? { ...m, isStreaming: false, content: m.content || "Something went wrong." }
                  : m,
              ),
            );
          },
        );
      } catch (err) {
        setError(extractApiErrorMessage(err));
      } finally {
        setIsAsking(false);
      }
    },
    [],
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isAsking, error, askQuestion, clearHistory };
}
