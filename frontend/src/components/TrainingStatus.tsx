import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Activity, Moon, AlertTriangle, Minus,
} from 'lucide-react';

interface TrainingStatusProps {
  athleteId: string;
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; bgClass: string; textClass: string }> = {
  '高效训练': { icon: <TrendingUp className="w-5 h-5" />, bgClass: 'bg-emerald-50 border-emerald-200', textClass: 'text-emerald-700' },
  '维持状态': { icon: <Activity className="w-5 h-5" />, bgClass: 'bg-blue-50 border-blue-200', textClass: 'text-blue-700' },
  '恢复减量': { icon: <Moon className="w-5 h-5" />, bgClass: 'bg-sky-50 border-sky-200', textClass: 'text-sky-700' },
  '负荷偏高': { icon: <AlertTriangle className="w-5 h-5" />, bgClass: 'bg-amber-50 border-amber-200', textClass: 'text-amber-700' },
  '过度训练': { icon: <AlertTriangle className="w-5 h-5" />, bgClass: 'bg-red-50 border-red-200', textClass: 'text-red-700' },
  '状态下滑': { icon: <TrendingDown className="w-5 h-5" />, bgClass: 'bg-yellow-50 border-yellow-200', textClass: 'text-yellow-700' },
  '数据不足': { icon: <Minus className="w-5 h-5" />, bgClass: 'bg-slate-50 border-slate-200', textClass: 'text-slate-500' },
};

export function TrainingStatus({ athleteId }: TrainingStatusProps) {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    import('../services/api').then(({ getTrainingStatus }) => {
      getTrainingStatus(athleteId)
        .then(setStatus)
        .catch(() => setStatus(null))
        .finally(() => setLoading(false));
    }).catch(() => setLoading(false));
  }, [athleteId]);

  if (loading) {
    return (
      <div className="card space-y-3">
        <div className="skeleton h-4 w-28" />
        <div className="skeleton h-16 w-full" />
        <div className="grid grid-cols-3 gap-2">
          <div className="skeleton h-12" />
          <div className="skeleton h-12" />
          <div className="skeleton h-12" />
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="card">
        <h5 className="text-sm font-semibold text-slate-700 mb-2">训练状态</h5>
        <p className="text-xs text-slate-400">暂无数据</p>
      </div>
    );
  }

  const cfg = STATUS_CONFIG[status.status] || STATUS_CONFIG['数据不足'];
  const metrics = status.supporting_metrics || {};

  return (
    <div className={`card border-2 ${cfg.bgClass}`}>
      <div className="flex items-center justify-between mb-3">
        <h5 className="text-sm font-semibold text-slate-700">训练状态</h5>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${cfg.textClass} font-bold text-sm`}>
          {cfg.icon}
          {status.status}
        </div>
      </div>

      <p className="text-xs text-slate-600 mb-3 leading-relaxed">{status.description}</p>

      {/* Metrics grid */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {[
          { label: 'ACWR', value: metrics.acwr?.toFixed(2), color: metrics.acwr > 1.5 ? 'text-red-600' : metrics.acwr > 1.3 ? 'text-amber-600' : 'text-emerald-600' },
          { label: 'RSSI', value: metrics.rssi_score?.toFixed(1), color: metrics.rssi_score > 50 ? 'text-red-600' : metrics.rssi_score > 30 ? 'text-amber-600' : 'text-emerald-600' },
          { label: '急性负荷', value: metrics.acute_load?.toFixed(0), color: 'text-slate-700' },
          { label: '单调性', value: metrics.monotony?.toFixed(2), color: metrics.monotony > 2 ? 'text-red-600' : 'text-slate-700' },
        ].map((m) => (
          <div key={m.label} className={`p-2 rounded-lg bg-white/60 text-center`}>
            <div className={`text-lg font-bold ${m.color}`}>{m.value || '-'}</div>
            <div className="text-[10px] text-slate-400">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Recommendation */}
      <div className="p-2.5 rounded-lg bg-white/70 text-xs text-slate-600 leading-relaxed">
        <span className="font-medium text-slate-700">建议: </span>
        {status.recommendation}
      </div>
    </div>
  );
}
