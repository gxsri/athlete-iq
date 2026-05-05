import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { TeamHeatmapResponse } from '../services/api';

interface TeamHeatmapProps {
  data: TeamHeatmapResponse;
}

function acwrColorClass(value: number): string {
  if (value > 1.5) return 'text-red-600';
  if (value > 1.3) return 'text-amber-600';
  return 'text-green-600';
}

function acwrBgClass(value: number): string {
  if (value > 1.5) return 'bg-red-50';
  if (value > 1.3) return 'bg-amber-50';
  return 'bg-green-50';
}

function rssiColorClass(level: string): string {
  if (level === '非功能性过度训练') return 'text-red-600 bg-red-50';
  if (level === '功能性过度训练') return 'text-amber-600 bg-amber-50';
  if (level === '适应性训练') return 'text-blue-600 bg-blue-50';
  return 'text-green-600 bg-green-50';
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === '上升') return <TrendingUp className="w-3.5 h-3.5 text-green-500" />;
  if (trend === '下降') return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
  return <Minus className="w-3.5 h-3.5 text-slate-400" />;
}

export function TeamHeatmap({ data }: TeamHeatmapProps) {
  const navigate = useNavigate();

  return (
    <div className="card space-y-4">
      {/* Group header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700">{data.group_name}</h4>
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-500">
            平均 ACWR: <span className={`font-bold ${acwrColorClass(data.avg_acwr)}`}>{data.avg_acwr.toFixed(2)}</span>
          </span>
          <span className={`flex items-center gap-1 ${data.at_risk_pct > 0 ? 'text-red-500' : 'text-green-500'} font-medium`}>
            {data.at_risk_pct > 0 && <AlertTriangle className="w-3 h-3" />}
            风险比例 {data.at_risk_pct}%
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-2 px-3 font-medium text-slate-500 text-xs">运动员</th>
              <th className="text-center py-2 px-3 font-medium text-slate-500 text-xs">ACWR</th>
              <th className="text-center py-2 px-3 font-medium text-slate-500 text-xs">RSSI</th>
              <th className="text-center py-2 px-3 font-medium text-slate-500 text-xs">近期负荷</th>
              <th className="text-center py-2 px-3 font-medium text-slate-500 text-xs">趋势</th>
              <th className="text-center py-2 px-3 font-medium text-slate-500 text-xs">伤病</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map(entry => (
              <tr
                key={entry.athlete_id}
                onClick={() => navigate(`/athletes/${entry.athlete_id}`)}
                className="border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                <td className="py-2.5 px-3 font-medium text-slate-700">{entry.athlete_name}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-xs font-mono font-bold ${acwrColorClass(entry.acwr)} ${acwrBgClass(entry.acwr)}`}>
                    {entry.acwr.toFixed(2)}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-xs font-mono font-bold ${rssiColorClass(entry.rssi_level)}`}>
                    {entry.rssi_score.toFixed(1)}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-center font-mono text-xs">{entry.recent_load}</td>
                <td className="py-2.5 px-3 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <TrendIcon trend={entry.perf_trend} />
                    <span className="text-xs">{entry.perf_trend}</span>
                  </div>
                </td>
                <td className="py-2.5 px-3 text-center">
                  {entry.active_injuries > 0 ? (
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-100 text-red-700 text-xs font-bold">
                      {entry.active_injuries}
                    </span>
                  ) : (
                    <span className="text-xs text-green-500">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
