/**
 * React hook for WebSocket-based real-time chat.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/lib/store/auth-store";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface UseChatSocketOptions {
  clawId: string;
  sessionId: string;
  enabled?: boolean;
  onChunk?: (chunk: string, done: boolean) => void;
  onError?: (detail: string) => void;
}

interface UseChatSocketReturn {
  connected: boolean;
  sendMessage: (content: string) => void;
  disconnect: () => void;
}

export function useChatSocket({
  clawId,
  sessionId,
  enabled = true,
  onChunk,
  onError,
}: UseChatSocketOptions): UseChatSocketReturn {
  const { accessToken } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (!enabled || !sessionId || !accessToken) return;

    const url = `${WS_BASE_URL}/ws/claws/${clawId}/sessions/${sessionId}/chat?token=${accessToken}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // Send ping every 30s to keep connection alive
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        switch (msg.type) {
          case "chunk":
            onChunk?.(msg.content as string, msg.done as boolean);
            break;
          case "error":
            onError?.(msg.detail as string);
            break;
          case "pong":
            break;
          default:
            break;
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;

      if (shouldReconnectRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [clawId, sessionId, enabled, accessToken, onChunk, onError]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  // Ping interval
  useEffect(() => {
    if (!connected) return;
    const interval = setInterval(() => {
      wsRef.current?.send(JSON.stringify({ type: "ping" }));
    }, 30_000);
    return () => clearInterval(interval);
  }, [connected]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", content }));
    }
  }, []);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    wsRef.current?.close();
  }, []);

  return { connected, sendMessage, disconnect };
}