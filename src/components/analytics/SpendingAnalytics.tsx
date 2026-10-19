import React from 'react';
import {
  PieChart as RechartsPie,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { CategoryBudget, Transaction } from '../../types/financial';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface SpendingAnalyticsProps {
  categories: CategoryBudget[];
  transactions: Transaction[];
  onOpenCopilot: () => void;
  onOpenOptimizeModal?: () => void;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="rounded-xl bg-slate-900 border border-slate-700 p-2.5 text-xs shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-2 mb-1">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: data.color }}
          />
          <span className="font-bold text-white">{data.name}</span>
        </div>
        <div className="space-y-0.5 text-slate-300 font-mono-numbers">
          <div>Spent: <strong className="text-white">${data.spent}</strong></div>
          <div>Share: <strong className="text-emerald-400">{data.percentage}%</strong> of total</div>
        </div>
      </div>
    );
  }
  return null;
};

export const SpendingAnalytics: React.FC<SpendingAnalyticsProps> = ({
  categories,
  transactions,
  onOpenCopilot,
}) => {
  const totalSpent = categories.reduce((sum, c) => sum + c.spent, 0);

  const pieData = categories
    .filter((cat) => cat.spent > 0)
    .map((cat) => ({
      name: cat.name,
      value: cat.spent,
      spent: cat.spent,
      color: cat.color,
      percentage: totalSpent > 0 ? ((cat.spent / totalSpent) * 100).toFixed(1) : '0',
    }));

  const anomalousTransactions = transactions.filter((t) => t.isAnomaly);

  return (
    <div className="space-y-6">
      {/* Top Row: Donut Breakdown + Subscription Spikes */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Donut Chart (7 cols) */}
        <Card className="p-6 lg:col-span-7 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white tracking-tight">
                    Expense Breakdown & Category Share
                  </h3>
                  <Badge variant="emerald" size="sm">
                    Live Distribution
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Proportional share of discretionary outflow with anomalous category weighting.
                </p>
              </div>
            </div>

            <div className="h-64 relative flex items-center justify-center">
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={105}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.color}
                          stroke="#0f172a"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </RechartsPie>
                </ResponsiveContainer>
              ) : (
                <div className="text-center p-6 text-slate-400 text-xs">
                  No category spending recorded yet.
                </div>
              )}

              {/* Center Metric Display */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">
                  Discretionary
                </span>
                <span className="text-xl font-extrabold text-white font-mono-numbers">
                  ${totalSpent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="text-[10px] text-emerald-400 font-semibold">
                  {categories.length} Categories
                </span>
              </div>
            </div>
          </div>

          {/* Category Chips Bar below donut */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-4 border-t border-slate-800/80 text-xs">
            {pieData.length > 0 ? (
              pieData.slice(0, 6).map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-900/50 border border-slate-800"
                >
                  <div
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <div className="truncate">
                    <span className="text-slate-300 truncate block text-[11px] font-medium">
                      {item.name}
                    </span>
                    <span className="text-slate-400 text-[10px] font-mono-numbers">
                      ${item.spent.toFixed(2)} ({item.percentage}%)
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full py-2 text-center text-slate-500 text-xs">
                No active category expenditures.
              </div>
            )}
          </div>
        </Card>

        {/* Anomaly & Spikes Inspector (5 cols) */}
        <Card className="p-6 lg:col-span-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  Anomalous Outflow Spikes
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  AI detected non-routine charges and inactive subscriptions.
                </p>
              </div>
              <Badge variant={anomalousTransactions.length > 0 ? 'rose' : 'slate'} size="sm">
                {anomalousTransactions.length} Flagged
              </Badge>
            </div>

            <div className="space-y-3">
              {anomalousTransactions.length > 0 ? (
                anomalousTransactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="p-3.5 rounded-xl bg-slate-900/60 border border-rose-500/30 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{tx.merchant}</span>
                      <span className="text-xs font-bold text-rose-400 font-mono-numbers">
                        -${tx.amount.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300">{tx.notes}</p>
                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                      <span>{tx.date}</span>
                      <span className="text-emerald-400 font-medium">
                        Payment: {tx.paymentMethod}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <p className="text-xs font-semibold text-white">No Outflow Spikes Detected</p>
                  <p className="text-[11px] text-slate-400">
                    All current cycle transactions align with expected merchant patterns and category limits.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80 mt-4 flex items-center justify-between">
            <span className="text-xs text-slate-400">Want AI to evaluate your finances?</span>
            <Button variant="glow" size="sm" onClick={onOpenCopilot}>
              Ask Copilot
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
