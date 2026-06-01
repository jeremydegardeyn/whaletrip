import ReactMarkdown from 'react-markdown';
import { clsx } from 'clsx';
import type { ChatMessage } from '@/types';

const AGENT_LABELS: Record<string, string> = {
  whale_intelligence_agent: '🔬 Whale Intelligence',
  travel_planner_agent:     '✈️ Travel Planner',
  tour_recommendation_agent: '🚢 Tour Expert',
  destination_agent:         '🗺️ Destination Guide',
  coordinator_agent:         '🐋 WhaleTrip',
};

interface Props {
  message: ChatMessage;
  onFollowUpClick: (q: string) => void;
}

export function MessageBubble({ message, onFollowUpClick }: Props) {
  const isUser = message.role === 'user';
  const agentLabel = message.agent ? AGENT_LABELS[message.agent] : null;

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[85%] rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'bg-ocean-600 text-white rounded-br-sm'
            : 'bg-ocean-900 text-ocean-100 rounded-bl-sm'
        )}
      >
        {agentLabel && !isUser && (
          <p className="text-ocean-400 text-[10px] mb-1.5 font-medium">{agentLabel}</p>
        )}
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {message.followUpQuestions && message.followUpQuestions.length > 0 && (
          <div className="mt-2.5 space-y-1">
            {message.followUpQuestions.map((q) => (
              <button
                key={q}
                onClick={() => onFollowUpClick(q)}
                className="block w-full text-left text-[11px] text-ocean-300 border border-ocean-700 rounded-lg px-2.5 py-1.5 hover:bg-ocean-800 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
