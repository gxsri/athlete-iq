import React from 'react';
import { Moon, Zap, Activity, Brain } from 'lucide-react';

interface ReadinessCardProps {
  sleep: number;
  soreness: number;
  fatigue: number;
  stress: number;
  color: string;
  date: string;
}

const colorMap: Record<string, { bg: string; text: string; ring: string; label: string }> = {
  green: { bg: 'bg-green-100', text: 'text-green-700', ring: 'ring-green-400', label: '良好' },
  yellow: { bg: 'bg-yellow-100', text: 'text-yellow-700', ring: 'ring-yellow-400', label: '注意' },
  red: { bg: 'bg-red-100', text: 'text-red-700', ring: 'ring-red-400', label: '预警' },
};

function ScoreBar({ label, value, max, icon: Icon, reverse }: { label: string; value: number; max: number; icon: React.ElementType; reverse?: boolean }) {
  const pct = (value / max) * 100;
  let barColor;
  if (reverse) {
    barColor = value >= 4 ? 'bg-green-500' : value >= 3 ? 'bg-yellow-500' : 'bg-red-500';
  } else {
    barColor = value >= 4 ? 'bg-red-500' : value >= 3 ? 'bg-yellow-500' : 'bg-green-500';
  }
  return (
    <div>
      <div className="flex justify-between items-center text-xs mb-0.5">
        <span className="flex items-center gap-1 text-slate-500">
          <Icon className="w-3 h-3" />{label}
        </span>
        <span className="font-mono text-slate-600">{value}/{max}</span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function ReadinessCard({ sleep, soreness, fatigue, stress, color, date }: ReadinessCardProps) {
  const cfg = colorMap[color] || colorMap.yellow;

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          每日准备状态
        </h4>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${cfg.bg} ${cfg.text}`}>
          <div className={`w-2 h-2 rounded-full ring-2 ${cfg.ring}`} style={{ backgroundColor: color }} />
          {cfg.label}
        </div>
      </div>
      <p className="text-xs text-slate-400">{date}</p>
      <div className="space-y-2">
        <ScoreBar label="睡眠质量" value={sleep} max={5} icon={Moon} reverse />
        <ScoreBar label="肌肉酸痛" value={soreness} max={5} icon={Activity} />
        <ScoreBar label="疲劳程度" value={fatigue} max={5} icon={Zap} />
        <ScoreBar label="压力/动力" value={stress} max={5} icon={Brain} />
      </div>
    </div>
  );
}
