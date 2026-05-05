import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Line, ComposedChart, Cell,
} from 'recharts';

interface WeeklyVolumeChartProps {
  athleteId?: string;
  teamView?: boolean;
  weeks?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200 text-xs">
      <p className="font-semibold text-slate-700 mb-1">周起始: {label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-500">{entry.name}:</span>
          <span className="font-mono font-medium">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export function WeeklyVolumeChart({ athleteId, teamView = false, weeks = 12 }: WeeklyVolumeChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    if (teamView) {
      import('../services/api').then(({ getTeamWeeklySummary }) => {
        getTeamWeeklySummary(weeks)
          .then((resp: any) => setData(resp.weekly_data || []))
          .catch(() => setData([]))
          .finally(() => setLoading(false));
      }).catch(() => setLoading(false));
    } else if (athleteId) {
      import('../services/api').then(({ getLoadSummary }) => {
        getLoadSummary(athleteId, weeks)
          .then((resp: any) => setData(resp.weekly_data || []))
          .catch(() => setData([]))
          .finally(() => setLoading(false));
      }).catch(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [athleteId, teamView, weeks]);

  const chartData = useMemo(() => {
    if (!data.length) return [];

    // Compute 4-week moving average
    const withMA = data.map((d: any, i: number) => {
      const window = data.slice(Math.max(0, i - 3), i + 1);
      const ma = window.reduce((s: number, w: any) => s + (w.total_load || 0), 0) / window.length;
      return {
        ...d,
        weekLabel: d.week_start?.slice(5) || d.week_start,
        totalLoad: d.total_load || 0,
        movingAvg: Math.round(ma),
        changePct: d.week_over_week_change_pct,
      };
    });

    return withMA;
  }, [data]);

  const avgLoad = useMemo(() => {
    if (!chartData.length) return 0;
    return chartData.reduce((s, d) => s + d.totalLoad, 0) / chartData.length;
  }, [chartData]);

  if (loading) {
    return (
      <div className="card space-y-3">
        <div className="skeleton h-4 w-36" />
        <div className="skeleton h-56 w-full rounded-lg" />
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="card">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">
          {teamView ? '全队' : '个人'}周训练量
        </h4>
        <p className="text-xs text-slate-400 text-center py-8">暂无训练数据</p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <h4 className="text-sm font-semibold text-slate-700">
        {teamView ? '全队' : '个人'}周训练量 — 最近 {weeks} 周
      </h4>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="weekLabel" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={avgLoad}
            stroke="#86868b"
            strokeDasharray="5 5"
            label={{
              value: `均值 ${avgLoad.toFixed(0)}`,
              position: 'right',
              style: { fontSize: 10, fill: '#86868b' },
            }}
          />
          <Bar dataKey="totalLoad" name="周总负荷" maxBarSize={32} radius={[3, 3, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={(entry.changePct || 0) > 10 ? '#ff3b30' : (entry.changePct || 0) < -10 ? '#ff9500' : '#007aff'}
                fillOpacity={0.75}
              />
            ))}
          </Bar>
          <Line
            type="monotone"
            dataKey="movingAvg"
            name="4周均线"
            stroke="#5856d6"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Color legend */}
      <div className="flex items-center gap-4 text-[10px] text-slate-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#007aff] opacity-75" />
          <span>周变化 ±10%以内</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#ff3b30] opacity-75" />
          <span>增加 &gt;10%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#ff9500] opacity-75" />
          <span>减少 &gt;10%</span>
        </div>
      </div>
    </div>
  );
}
