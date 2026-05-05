import React, { useState, useEffect } from 'react';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { Heart, Activity, Moon } from 'lucide-react';

interface WellnessTrend {
  date: string;
  morning_heart_rate?: number | null;
  hrv_lnrmssd?: number | null;
  sleep_duration_hours?: number | null;
  sleep_quality?: number | null;
  fatigue_score?: number | null;
}

interface HRVSleepTrendProps {
  athleteId: string;
  days?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200 text-xs space-y-0.5">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-500">{entry.name}:</span>
          <span className="font-mono font-medium">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

export function HRVSleepTrend({ athleteId, days = 30 }: HRVSleepTrendProps) {
  const [trends, setTrends] = useState<WellnessTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState({ hr: true, hrv: true, sleep: true });

  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    // Dynamic import for wellness trends API
    import('../services/api').then(({ getWellnessTrends }) => {
      getWellnessTrends(athleteId, days)
        .then((data: any) => setTrends(data.trends || []))
        .catch(() => setTrends([]))
        .finally(() => setLoading(false));
    }).catch(() => setLoading(false));
  }, [athleteId, days]);

  const chartData = trends.map((t) => ({
    date: t.date.slice(5),
    fullDate: t.date,
    '晨起心率': t.morning_heart_rate,
    'HRV (LnRMSSD)': t.hrv_lnrmssd,
    '睡眠时长(h)': t.sleep_duration_hours,
  }));

  if (loading) {
    return (
      <div className="card space-y-3">
        <div className="skeleton h-4 w-40" />
        <div className="skeleton h-56 w-full rounded-lg" />
      </div>
    );
  }

  if (trends.length === 0) {
    return (
      <div className="card">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">HRV / 心率 / 睡眠趋势</h4>
        <p className="text-xs text-slate-400 text-center py-8">
          暂无健康数据，请先记录晨起健康问卷
        </p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700">HRV · 心率 · 睡眠趋势</h4>
        <div className="flex items-center gap-2">
          {([
            { key: 'hr', label: '心率', color: '#ff3b30', icon: Heart },
            { key: 'hrv', label: 'HRV', color: '#af52de', icon: Activity },
            { key: 'sleep', label: '睡眠', color: '#34c759', icon: Moon },
          ] as const).map(({ key, label, color, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setVisible((v) => ({ ...v, [key]: !v[key] }))}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium transition-colors ${
                visible[key]
                  ? 'bg-slate-100 text-slate-700'
                  : 'bg-transparent text-slate-300 line-through'
              }`}
            >
              <Icon className="w-3 h-3" style={{ color: visible[key] ? color : undefined }} />
              {label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            interval={Math.max(0, Math.floor(chartData.length / 8) - 1)}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 10 }}
            domain={['auto', 'auto']}
            label={{ value: 'bpm / ms', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#86868b' } }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 10 }}
            domain={[0, 'auto']}
            label={{ value: '小时', angle: 90, position: 'insideRight', style: { fontSize: 10, fill: '#86868b' } }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {visible.hr && (
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="晨起心率"
              stroke="#ff3b30"
              strokeWidth={1.5}
              dot={false}
              connectNulls
            />
          )}
          {visible.hrv && (
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="HRV (LnRMSSD)"
              stroke="#af52de"
              strokeWidth={1.5}
              dot={false}
              connectNulls
            />
          )}
          {visible.sleep && (
            <Bar
              yAxisId="right"
              dataKey="睡眠时长(h)"
              fill="#34c759"
              fillOpacity={0.5}
              radius={[2, 2, 0, 0]}
              maxBarSize={20}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
