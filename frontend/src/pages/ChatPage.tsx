import { Sidebar } from "../components/Sidebar";
import { ChatWindow } from "../components/ChatWindow";
import { useChat } from "../hooks/useChat";

export function ChatPage() {
  const { messages, isAsking, error, askQuestion, clearHistory } = useChat();

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <Sidebar />
      <ChatWindow
        messages={messages}
        isAsking={isAsking}
        error={error}
        onAsk={(question) => askQuestion(question)}
        onClear={clearHistory}
      />
    </div>
  );
}
