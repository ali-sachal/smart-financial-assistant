import React, { useState } from 'react';
import { SlidersHorizontal, Sparkles, Check, RefreshCw } from 'lucide-react';
import type { CategoryBudget } from '../../types/financial';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';

interface BudgetSlidersModalProps {
  isOpen: boolean;
  onClose: () => void;
  categories: CategoryBudget[];
  onSaveAllocations: (updatedAllocations: Record<string, number>) => void;
  onApplyAiSuggestions?: () => void;
}


export const BudgetSlidersModal: React.FC<BudgetSlidersModalProps> = ({
  isOpen,
  onClose,
  categories,
  onSaveAllocations,
  onApplyAiSuggestions,
}) => {
  const [allocations, setAllocations] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    categories.forEach((cat) => {
      initial[cat.id] = cat.allocated;
    });
    return initial;
  });

  const totalAllocated = Object.values(allocations).reduce((sum, val) => sum + val, 0);
  const baselineTotal = categories.reduce((sum, c) => sum + c.allocated, 0);
  const delta = totalAllocated - baselineTotal;

  const handleSliderChange = (id: string, value: number) => {
    setAllocations((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  const handleApplyAiPreset = () => {
    const aiPreset: Record<string, number> = {};
    categories.forEach((cat) => {
      aiPreset[cat.id] = cat.aiSuggested;
    });
    setAllocations(aiPreset);
    if (onApplyAiSuggestions) {
      onApplyAiSuggestions();
    }
  };


  const handleReset = () => {
    const resetValues: Record<string, number> = {};
    categories.forEach((cat) => {
      resetValues[cat.id] = cat.allocated;
    });
    setAllocations(resetValues);
  };

  const handleSave = () => {
    onSaveAllocations(allocations);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-emerald-400" />
          <span>Interactive Budget Reallocation Sliders</span>
        </div>
      }
      description="Fine-tune monthly category ceilings. Adjustments that alter state require Tier 3 PIN authentication."
      maxWidth="2xl"
    >
      <div className="space-y-6">
        {/* Total Allocation Header Banner */}
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400">Total Monthly Discretionary Envelope</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-extrabold text-white font-mono-numbers">
                ${totalAllocated.toLocaleString()}
              </span>
              <span
                className={`text-xs font-semibold ${
                  delta === 0
                    ? 'text-emerald-400'
                    : delta > 0
                    ? 'text-rose-400'
                    : 'text-sky-400'
                }`}
              >
                {delta === 0
                  ? 'Zero-sum balanced'
                  : delta > 0
                  ? `+$${delta} over baseline`
                  : `-$${Math.abs(delta)} surplus freed`}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Reset
            </Button>
            <Button
              variant="glow"
              size="sm"
              onClick={handleApplyAiPreset}
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
            >
              Use AI Suggestion
            </Button>
          </div>
        </div>

        {/* Sliders List */}
        <div className="space-y-4 max-h-[360px] overflow-y-auto pr-1">
          {categories.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              No budget categories defined yet. Add transactions or configure monthly category ceilings (PUT /budgets/&#123;month&#125;/&#123;category&#125;) to adjust allocations.
            </div>
          ) : (
            categories.map((cat) => {
              const currentVal = allocations[cat.id] ?? cat.allocated;
              const diffWithAi = currentVal - cat.aiSuggested;

              return (
                <div
                  key={cat.id}
                  className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white">{cat.name}</span>
                      <span className="text-[10px] text-slate-400">
                        Spent so far: <strong className="text-slate-300 font-mono-numbers">${cat.spent}</strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      {diffWithAi !== 0 && (
                        <span className="text-[10px] text-slate-400">
                          AI Target: ${cat.aiSuggested}
                        </span>
                      )}
                      <span className="text-xs font-bold font-mono-numbers text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        ${currentVal}
                      </span>
                    </div>
                  </div>

                  {/* Range Slider */}
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-slate-500 font-mono-numbers w-8">$50</span>
                    <input
                      type="range"
                      min={Math.max(50, cat.spent)}
                      max={1200}
                      step={10}
                      value={currentVal}
                      onChange={(e) => handleSliderChange(cat.id, Number(e.target.value))}
                      className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500 focus:outline-none"
                    />
                    <span className="text-[10px] text-slate-500 font-mono-numbers w-10">$1,200</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Actions */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            🔒 State changes will invoke the <strong>Tier 3 PIN gatekeeper</strong>.
          </span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={handleSave}
              leftIcon={<Check className="w-4 h-4" />}
            >
              Commit Budget Allocations
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
