import React from 'react';
import {
  TrendingUp,
  PiggyBank,
  Sparkles,
  Flame,
  ShieldCheck,
  Calendar,
} from 'lucide-react';

import type { MetricSummary } from '../../types/financial';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface MetricCardsProps {
  metrics: MetricSummary;
  onOptimizeClick: () => void;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics, onOptimizeClick }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Monthly Inflow */}
      <Card className="p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/10 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none transition-all group-hover:bg-emerald-500/15" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400">Monthly Inflow</span>
          <div className="w-8 h-8 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono-numbers">
            ${metrics.totalInflow.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-xs font-semibold text-emerald-400">100% on pace</span>
        </div>
        <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
          <Calendar className="w-3 h-3 text-slate-400" /> Current cycle ledger inflow
        </p>
      </Card>

      {/* Discretionary Outflow & Burn Rate */}
      <Card className="p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-rose-500/10 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none transition-all group-hover:bg-rose-500/15" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400">Discretionary Outflow</span>
          <div className="w-8 h-8 rounded-xl bg-rose-500/15 text-rose-400 flex items-center justify-center">
            <Flame className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono-numbers">
            ${metrics.discretionaryOutflow.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-xs font-semibold text-amber-400">
            ${metrics.dailyBurnRate}/day
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
          <span>Fixed bills: ${metrics.fixedOutflow.toFixed(0)}</span>
          <span className="text-emerald-400 font-semibold font-mono-numbers">
            Safe: ${metrics.safeToSpendDaily}/day
          </span>
        </div>
      </Card>

      {/* Net Monthly Savings & Rate */}
      <Card className="p-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-28 h-28 bg-sky-500/10 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none transition-all group-hover:bg-sky-500/15" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400">Net Savings (Runway)</span>
          <div className="w-8 h-8 rounded-xl bg-sky-500/15 text-sky-400 flex items-center justify-center">
            <PiggyBank className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono-numbers">
            +${metrics.netSavings.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
          <Badge variant="sky" size="sm">
            {metrics.savingsRate}% Rate
          </Badge>
        </div>
        <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-sky-400" />
          <span>Runway: <strong className="text-white font-mono-numbers">{metrics.runwayDays} days</strong> liquid reserve</span>
        </p>
      </Card>

      {/* AI Financial Health Score */}
      <Card className="p-5 relative overflow-hidden group border-emerald-500/30 shadow-lg shadow-emerald-500/5">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/15 rounded-full blur-2xl -mr-6 -mt-6 pointer-events-none" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-300">AI Health Score</span>
          <div className="w-8 h-8 rounded-xl bg-emerald-500 text-slate-950 flex items-center justify-center font-bold">
            <Sparkles className="w-4 h-4" />
          </div>
        </div>
        <div className="flex items-baseline gap-2.5">
          <span className="text-3xl font-extrabold text-white font-mono-numbers">
            {metrics.healthScore}
          </span>
          <span className="text-xs text-slate-400">/ 100</span>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-md">
            +{metrics.scoreChange} pts
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">Autonomous status:</span>
          <button
            onClick={onOptimizeClick}
            className="text-[11px] font-bold text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1"
          >
            Fine-tune Budget →
          </button>
        </div>
      </Card>
    </div>
  );
};
