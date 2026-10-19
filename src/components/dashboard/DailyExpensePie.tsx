import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Sparkles, CalendarDays } from 'lucide-react';
import type { CategoryBudget } from '../../types/financial';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface DailyExpensePieProps {
  categories: CategoryBudget[];
}

// Custom tooltip for the pie chart
const CustomPieTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.[0]) return null;
  const data = payload[0].payload;
  return (
    <div className="bg-slate-900/95 backdrop-blur-lg border border-slate-700/80 rounded-xl px-4 py-3 shadow-2xl">
      <p className="text-xs font-bold text-white mb-1">{data.fullName}</p>
      <p className="text-sm font-mono-numbers text-emerald-400 font-bold">${data.value.toFixed(2)}</p>
      <p className="text-[10px] text-slate-400 mt-0.5">
        {data._total > 0 ? ((data.value / data._total) * 100).toFixed(1) : 0}% of daily spend
      </p>
    </div>
  );
};

export const DailyExpensePie: React.FC<DailyExpensePieProps> = ({ categories }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const currentDay = Math.max(1, new Date().getDate());
  const rawData = categories
    .filter((c) => c.spent > 0)
    .map((cat) => ({
      name: cat.name.split(' ')[0],
      fullName: cat.name,
      value: Number((cat.spent / currentDay).toFixed(2)),
      color: cat.color || '#10b981',
      isAlert: cat.isAlert,
    }))
    .sort((a, b) => b.value - a.value);

  const totalToday = rawData.reduce((s, d) => s + d.value, 0);
  const todayData = rawData.map((d) => ({ ...d, _total: totalToday }));
  const alertCategory = categories.find((c) => c.isAlert);

  const formattedDate = new Date().toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Card className="p-6 relative overflow-hidden">
      {/* Decorative glow */}
      <div className="absolute -top-20 -right-20 w-56 h-56 rounded-full bg-emerald-500/8 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-40 h-40 rounded-full bg-cyan-500/6 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight m-0">
              Today's Spending Breakdown
            </h2>
            <Badge variant="emerald" size="sm" dot>
              Live
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
            <CalendarDays className="w-3.5 h-3.5 text-slate-500" />
            {formattedDate} — Daily category distribution
          </p>
        </div>
        <div className="text-right">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Total Today</span>
          <p className="text-xl font-extrabold text-white font-mono-numbers mt-0.5">
            ${totalToday.toFixed(2)}
          </p>
        </div>
      </div>

      {todayData.length === 0 ? (
        <div className="py-12 text-center text-slate-400 text-xs">
          No category expenses recorded for the current cycle yet. Add transactions or seed demo data to view breakdowns.
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row items-center gap-6">
          {/* Pie Chart */}
          <div className="w-full lg:w-1/2 h-[280px] relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={todayData}
                  cx="50%"
                  cy="50%"
                  innerRadius={62}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  onMouseEnter={(_, index) => setActiveIndex(index)}
                  strokeWidth={0}
                  animationBegin={0}
                  animationDuration={800}
                >
                  {todayData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      fillOpacity={activeIndex === index ? 1 : 0.7}
                      stroke={activeIndex === index ? entry.color : 'transparent'}
                      strokeWidth={activeIndex === index ? 3 : 0}
                      style={{
                        filter: activeIndex === index ? `drop-shadow(0 0 10px ${entry.color}60)` : 'none',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Center label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Active</span>
              <span className="text-lg font-extrabold text-white font-mono-numbers">
                {todayData[activeIndex]?.fullName.split(' ')[0] || 'Total'}
              </span>
              <span className="text-xs font-bold text-emerald-400 font-mono-numbers">
                ${todayData[activeIndex]?.value.toFixed(2) || totalToday.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Interactive Legend List */}
          <div className="w-full lg:w-1/2 space-y-1.5">
            {todayData.map((item, idx) => {
              const isActive = activeIndex === idx;
              const pct = totalToday > 0 ? ((item.value / totalToday) * 100).toFixed(1) : 0;
              return (
                <button
                  key={item.fullName}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl transition-all duration-200 text-left ${
                    isActive
                      ? 'bg-slate-800/90 border border-slate-700/80 shadow-sm'
                      : 'bg-slate-900/40 border border-transparent hover:bg-slate-800/50'
                  }`}
                  onMouseEnter={() => setActiveIndex(idx)}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full shrink-0 ring-2 ring-offset-1 ring-offset-slate-950"
                      style={{ backgroundColor: item.color }}
                    />
                    <div>
                      <span className="text-xs font-semibold text-white">{item.fullName}</span>
                      <span className="block text-[10px] text-slate-400">{pct}% of daily spend</span>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono-numbers text-white">
                    ${item.value.toFixed(2)}
                  </span>
                </button>
              );
            })}

            {/* Dynamic AI insight chip */}
            <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/20 mt-3">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span className="text-[11px] text-emerald-300/90 leading-relaxed">
                <strong>AI Insight:</strong>{' '}
                {alertCategory
                  ? `${alertCategory.name} is pacing near its ceiling. Consider monitoring discretionary spend.`
                  : 'All monitored categories are currently pacing within safe thresholds.'}
              </span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
