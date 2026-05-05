import React from 'react';
import {
  RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Legend, ResponsiveContainer, Tooltip
} from 'recharts';
import type { RadarChartData } from '../services/api';

interface RadarChartProps {
  data: RadarChartData;
}

export function AthleteRadarChart({ data }: RadarChartProps) {
  const chartData = data.labels.map((label, i) => ({
    label,
    current: data.current[i],
    best: data.best[i],
    normLow: data.normLow[i],
    normHigh: data.normHigh[i],
    isWeakness: data.weaknesses.includes(label),
  }));

  return (
    <div className="card space-y-4">
      <h4 className="text-sm font-semibold text-slate-700">运动员能力雷达图</h4>
      <ResponsiveContainer width="100%" height={350}>
        <RechartsRadar data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis
            dataKey="label"
            tick={({ payload, x, y, ...rest }: any) => {
              const item = chartData.find(d => d.label === payload.value);
              return (
                <text x={x} y={y} textAnchor="middle" fontSize={11} fill={item?.isWeakness ? '#ef4444' : '#475569'}>
                  {payload.value}
                </text>
              );
            }}
          />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />

          {/* Norm range (low) */}
          <Radar name="常模下限" dataKey="normLow" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.05} strokeDasharray="4 4" />

          {/* Norm range (high) */}
          <Radar name="常模上限" dataKey="normHigh" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.05} strokeDasharray="4 4" />

          {/* Best performance */}
          <Radar name="历史最佳" dataKey="best" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} />

          {/* Current */}
          <Radar name="当前水平" dataKey="current" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} />

          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </RechartsRadar>
      </ResponsiveContainer>

      {/* Weaknesses */}
      {data.weaknesses.length > 0 && (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">薄弱环节:</span>
          {data.weaknesses.map(w => (
            <span key={w} className="px-2 py-0.5 rounded-full bg-red-50 text-red-600 font-medium">
              {w}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
