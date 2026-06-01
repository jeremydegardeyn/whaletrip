'use client';

import { useState, useRef, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';
import type { MapAction, SightingsFilter } from '@/types';

interface Props {
  onMapAction?: (actions: MapAction[]) => void;
  onFilterChange?: (filter: Partial<SightingsFilter>) => void;
  mapContext?: Record<string, unknown>;
  isOpen: boolean;
  onToggle: () => void;
}

const STARTER_PROMPTS = [
  'Where can I see blue whales in September?',
  "I'm in Toronto, budget $2,500 — where should I go?",
  'Best place for humpback whales next month?',
  'I love hiking and photography — what destination suits me?',
];

export function ChatPanel({ onMapAction, onFilterChange, mapContext, isOpen, onToggle }: Props) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { messages, isLoading, error, sendMessage, clearSession } = useChat({
    onMapAction,
    onFilterChange,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const text = input;
    setInput('');
    await sendMessage(text, mapContext);
  }

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="absolute bottom-6 right-6 z-20 bg-ocean-600 hover:bg-ocean-500 text-white rounded-full p-4 shadow-2xl transition-all hover:scale-105"
        title="Open WhaleTrip Assistant"
      >
        <span className="text-2xl">🐋</span>
      </button>
    );
  }

  return (
    <div className="absolute bottom-0 right-0 z-20 w-full md:w-[420px] h-full md:h-[600px] md:bottom-4 md:right-4 md:rounded-2xl flex flex-col bg-ocean-950/98 border border-ocean-700 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ocean-800 rounded-t-2xl">
        <div className="flex items-center gap-2">
          <span className="text-xl">🐋</span>
          <div>
            <h2 className="text-white font-semibold text-sm">WhaleTrip Assistant</h2>
            <p className="text-ocean-400 text-xs">Powered by Gemini</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={clearSession}
            className="text-xs text-ocean-500 hover:text-ocean-300 px-2 py-1 rounded hover:bg-ocean-800 transition-colors"
            title="New conversation"
          >
            New chat
          </button>
          <button onClick={onToggle} className="text-ocean-400 hover:text-white text-lg leading-none">
            ×
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-ocean-400 text-sm text-center pt-4">
              Ask me anything about whale watching worldwide.
            </p>
            <div className="grid grid-cols-1 gap-2">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt, mapContext)}
                  className="text-left text-xs px-3 py-2.5 rounded-lg bg-ocean-900 border border-ocean-700 text-ocean-300 hover:bg-ocean-800 hover:text-white transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onFollowUpClick={(q) => sendMessage(q, mapContext)}
          />
        ))}

        {isLoading && (
          <div className="flex gap-1 px-3 py-2">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-2 h-2 rounded-full bg-ocean-500 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        )}

        {error && (
          <p className="text-red-400 text-xs px-3 py-2 bg-red-900/20 rounded-lg">{error}</p>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-ocean-800">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about whales or plan a trip…"
            disabled={isLoading}
            className="flex-1 bg-ocean-900 border border-ocean-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-ocean-500 focus:outline-none focus:border-ocean-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-ocean-600 hover:bg-ocean-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl px-4 py-2.5 transition-colors"
          >
            ↑
          </button>
        </div>
      </form>
    </div>
  );
}
