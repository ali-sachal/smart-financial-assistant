import React from 'react';
import {
  ShieldCheck,
  Terminal,
  Eye,
  Bot,
} from 'lucide-react';
import type { SecurityTier, SecurityTierInfo } from '../../types/agent';
import { Button } from '../ui/Button';

interface HeaderProps {
  currentTier: SecurityTier;
  setCurrentTier: (tier: SecurityTier) => void;
  activeTierInfo?: SecurityTierInfo;
  piiMaskingEnabled: boolean;
  onOpenPiiModal: () => void;
  onOpenAuditDrawer: () => void;
  auditCount: number;
  onOpenCopilot: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTier,
  setCurrentTier,
  piiMaskingEnabled,
  onOpenPiiModal,
  onOpenAuditDrawer,
  auditCount,
  onOpenCopilot,
}) => {

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Title & Autonomous Agent Pill */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <h1 className="text-base font-bold text-white tracking-tight m-0">
            Topic A: Personal Finance Assistant
          </h1>
          <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            AI Participant Online
          </span>
        </div>
      </div>

      {/* Action Controls & Gatekeeper Bar */}
      <div className="flex items-center gap-2.5">
        {/* Tier Selector Dropdown */}
        <div className="flex items-center bg-slate-900/90 rounded-xl p-1 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 px-2 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="hidden md:inline">Gateway:</span>
          </span>
          {([1, 2, 3] as SecurityTier[]).map((t) => {
            const isSelected = currentTier === t;
            return (
              <button
                key={t}
                onClick={() => setCurrentTier(t)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                  isSelected
                    ? t === 3
                      ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                      : t === 2
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title={`Switch to Tier ${t}: ${
                  t === 1 ? 'Read-Only' : t === 2 ? 'Predictive' : 'State-Modifying (PIN Gated)'
                }`}
              >
                T{t}
              </button>
            );
          })}
        </div>

        {/* PII Preview Trigger */}
        <button
          onClick={onOpenPiiModal}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
            piiMaskingEnabled
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
              : 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
          }`}
          title="Inspect Client-Side PII Masking Engine"
        >
          <Eye className="w-3.5 h-3.5" />
          <span className="hidden lg:inline">PII Shield:</span>
          <span>{piiMaskingEnabled ? 'Masked' : 'Raw'}</span>
        </button>

        {/* Audit Evidence Drawer Button */}
        <button
          onClick={onOpenAuditDrawer}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 transition-all shadow-sm"
          title="Open Sandbox Execution Evidence Drawer"
        >
          <Terminal className="w-3.5 h-3.5 text-sky-400" />
          <span className="hidden sm:inline">Execution Evidence</span>
          <span className="bg-sky-500/20 text-sky-300 text-[10px] px-1.5 py-0.2 rounded-full font-mono-numbers">
            {auditCount}
          </span>
        </button>

        {/* Quick Copilot Trigger */}
        <Button
          variant="glow"
          size="sm"
          onClick={onOpenCopilot}
          leftIcon={<Bot className="w-4 h-4" />}
          className="shadow-sm"
        >
          <span className="hidden sm:inline">Ask</span> Copilot
        </Button>
      </div>
    </header>
  );
};
