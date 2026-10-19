import React, { useState } from 'react';
import {
  Bot,
  User,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  CheckCircle2,
  Lock,
  Layers,
} from 'lucide-react';

import type { CopilotMessage, ActionRecommendation } from '../../types/agent';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface MessageItemProps {
  message: CopilotMessage;
  onExecuteRecommendation: (rec: ActionRecommendation) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onExecuteRecommendation,
}) => {
  const [showThinking, setShowThinking] = useState(false);
  const isAgent = message.sender === 'agent';

  // Simple Markdown-like formatter for bullet points, bolding, and headers
  const formatText = (text: string) => {
    return text.split('\n').map((line, idx) => {
      if (line.startsWith('### ')) {
        return (
          <h4 key={idx} className="text-sm font-bold text-white mt-2 mb-1">
            {line.replace('### ', '')}
          </h4>
        );
      }
      if (line.startsWith('* ') || line.startsWith('- ')) {
        const itemContent = line.slice(2);
        return (
          <div key={idx} className="flex items-start gap-2 text-xs text-slate-300 my-0.5 pl-1">
            <span className="text-emerald-400 font-bold shrink-0 mt-0.5">•</span>
            <span
              dangerouslySetInnerHTML={{
                __html: itemContent
                  .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
                  .replace(/`(.*?)`/g, '<code class="bg-slate-900 px-1 py-0.5 rounded text-emerald-300 font-mono text-[11px]">$1</code>'),
              }}
            />
          </div>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} className="h-1.5" />;
      }
      return (
        <p
          key={idx}
          className="text-xs text-slate-300 leading-relaxed my-0.5"
          dangerouslySetInnerHTML={{
            __html: line
              .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
              .replace(/`(.*?)`/g, '<code class="bg-slate-900 px-1 py-0.5 rounded text-emerald-300 font-mono text-[11px]">$1</code>'),
          }}
        />
      );
    });
  };

  return (
    <div
      className={`flex gap-3 py-3 ${
        isAgent ? 'items-start' : 'items-start flex-row-reverse'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
          isAgent
            ? 'bg-gradient-to-tr from-emerald-500 to-teal-400 text-slate-950 font-bold'
            : 'bg-slate-800 text-slate-200 border border-slate-700'
        }`}
      >
        {isAgent ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Message Content Container */}
      <div
        className={`max-w-[85%] rounded-2xl p-4 space-y-3 ${
          isAgent
            ? 'bg-slate-900/80 border border-slate-800/90 text-slate-200 shadow-lg'
            : 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20'
        }`}
      >
        {/* Thinking & Diagnostic Tool Results Collapsible (Agent only) */}
        {isAgent && (message.thinking || (message.toolResults && message.toolResults.length > 0)) && (
          <div className="pb-2 border-b border-slate-800/80">
            <button
              onClick={() => setShowThinking(!showThinking)}
              className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Sparkles className="w-3 h-3 text-emerald-400" />
              <span>
                Diagnostic Tool Evidence {message.toolResults ? `(${message.toolResults.length} tool calls)` : ''}
              </span>
              {showThinking ? (
                <ChevronUp className="w-3 h-3 ml-1" />
              ) : (
                <ChevronDown className="w-3 h-3 ml-1" />
              )}
            </button>
            {showThinking && (
              <div className="mt-2 space-y-2">
                {message.thinking && (
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] font-mono text-emerald-300 leading-relaxed animate-in fade-in">
                    {message.thinking}
                  </div>
                )}
                {message.toolResults?.map((tr, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1"
                  >
                    <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3" />
                      <span>Tool: {tr.tool}</span>
                    </div>
                    <pre className="overflow-x-auto text-[10px] text-slate-400 bg-slate-900/60 p-2 rounded-lg">
                      {JSON.stringify(tr.result, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Message Body */}
        <div className="space-y-1">{formatText(message.text)}</div>

        {/* Actionable Recommendation Cards */}
        {isAgent && message.recommendations && message.recommendations.length > 0 && (
          <div className="space-y-2.5 pt-2 border-t border-slate-800/80">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 flex items-center gap-1">
              <Layers className="w-3 h-3 text-emerald-400" /> Embedded Actionable Recommendations:
            </span>
            {message.recommendations.map((rec) => (
              <div
                key={rec.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  rec.executed
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-slate-950/70 border-slate-700/80 hover:border-slate-600'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white tracking-tight">
                        {rec.title}
                      </span>
                      <Badge variant="amber" size="sm">
                        Tier {rec.tier} Required
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{rec.description}</p>
                    <p className="text-[11px] text-emerald-400 font-semibold mt-1">
                      Impact: {rec.impact}
                    </p>
                  </div>

                  <div className="shrink-0">
                    {rec.executed ? (
                      <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-500/15 px-3 py-1.5 rounded-xl border border-emerald-500/30">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Executed</span>
                      </div>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => onExecuteRecommendation(rec)}
                        leftIcon={<Lock className="w-3.5 h-3.5 text-slate-950" />}
                        rightIcon={<ArrowRight className="w-3.5 h-3.5 text-slate-950" />}
                      >
                        Authorize & Run
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Citations & Metadata footer */}
        {isAgent && message.citations && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400">
            <span>Sources:</span>
            {message.citations.map((cite, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300"
              >
                {cite}
              </span>
            ))}
            <span className="ml-auto text-slate-400 font-mono-numbers">
              {message.timestamp}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
