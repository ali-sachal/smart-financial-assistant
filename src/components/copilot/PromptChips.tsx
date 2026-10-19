import React from 'react';
import { Sparkles, Utensils, PieChart, Receipt, PiggyBank, TrendingUp } from 'lucide-react';

interface PromptChipsProps {
  onSelectPrompt: (promptText: string) => void;
  disabled?: boolean;
}

export const PromptChips: React.FC<PromptChipsProps> = ({
  onSelectPrompt,
  disabled = false,
}) => {
  const chips = [
    {
      label: 'Can I afford dinner out tonight?',
      query: 'Can I afford dinner out tonight without exceeding my dining limit?',
      icon: Utensils,
    },
    {
      label: 'Summarize weekly expenses',
      query: 'Summarize weekly expenses and highlight burn rate anomalies',
      icon: PieChart,
    },
    {
      label: 'Analyze bill changes',
      query: 'Analyze bill changes between September and October receipts',
      icon: Receipt,
    },
    {
      label: 'Review budget surplus',
      query: 'Review budget surplus and recommend emergency fund transfer',
      icon: PiggyBank,
    },
    {
      label: 'Check month-end projection',
      query: 'Check month-end projection and runway estimate',
      icon: TrendingUp,
    },
  ];

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none py-1">
      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 shrink-0 flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-emerald-400" /> Suggestions:
      </span>
      {chips.map((chip, idx) => {
        const Icon = chip.icon;
        return (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSelectPrompt(chip.query)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 hover:border-emerald-500/40 transition-all shrink-0 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
          >
            <Icon className="w-3 h-3 text-emerald-400" />
            <span>{chip.label}</span>
          </button>
        );
      })}
    </div>
  );
};
