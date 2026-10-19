import React from 'react';
import {
  ShoppingCart,
  Utensils,
  Cloud,
  Film,
  Zap,
  Car,
  HeartPulse,
  SlidersHorizontal,
  Sparkles,
  AlertTriangle,
} from 'lucide-react';

import type { CategoryBudget } from '../../types/financial';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface CategoryListProps {
  categories: CategoryBudget[];
  onOpenSliders: () => void;
  onApplyOptimization: () => void;
}

const ICON_MAP: Record<string, React.FC<{ className?: string }>> = {
  ShoppingCart,
  Utensils,
  Cloud,
  Film,
  Zap,
  Car,
  HeartPulse,
};

export const CategoryList: React.FC<CategoryListProps> = ({
  categories,
  onOpenSliders,
  onApplyOptimization,
}) => {
  return (
    <Card className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight m-0">
              Category Allocation Ceilings
            </h2>
            <Badge variant="slate" size="sm">
              {categories.length} Active {categories.length === 1 ? 'Budget' : 'Budgets'}
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic threshold tracking: Green (&lt;70%), Amber (70-90%), Red (&gt;90% exhaustion).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenSliders}
            leftIcon={<SlidersHorizontal className="w-3.5 h-3.5 text-slate-300" />}
          >
            Reallocation Sliders
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onApplyOptimization}
            leftIcon={<Sparkles className="w-3.5 h-3.5" />}
          >
            Apply AI Plan
          </Button>
        </div>
      </div>

      {/* Category Rows */}
      {categories.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs">
          No budget categories defined yet. Use Reallocation Sliders or Seed Demo to configure monthly ceilings.
        </div>
      ) : (
        <div className="space-y-4">
          {categories.map((cat) => {
            const Icon = ICON_MAP[cat.icon] || ShoppingCart;
            const percentage = cat.allocated > 0 ? (cat.spent / cat.allocated) * 100 : 0;
          const isCritical = percentage >= 90;
          const isWarning = percentage >= 70 && percentage < 90;

          return (
            <div
              key={cat.id}
              className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all duration-200"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border border-white/10"
                    style={{ backgroundColor: `${cat.color}22`, color: cat.color }}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{cat.name}</span>
                      {cat.isAlert && (
                        <span className="flex items-center gap-1 text-[10px] text-rose-400 font-bold px-1.5 py-0.2 rounded bg-rose-500/15 border border-rose-500/30">
                          <AlertTriangle className="w-3 h-3" /> Velocity Alert
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                      <span>Velocity ratio:</span>
                      <strong className={cat.velocity > 1.2 ? 'text-rose-400 font-mono-numbers' : 'text-slate-300 font-mono-numbers'}>
                        {cat.velocity}x
                      </strong>
                      <span className="text-slate-400">•</span>
                      <span>AI Suggested:</span>
                      <strong className="text-emerald-400 font-mono-numbers">
                        ${cat.aiSuggested}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="text-right font-mono-numbers">
                  <div className="flex items-baseline gap-1 justify-end">
                    <span className="text-sm font-bold text-white">${cat.spent}</span>
                    <span className="text-xs text-slate-400">/ ${cat.allocated}</span>
                  </div>
                  <span
                    className={`text-[11px] font-semibold ${
                      isCritical
                        ? 'text-rose-400'
                        : isWarning
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {percentage.toFixed(0)}% spent
                  </span>
                </div>
              </div>

              {/* Dynamic Threshold Bar */}
              <Progress
                value={cat.spent}
                max={cat.allocated}
                thresholdGreen={70}
                thresholdAmber={90}
                height="md"
              />
            </div>
          );
        })}
      </div>
    )}
  </Card>
);
};
