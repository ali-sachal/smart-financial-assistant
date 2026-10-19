import React from 'react';
import { ArrowUpRight, ArrowDownRight, Sparkles } from 'lucide-react';
import type { MetricSummary } from '../../types/financial';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface VelocityTrackerProps {
  metrics: MetricSummary;
  onOpenOptimizeModal: () => void;
}

export const VelocityTracker: React.FC<VelocityTrackerProps> = ({
  metrics,
  onOpenOptimizeModal,
}) => {
  const now = new Date();
  const cycleDay = now.getDate();
  const cycleTotalDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const cyclePercent = (cycleDay / cycleTotalDays) * 100;

  const discretionaryCap = Math.max(0, metrics.totalInflow - metrics.fixedOutflow);
  const targetDailySpend = Number((metrics.totalInflow / cycleTotalDays).toFixed(2));
  const outflowPercent = discretionaryCap > 0 ? Math.min(100, (metrics.discretionaryOutflow / discretionaryCap) * 100) : 0;
  const riskLabel = metrics.savingsRate >= 20 ? 'LOW' : metrics.savingsRate >= 0 ? 'MODERATE' : 'ELEVATED';
  const riskGrade = metrics.savingsRate >= 20 ? 'Grade A' : metrics.savingsRate >= 0 ? 'Grade B' : 'Grade C';

  return (
    <Card className="p-6 relative overflow-hidden">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight m-0">
              Income & Expense Velocity Tracker
            </h2>
            <Badge variant="emerald" size="sm" dot>
              Real-time Inflow vs Outflow
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Tracking spending acceleration against the current monthly cycle budget.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">
              Billing Cycle Status
            </span>
            <p className="text-xs font-bold text-white">
              Day {cycleDay} of {cycleTotalDays} ({cyclePercent.toFixed(0)}% elapsed)
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={onOpenOptimizeModal}
            leftIcon={<Sparkles className="w-3.5 h-3.5 text-emerald-400" />}
          >
            Adjust Allocations
          </Button>
        </div>
      </div>

      {/* Comparative Velocity Stream Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-5">
        {/* Inflow Velocity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
              <ArrowDownRight className="w-4 h-4 text-emerald-400" />
              <span>Inflow Velocity (Deposits)</span>
            </div>
            <span className="font-mono-numbers font-bold text-white">
              ${metrics.totalInflow.toLocaleString('en-US', { minimumFractionDigits: 2 })} / mo
            </span>
          </div>
          <div className="h-3 w-full bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/60">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full shadow-lg shadow-emerald-500/20 transition-all duration-700"
              style={{ width: metrics.totalInflow > 0 ? '100%' : '0%' }}
            />
          </div>
          <div className="flex justify-between items-center text-[11px] text-slate-400">
            <span>Verified Ledger Inflows</span>
            <span className="text-emerald-400 font-medium">
              {metrics.totalInflow > 0 ? '100% Verified' : 'No deposits recorded'}
            </span>
          </div>
        </div>

        {/* Discretionary Outflow Velocity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-amber-400">
              <ArrowUpRight className="w-4 h-4 text-amber-400" />
              <span>Outflow Velocity (Discretionary)</span>
            </div>
            <span className="font-mono-numbers font-bold text-white">
              ${metrics.discretionaryOutflow.toFixed(2)} / ${discretionaryCap.toFixed(2)}
            </span>
          </div>
          <div className="h-3 w-full bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/60">
            <div
              className="h-full bg-gradient-to-r from-amber-400 to-rose-500 rounded-full shadow-lg shadow-amber-500/20 transition-all duration-700"
              style={{ width: `${outflowPercent}%` }}
            />
          </div>
          <div className="flex justify-between items-center text-[11px] text-slate-400">
            <span>Pacing: ${(metrics.discretionaryOutflow / Math.max(1, cycleDay)).toFixed(1)}/day</span>
            <span className="text-amber-300 font-medium">
              Runway: Safe spend ${metrics.safeToSpendDaily}/day
            </span>
          </div>
        </div>
      </div>

      {/* Velocity Diagnostics Micro-grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-800/80">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 font-semibold uppercase">Daily Burn</span>
          <p className="text-base font-extrabold text-white font-mono-numbers mt-0.5">
            ${metrics.dailyBurnRate.toFixed(2)}
          </p>
          <span className="text-[10px] text-emerald-400">Target: ${targetDailySpend.toFixed(2)}</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 font-semibold uppercase">Discretionary Cap</span>
          <p className="text-base font-extrabold text-white font-mono-numbers mt-0.5">
            ${discretionaryCap.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </p>
          <span className="text-[10px] text-slate-400">Ceiling total</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 font-semibold uppercase">Fixed Commitments</span>
          <p className="text-base font-extrabold text-white font-mono-numbers mt-0.5">
            ${metrics.fixedOutflow.toFixed(2)}
          </p>
          <span className="text-[10px] text-slate-400">Scheduled bills</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 font-semibold uppercase">AI Risk Rating</span>
          <p className="text-base font-extrabold text-emerald-400 font-mono-numbers mt-0.5 flex items-center gap-1">
            {riskLabel} <span className="text-xs text-slate-400 font-normal">/ {riskGrade}</span>
          </p>
          <span className="text-[10px] text-emerald-400">Protected by Tier 3 PIN</span>
        </div>
      </div>
    </Card>
  );
};
