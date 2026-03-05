/**
 * Zustand chat store for managing active sessions and messages.
 */

import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  tool_calls?: unknown[] | null;
  created_at: string;
}

interface ChatState {
  // Active session per Claw
  activeSessions: Record<string, string>; // clawId → sessionId
  // Streaming content per session
  streamingContent: Record<string, string>;

  setActiveSession: (clawId: string, sessionId: string) => void;
  appendStream: (sessionId: string, chunk: string) => void;
  clearStream: (sessionId: string) => string;
}

export const useChatStore = create<ChatState>((set, get) => ({
  activeSessions: {},
  streamingContent: {},

  setActiveSession: (clawId, sessionId) =>
    set((state) => ({
      activeSessions: { ...state.activeSessions, [clawId]: sessionId },
    })),

  appendStream: (sessionId, chunk) =>
    set((state) => ({
      streamingContent: {
        ...state.streamingContent,
        [sessionId]: (state.streamingContent[sessionId] ?? "") + chunk,
      },
    })),

  clearStream: (sessionId) => {
    const content = get().streamingContent[sessionId] ?? "";
    set((state) => {
      const { [sessionId]: _, ...rest } = state.streamingContent;
      return { streamingContent: rest };
    });
    return content;
  },
}));