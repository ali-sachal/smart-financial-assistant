import React, { useRef, useEffect } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import type { CopilotMessage, ActionRecommendation, SecurityTier } from '../../types/agent';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

import { MessageItem } from './MessageItem';
import { PromptChips } from './PromptChips';

interface ChatDrawerProps {
  messages: CopilotMessage[];
  isTyping: boolean;
  inputValue: string;
  setInputValue: (val: string) => void;
  onSendMessage: (text: string) => void;
  onExecuteRecommendation: (rec: ActionRecommendation) => void;
  currentTier: SecurityTier;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({
  messages,
  isTyping,
  inputValue,
  setInputValue,
  onSendMessage,
  onExecuteRecommendation,
  currentTier,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isTyping) {
      onSendMessage(inputValue);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] rounded-3xl glass-panel overflow-hidden border border-slate-800">
      {/* Copilot Header */}
      <div className="p-4 px-6 border-b border-slate-800/80 bg-slate-950/60 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-slate-950 font-bold shadow-md shadow-emerald-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-tight m-0">
                Aura AI Advisory Copilot
              </h2>
              <span className="text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                Live Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Autonomous financial participant with tool execution & state mutation capabilities
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="emerald" size="sm" dot>
            Tier {currentTier} Gateway Active
          </Badge>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <MessageItem
            key={message.id}
            message={message}
            onExecuteRecommendation={onExecuteRecommendation}
          />
        ))}

        {isTyping && (
          <div className="flex items-center gap-3 py-2 text-xs text-slate-400 animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-slate-800/90 border border-slate-700/80 flex items-center justify-center text-emerald-400">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-3 rounded-2xl bg-slate-900/60 border border-slate-800 text-slate-300 text-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce [animation-delay:0.2s]" />
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-bounce [animation-delay:0.4s]" />
              <span className="ml-1 text-slate-400">Aura is evaluating financial parameters...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips Bar */}
      <div className="px-6 py-2 bg-slate-950/80 border-t border-slate-800/60 shrink-0">
        <PromptChips
          onSelectPrompt={(prompt) => {
            setInputValue(prompt);
            onSendMessage(prompt);
          }}
          disabled={isTyping}
        />
      </div>

      {/* Input Message Form */}
      <form
        onSubmit={handleSubmit}
        className="p-4 px-6 bg-slate-950 border-t border-slate-800/80 flex items-center gap-3 shrink-0"
      >
        <div className="relative flex-1">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask Aura (e.g. 'Can I afford dinner out tonight without exceeding my dining limit?')..."
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-2xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 pr-12 transition-all shadow-inner"
            disabled={isTyping}
          />
        </div>

        <Button
          type="submit"
          variant="glow"
          size="md"
          disabled={!inputValue.trim() || isTyping}
          className="rounded-2xl"
          rightIcon={<Send className="w-4 h-4" />}
        >
          Send
        </Button>
      </form>
    </div>
  );
};
