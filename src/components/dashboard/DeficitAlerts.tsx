import React from 'react';
import { AlertCircle, AlertTriangle, Info, ArrowRight, X } from 'lucide-react';

import type { DeficitWarning } from '../../types/financial';
import { Button } from '../ui/Button';

interface DeficitAlertsProps {
  warnings: DeficitWarning[];
  onDismiss: (id: string) => void;
  onTakeAction: (warning: DeficitWarning) => void;
}

export const DeficitAlerts: React.FC<DeficitAlertsProps> = ({
  warnings,
  onDismiss,
  onTakeAction,
}) => {
  if (warnings.length === 0) return null;

  return (
    <div className="space-y-3">
      {warnings.map((warning) => {
        const isDanger = warning.severity === 'danger';
        const isWarning = warning.severity === 'warning';

        const borderStyles = isDanger
          ? 'border-rose-500/40 bg-rose-500/10'
          : isWarning
          ? 'border-amber-500/40 bg-amber-500/10'
          : 'border-sky-500/40 bg-sky-500/10';

        const iconColor = isDanger
          ? 'text-rose-400'
          : isWarning
          ? 'text-amber-400'
          : 'text-sky-400';

        const Icon = isDanger ? AlertCircle : isWarning ? AlertTriangle : Info;

        return (
          <div
            key={warning.id}
            className={`p-4 rounded-2xl border ${borderStyles} flex flex-col sm:flex-row sm:items-center justify-between gap-4 backdrop-blur-md transition-all duration-300 animate-in fade-in`}
          >
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-xl bg-slate-950/40 shrink-0 ${iconColor}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white tracking-tight">
                    {warning.title}
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-900 text-slate-300 border border-slate-700">
                    {warning.category}
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {warning.message}
                </p>
                <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-1.5">
                  <span>Forecast date:</span>
                  <strong className="text-white">{warning.projectedDeficitDate}</strong>
                  <span>•</span>
                  <span>Impact:</span>
                  <strong className="text-emerald-400 font-mono-numbers">
                    +${warning.potentialImpact.toFixed(2)}
                  </strong>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
              <Button
                variant={isDanger ? 'danger' : 'secondary'}
                size="sm"
                onClick={() => onTakeAction(warning)}
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Execute Fix
              </Button>
              <button
                onClick={() => onDismiss(warning.id)}
                className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800/60 transition-colors"
                title="Dismiss alert"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
