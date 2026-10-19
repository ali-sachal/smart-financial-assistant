import React from 'react';

interface ProgressProps {
  value: number; // current spent or progress (0 - 100 or higher)
  max?: number;
  thresholdGreen?: number; // e.g. 70
  thresholdAmber?: number; // e.g. 90
  showPercent?: boolean;
  className?: string;
  barClassName?: string;
  height?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  thresholdGreen = 70,
  thresholdAmber = 90,
  showPercent = false,
  className = '',
  barClassName = '',
  height = 'md',
  animated = true,
}) => {
  const percentage = Math.min(Math.max(0, (value / max) * 100), 100);

  // Dynamic color threshold: Green -> Amber -> Red
  let statusColor = 'from-emerald-500 to-teal-400';
  let glowColor = 'shadow-emerald-500/20';

  if (percentage >= thresholdAmber) {
    statusColor = 'from-rose-500 to-pink-500';
    glowColor = 'shadow-rose-500/30';
  } else if (percentage >= thresholdGreen) {
    statusColor = 'from-amber-400 to-amber-500';
    glowColor = 'shadow-amber-500/20';
  }

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={`w-full ${className}`}>
      <div
        className={`w-full bg-slate-800/80 rounded-full overflow-hidden border border-slate-700/50 p-0.5 ${heightStyles[height]}`}
      >
        <div
          className={`h-full rounded-full bg-gradient-to-r ${statusColor} ${glowColor} shadow-md transition-all duration-500 ease-out ${
            animated ? 'relative overflow-hidden' : ''
          } ${barClassName}`}
          style={{ width: `${percentage}%` }}
        >
          {animated && (
            <div className="absolute inset-0 bg-white/20 -skew-x-12 animate-[shimmer_2s_infinite]" />
          )}
        </div>
      </div>
      {showPercent && (
        <div className="flex justify-between items-center mt-1 text-[11px] text-slate-400">
          <span>{percentage.toFixed(0)}% used</span>
          <span>{percentage > 100 ? 'Over limit!' : `${(100 - percentage).toFixed(0)}% remaining`}</span>
        </div>
      )}
    </div>
  );
};
