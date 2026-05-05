import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { getTrainingDistribution, getTeamDistribution } from '../services/api';

interface TrainingLoadDistributionProps {
  athleteId?: string;
  teamView?: boolean;
  days?: number;
}

const TYPE_COLORS: Record<string, string> = {
  '力量': '#007aff',
  '耐力': '#34c759',
  '速度': '#ff9500',
  '技战术': '#af52de',
  '柔韧': '#ff2d55',
  '混合': '#5856d6',
  '羽毛球-技战术': '#30b0c7',
};

const FALLBACK_COLORS = ['#007aff', '#34c759', '#ff9500', '#af52de', '#ff2d55', '#5856d6', '#30b0c7'];

function getTypeColor(type: string, index: number): string {
  return TYPE_COLORS[type] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-slate-200 text-xs">
        <p className="font-semibold text-slate-700">{d.type}</p>
        <p className="text-slate-500">总负荷: {d.total_load.toLocaleString()}</p>
        <p className="text-slate-500">占比: {d.percentage}%</p>
      </div>
    );
  }
  return null;
};

const renderLegend = (props: any) => {
  const { payload } = props;
  return (
    <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2">
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-1 text-[11px] text-slate-600">
          <div
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          {entry.value}
        </div>
      ))}
    </div>
  );
};

export function TrainingLoadDistribution({
  athleteId,
  teamView = false,
  days = 90,
}: TrainingLoadDistributionProps) {
  const [distribution, setDistribution] = useState<{ type: string; total_load: number; percentage: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const fetchData = teamView
      ? getTeamDistribution(days)
      : athleteId
        ? getTrainingDistribution(athleteId, days)
        : Promise.resolve(null);

    fetchData
      .then((data: any) => {
        if (data?.distribution) {
          setDistribution(data.distribution);
        }
      })
      .catch(() => setDistribution([]))
      .finally(() => setLoading(false));
  }, [athleteId, teamView, days]);

  if (loading) {
    return (
      <div className="card space-y-3">
        <div className="skeleton h-4 w-36" />
        <div className="skeleton h-48 w-full rounded-full" />
      </div>
    );
  }

  if (distribution.length === 0) {
    return (
      <div className="card">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">训练负荷分布</h4>
        <p className="text-xs text-slate-400 text-center py-8">暂无训练数据</p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <h4 className="text-sm font-semibold text-slate-700">
        训练负荷分布 — {teamView ? '全队' : '个人'}
      </h4>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={distribution}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
            dataKey="total_load"
            nameKey="type"
          >
            {distribution.map((entry, index) => (
              <Cell
                key={index}
                fill={getTypeColor(entry.type, index)}
                stroke="#fff"
                strokeWidth={1}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={renderLegend} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
