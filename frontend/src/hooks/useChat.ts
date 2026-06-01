'use client';

import { useState, useCallback } from 'react';
import { sendChatMessage, clearChatSession } from '@/lib/api';
import type { ChatMessage, MapAction, SightingsFilter } from '@/types';

interface UseChatOptions {
  onMapAction?: (actions: MapAction[]) => void;
  onFilterChange?: (filter: Partial<SightingsFilter>) => void;
}

export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, mapContext?: Record<string, unknown>) => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await sendChatMessage(text, sessionId, mapContext);
        if (response.session_id) setSessionId(response.session_id);

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.message,
          agent: response.agent ?? undefined,
          timestamp: new Date(),
          mapActions: response.map_actions as MapAction[] | undefined,
          followUpQuestions: response.follow_up_questions ?? undefined,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (response.map_actions?.length && options.onMapAction) {
          options.onMapAction(response.map_actions as MapAction[]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, options]
  );

  const clearSession = useCallback(async () => {
    if (sessionId) {
      await clearChatSession(sessionId).catch(() => {});
    }
    setMessages([]);
    setSessionId(undefined);
    setError(null);
  }, [sessionId]);

  return { messages, sessionId, isLoading, error, sendMessage, clearSession };
}
