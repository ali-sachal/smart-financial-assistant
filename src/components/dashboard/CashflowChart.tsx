import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { CashflowPoint } from '../../types/financial';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface CashflowChartProps {
  data: CashflowPoint[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {

  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload as CashflowPoint;
    const isProjected = dataPoint.isProjected;

    return (
      <div className="rounded-xl bg-slate-900/95 border border-slate-700/80 p-3 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-1.5 mb-2">
          <span className="text-xs font-bold text-white">{dataPoint.dayLabel} ({dataPoint.date})</span>
          {isProjected ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
              AI Projection
            </span>
          ) : (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
              Actual
            </span>
          )}
        </div>

        <div className="space-y-1 text-xs font-mono-numbers">
          {!isProjected ? (
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">Net Ledger Balance:</span>
              <span className="font-bold text-emerald-400">
                ${dataPoint.netBalance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-400">Projected Balance:</span>
                <span className="font-bold text-teal-300">
                  ${dataPoint.projectedBalance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              {dataPoint.burnRateUpper && (
                <div className="flex items-center justify-between gap-4 text-[11px] text-slate-400">
                  <span>Confidence Envelope:</span>
                  <span>${dataPoint.burnRateLower} - ${dataPoint.burnRateUpper}</span>
                </div>
              )}
            </>
          )}

          {dataPoint.income > 0 && (
            <div className="flex items-center justify-between gap-4 text-emerald-400">
              <span>Deposit Inflow:</span>
              <span>+${dataPoint.income}</span>
            </div>
          )}
          {dataPoint.expense > 0 && (
            <div className="flex items-center justify-between gap-4 text-rose-400">
              <span>Day Outflow:</span>
              <span>-${dataPoint.expense}</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const CashflowChart: React.FC<CashflowChartProps> = ({ data }) => {
  const [viewMode, setViewMode] = useState<'all' | 'actual' | 'forecast'>('all');

  const filteredData = React.useMemo(() => {
    if (viewMode === 'actual') return data.filter((d) => !d.isProjected || d.dayLabel.includes('Today'));
    if (viewMode === 'forecast') return data.filter((d) => d.isProjected || d.dayLabel.includes('Today'));
    return data;
  }, [data, viewMode]);

  return (
    <Card className="p-6 relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight m-0">
              Burn Rate & Cash Flow Curves
            </h2>
            <Badge variant="emerald" size="sm" dot>
              AI Forecast Active
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Historical ledger trajectory merged with deterministic 30-day cash-flow forecast.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900 rounded-xl p-1 border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('all')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                viewMode === 'all'
                  ? 'bg-emerald-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Full Cycle
            </button>
            <button
              onClick={() => setViewMode('actual')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                viewMode === 'actual'
                  ? 'bg-emerald-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Historical
            </button>
            <button
              onClick={() => setViewMode('forecast')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                viewMode === 'forecast'
                  ? 'bg-emerald-500 text-slate-950 font-bold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Forecast
            </button>
          </div>
        </div>
      </div>

      {/* Legend & Summary indicators */}
      <div className="flex flex-wrap items-center gap-4 mb-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
          <span className="text-slate-300 font-medium">Historical Ledger Balance</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-cyan-400 border border-cyan-300 border-dashed" />
          <span className="text-slate-300 font-medium">Projected Burn Rate Curve</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-cyan-500/20 border border-cyan-500/40" />
          <span className="text-slate-300 font-medium">95% Confidence Envelope</span>
        </div>
      </div>

      {filteredData.length === 0 ? (
        <div className="py-16 text-center text-slate-400 text-xs">
          No cash-flow forecast points available. Add transactions or run Seed Demo to calculate curves.
        </div>
      ) : (
        <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={filteredData}
            margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
          >
            <defs>
              {/* Historical Balance Gradient */}
              <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>

              {/* Projected Curve Gradient */}
              <linearGradient id="colorProjected" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>

              {/* Confidence Band Gradient */}
              <linearGradient id="colorEnvelope" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0284c7" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#0284c7" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="dayLabel"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              domain={[10000, 18000]}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Target Reserve Floor Reference */}
            <ReferenceLine
              y={14000}
              stroke="#f43f5e"
              strokeDasharray="4 4"
              label={{
                value: 'Min Floor ($14k)',
                fill: '#f43f5e',
                fontSize: 10,
                position: 'insideBottomRight',
              }}
            />

            {/* Confidence Upper/Lower Band */}
            <Area
              type="monotone"
              dataKey="burnRateUpper"
              stroke="transparent"
              fill="url(#colorEnvelope)"
              fillOpacity={1}
            />

            {/* Projected Curve */}
            <Area
              type="monotone"
              dataKey="projectedBalance"
              stroke="#06b6d4"
              strokeWidth={2.5}
              strokeDasharray="5 5"
              fill="url(#colorProjected)"
            />

            {/* Historical Balance Curve */}
            <Area
              type="monotone"
              dataKey="netBalance"
              stroke="#10b981"
              strokeWidth={3}
              fill="url(#colorBalance)"
              activeDot={{ r: 6, fill: '#10b981', stroke: '#0f172a', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    )}
  </Card>
);
};
