import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  ReceiptText,
  TrendingUp,
  Bot,
  ShieldCheck,
  Sparkles,
  Database,
  User,
  Activity,
} from 'lucide-react';
import type { SecurityTier, SecurityTierInfo } from '../../types/agent';
import { Badge } from '../ui/Badge';
import { endpoints } from '../../api';

export type NavTab = 'dashboard' | 'bills' | 'insights' | 'copilot' | 'security';

interface TopNavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  currentTier: SecurityTier;
  activeTierInfo: SecurityTierInfo;
  onOpenSeedModal?: () => void;
  onOpenProfileModal?: () => void;
  username?: string;
}

const navItems: { id: NavTab; label: string; icon: React.FC<{ className?: string }>; badge?: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'bills', label: 'Bills & OCR', icon: ReceiptText, badge: 'OCR' },
  { id: 'insights', label: 'Insights & Forecast', icon: TrendingUp },
  { id: 'copilot', label: 'AI Copilot', icon: Bot, badge: 'Agent' },
  { id: 'security', label: 'Security & Tiers', icon: ShieldCheck },
];

export const TopNavbar: React.FC<TopNavbarProps> = ({
  activeTab,
  setActiveTab,
  currentTier,
  activeTierInfo,
  onOpenSeedModal,
  onOpenProfileModal,
  username,
}) => {
  const [apiHealth, setApiHealth] = useState<'checking' | 'online' | 'standby'>('checking');
  const [latency, setLatency] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkApi = async () => {
      const start = Date.now();
      try {
        await endpoints.health.check();
        if (isMounted) {
          setApiHealth('online');
          setLatency(`${Date.now() - start}ms`);
        }
      } catch {
        if (isMounted) {
          setApiHealth('standby');
        }
      }
    };

    checkApi();
    const interval = setInterval(checkApi, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <nav className="sticky top-0 z-30 w-full bg-slate-950/85 backdrop-blur-2xl border-b border-slate-800/70">
      {/* Upper strip – brand + API status + controls */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <Sparkles className="w-[18px] h-[18px] text-slate-950" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-[15px] tracking-tight text-white">AuraFin</span>
              <span className="hidden sm:inline-flex text-[9px] uppercase font-bold tracking-widest px-1.5 py-[3px] rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                Financial Agent
              </span>
            </div>
          </div>

          {/* Center / Right status indicators & quick buttons */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* API Health badge */}
            <span
              className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${
                apiHealth === 'online'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : apiHealth === 'checking'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                  : 'bg-slate-800/80 text-slate-400 border-slate-700/80'
              }`}
              title="API Endpoint liveness (GET /health/check)"
            >
              <Activity className="w-3 h-3" />
              <span>
                {apiHealth === 'online'
                  ? `API Live ${latency ? `(${latency})` : ''}`
                  : apiHealth === 'checking'
                  ? 'Connecting...'
                  : 'API Standby (Demo)'}
              </span>
            </span>

            {/* Quick Demo Seed */}
            {onOpenSeedModal && (
              <button
                onClick={onOpenSeedModal}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/25 transition-colors"
                title="Seed 20 demo items via POST /demo/seed"
              >
                <Database className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Seed Demo</span>
              </button>
            )}

            {/* Profile Preferences */}
            {onOpenProfileModal && (
              <button
                onClick={onOpenProfileModal}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-colors"
                title="Finance Preferences (GET /profile)"
              >
                <User className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden md:inline">Profile</span>
              </button>
            )}

            {/* Tier badge */}
            <Badge
              variant={currentTier === 3 ? 'emerald' : currentTier === 2 ? 'amber' : 'slate'}
              size="sm"
              dot
            >
              Tier {currentTier} – {activeTierInfo.name}
            </Badge>

            {/* User avatar */}
            <div
              className="relative ml-1 cursor-pointer"
              onClick={onOpenProfileModal}
              title={username || 'Signed-in user'}
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-[11px] text-white shadow-md">
                {username ? username.slice(0, 2).toUpperCase() : 'AM'}
              </div>
              <span
                className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-slate-950 ${
                  apiHealth === 'online' ? 'bg-emerald-500' : 'bg-slate-500'
                }`}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Tab row */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-1 -mb-px overflow-x-auto scrollbar-thin pb-px">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative flex items-center gap-2 px-4 py-2.5 text-[13px] font-semibold rounded-t-xl transition-all duration-200 whitespace-nowrap group ${
                  isActive
                    ? 'text-emerald-300 bg-slate-900/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/30'
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-emerald-400' : 'text-slate-500 group-hover:text-slate-300'
                  }`}
                />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-[1px] rounded-full font-bold leading-tight ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
                {/* Active underline */}
                {isActive && (
                  <span className="absolute left-3 right-3 -bottom-px h-[2px] rounded-full bg-gradient-to-r from-emerald-400 to-teal-400" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
