import React from 'react';

interface RiskGaugeProps {
  score: number;       // 0-100, higher = more risk
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function RiskGauge({ score, size = 'md', showLabel = true }: RiskGaugeProps) {
  const dims = size === 'sm' ? 80 : size === 'lg' ? 160 : 120;
  const strokeW = size === 'sm' ? 6 : 10;
  const radius = (dims - strokeW) / 2;
  const circumference = 2 * Math.PI * radius;
  const cx = dims / 2;
  const cy = dims / 2;
  const fontSize = size === 'sm' ? 14 : size === 'lg' ? 28 : 20;

  // Color: green (0-30) -> yellow (30-70) -> red (70-100)
  let color = '#22c55e';
  let riskLabel = '低风险';
  if (score >= 70) { color = '#ef4444'; riskLabel = '高风险'; }
  else if (score >= 30) { color = '#f59e0b'; riskLabel = '中等风险'; }

  // Arc calculation: start at top (12 o'clock), clockwise
  const pct = Math.min(100, Math.max(0, score)) / 100;
  const offset = circumference * (1 - pct);

  return (
    <div className="inline-flex flex-col items-center gap-0.5">
      <svg width={dims} height={dims} viewBox={`0 0 ${dims} ${dims}`}>
        {/* Background circle */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke="#e2e8f0" strokeWidth={strokeW}
        />
        {/* Gradient definition */}
        <defs>
          <linearGradient id={`riskGrad-${size}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="40%" stopColor="#facc15" />
            <stop offset="70%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        {/* Foreground arc (rotated to start at top) */}
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke={`url(#riskGrad-${size})`} strokeWidth={strokeW}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cy})`}
        />
        {/* Score text */}
        <text x={cx} y={cy + fontSize * 0.35} textAnchor="middle" fontSize={fontSize} fontWeight="bold" fill="#1e293b">
          {Math.round(score)}%
        </text>
      </svg>
      {showLabel && <span className="text-xs font-medium" style={{ color }}>{riskLabel}</span>}
    </div>
  );
}
