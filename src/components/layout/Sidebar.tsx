import React from 'react';
import {
  LayoutDashboard,
  ReceiptText,
  TrendingUp,
  Bot,
  ShieldCheck,
  Terminal,
  Sparkles,
  Lock,
  ChevronRight,
  Eye,
  EyeOff,
} from 'lucide-react';
import type { SecurityTier, SecurityTierInfo } from '../../types/agent';
import { Badge } from '../ui/Badge';

export type NavTab = 'dashboard' | 'bills' | 'insights' | 'copilot' | 'security' | 'audit';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  currentTier: SecurityTier;
  activeTierInfo: SecurityTierInfo;
  piiMaskingEnabled: boolean;
  onTogglePiiMasking: () => void;
  onOpenAuditDrawer: () => void;
  auditCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  currentTier,
  activeTierInfo,
  piiMaskingEnabled,
  onTogglePiiMasking,
  onOpenAuditDrawer,
  auditCount,
}) => {
  const navItems = [
    {
      id: 'dashboard' as NavTab,
      label: 'Smart Dashboard',
      icon: LayoutDashboard,
      badge: undefined,
    },
    {
      id: 'bills' as NavTab,
      label: 'Multimodal Bills & OCR',
      icon: ReceiptText,
      badge: '2 New',
    },
    {
      id: 'insights' as NavTab,
      label: 'Cash Flow & Curves',
      icon: TrendingUp,
      badge: undefined,
    },
    {
      id: 'copilot' as NavTab,
      label: 'Autonomous Copilot',
      icon: Bot,
      badge: 'Live',
    },
    {
      id: 'security' as NavTab,
      label: 'Security & PII Gateway',
      icon: ShieldCheck,
      badge: `Tier ${currentTier}`,
    },
    {
      id: 'audit' as NavTab,
      label: 'Sandbox Audit Drawer',
      icon: Terminal,
      badge: `${auditCount}`,
      action: onOpenAuditDrawer,
    },
  ];

  return (
    <aside className="w-64 bg-slate-950/90 border-r border-slate-800/80 flex flex-col h-screen sticky top-0 shrink-0 backdrop-blur-xl z-20">
      {/* Brand & Track Info */}
      <div className="p-5 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <Sparkles className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-white">AuraFin</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                AI Agent
              </span>
            </div>
            <p className="text-[11px] text-slate-400 truncate">Financial Participant Track</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Core Workspaces
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                if (item.action) {
                  item.action();
                } else {
                  setActiveTab(item.id);
                }
              }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 group ${
                isActive
                  ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono-numbers font-medium ${
                    isActive
                      ? 'bg-emerald-500/25 text-emerald-300'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Security Status Box */}
      <div className="p-3 mx-3 mb-3 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px] font-bold text-white">Gateway Status</span>
          </div>
          <Badge
            variant={currentTier === 3 ? 'emerald' : currentTier === 2 ? 'amber' : 'slate'}
            size="sm"
            dot
          >
            Tier {currentTier}
          </Badge>
        </div>

        <p className="text-[10px] text-slate-400 leading-relaxed">
          {activeTierInfo.name}
        </p>

        {/* PII Masking Quick Toggle */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            {piiMaskingEnabled ? (
              <EyeOff className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Eye className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span className="text-[10px] font-medium">PII Sanitization</span>
          </div>
          <button
            onClick={onTogglePiiMasking}
            className={`w-9 h-5 rounded-full p-0.5 transition-colors duration-200 ease-in-out focus:outline-none ${
              piiMaskingEnabled ? 'bg-emerald-500' : 'bg-slate-700'
            }`}
            title="Toggle client-side PII scrubbing"
          >
            <div
              className={`w-4 h-4 rounded-full bg-slate-950 shadow transform transition-transform duration-200 ease-in-out ${
                piiMaskingEnabled ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* User Badge */}
      <div className="p-3 border-t border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-xs text-white shadow-md">
              AM
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-slate-950" />
          </div>
          <div className="truncate">
            <p className="text-xs font-semibold text-white truncate">Alex Mercer</p>
            <p className="text-[10px] text-slate-400 truncate">Fin Participant #810</p>
          </div>
        </div>
        <button
          onClick={() => setActiveTab('security')}
          className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          title="Security preferences"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
