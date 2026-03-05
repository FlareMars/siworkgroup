"use client";

import { use, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/lib/store/chat-store";
import { useChatSocket } from "@/lib/socket/use-chat-socket";
import { apiClient } from "@/lib/api/client";

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  created_at: string;
}

interface Session {
  id: string;
  title: string;
}

export default function ChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: clawId } = use(params);
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [streamContent, setStreamContent] = useState("");

  const { sendMessage, connected } = useChatSocket({
    clawId,
    sessionId: activeSessionId ?? "",
    enabled: !!activeSessionId,
    onChunk: (chunk, done) => {
      if (!done) {
        setStreamContent((prev) => prev + chunk);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: streamContent + chunk,
            created_at: new Date().toISOString(),
          },
        ]);
        setStreamContent("");
        setIsTyping(false);
      }
    },
  });

  // Load sessions
  useEffect(() => {
    apiClient
      .get<Session[]>(`/api/v1/claws/${clawId}/sessions`)
      .then((res) => {
        setSessions(res.data);
        if (res.data.length > 0) {
          setActiveSessionId(res.data[0].id);
        }
      })
      .catch(console.error);
  }, [clawId]);

  // Load messages when session changes
  useEffect(() => {
    if (!activeSessionId) return;
    apiClient
      .get<Message[]>(
        `/api/v1/claws/${clawId}/sessions/${activeSessionId}/messages`
      )
      .then((res) => setMessages(res.data))
      .catch(console.error);
  }, [clawId, activeSessionId]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  const createSession = async () => {
    const res = await apiClient.post<Session>(
      `/api/v1/claws/${clawId}/sessions`,
      { title: "New Session" }
    );
    setSessions((prev) => [res.data, ...prev]);
    setActiveSessionId(res.data.id);
    setMessages([]);
  };

  const handleSend = () => {
    if (!input.trim() || !activeSessionId || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);
    sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Session Sidebar */}
      <aside className="hidden w-64 border-r bg-muted/20 md:flex md:flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back
          </button>
          <button
            onClick={createSession}
            className="text-sm font-medium text-primary hover:underline"
          >
            + New
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => setActiveSessionId(session.id)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                session.id === activeSessionId
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50"
              }`}
            >
              {session.title}
            </button>
          ))}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-muted-foreground"}`}
            />
            <span className="text-sm font-medium">
              {connected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {!activeSessionId ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p className="text-muted-foreground">No session selected</p>
                <button
                  onClick={createSession}
                  className="mt-2 text-sm text-primary hover:underline"
                >
                  Create a new session
                </button>
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground"
                    }`}
                  >
                    <pre className="whitespace-pre-wrap font-sans">
                      {msg.content}
                    </pre>
                  </div>
                </div>
              ))}

              {/* Streaming chunk */}
              {isTyping && streamContent && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-2xl bg-muted px-4 py-2 text-sm">
                    <pre className="whitespace-pre-wrap font-sans">
                      {streamContent}
                    </pre>
                  </div>
                </div>
              )}

              {isTyping && !streamContent && (
                <div className="flex justify-start">
                  <div className="flex gap-1 rounded-2xl bg-muted px-4 py-3">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="h-2 w-2 animate-typing rounded-full bg-muted-foreground"
                        style={{ animationDelay: `${i * 0.2}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t p-4">
          <div className="mx-auto flex max-w-3xl gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                activeSessionId
                  ? "Type a message... (Enter to send, Shift+Enter for newline)"
                  : "Create a session to start chatting"
              }
              disabled={!activeSessionId || isTyping}
              rows={1}
              className="flex-1 resize-none rounded-xl border bg-background px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !activeSessionId || isTyping}
              className="rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}