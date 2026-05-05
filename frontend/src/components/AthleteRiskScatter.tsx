import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell, Legend } from 'recharts';

interface Props { data: any[]; onAthleteClick?: (id: string) => void; }

const RISK_COLORS: Record<string, string> = {
  '不正常': '#e74c3c',
  '亚正常': '#f39c12',
  '正常': '#27ae60',
};
const RISK_ORDER: Record<string, number> = { '不正常': 3, '亚正常': 2, '正常': 1 };
const RISK_GROUPS = ['不正常', '亚正常', '正常'];

function classify(acwr: number, rssi: number, shoulderRisk: number, kneeRisk: number): string {
  if (acwr > 1.5 || acwr < 0.7 || rssi > 40 || shoulderRisk > 70 || kneeRisk > 70) return '不正常';
  if (acwr > 1.3 || acwr < 0.8 || rssi > 20 || shoulderRisk > 45 || kneeRisk > 45) return '亚正常';
  return '正常';
}

function riskDesc(level: string): string {
  if (level === '不正常') return '需立即干预，减量50%，安排康复评估';
  if (level === '亚正常') return '需关注，建议调整负荷，增加恢复日';
  return '状态良好，保持当前训练计划';
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="bg-white dark:bg-slate-800 px-3 py-2 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 text-xs">
      <p className="font-bold text-slate-700 dark:text-slate-200">{d.name}</p>
      <p className="text-slate-500 dark:text-slate-400">项目: {d.sport}</p>
      <p className="text-slate-500 dark:text-slate-400">ACWR: {d.acwr.toFixed(2)}</p>
      <p className="text-slate-500 dark:text-slate-400">综合风险分: {d.riskScore.toFixed(0)}</p>
      <p className="text-slate-500 dark:text-slate-400">RSSI: {d.rssi.toFixed(0)}</p>
      {d.shoulderRisk > 30 && <p className="text-slate-500 dark:text-slate-400">肩部风险: {d.shoulderRisk.toFixed(0)}</p>}
      {d.kneeRisk > 30 && <p className="text-slate-500 dark:text-slate-400">膝部风险: {d.kneeRisk.toFixed(0)}</p>}
      <p style={{ color: RISK_COLORS[d.riskLevel] || '#95a5a6', fontWeight: 600 }}>{d.riskLevel} — {riskDesc(d.riskLevel)}</p>
    </div>
  );
}

export function AthleteRiskScatter({ data, onAthleteClick }: Props) {
  if (!data?.length) return <p className="text-xs text-slate-400 text-center py-16">暂无运动员数据</p>;

  const classified = data.map(d => ({
    ...d,
    riskLevel: classify(d.acwr, d.rssi, d.shoulderRisk || 0, d.kneeRisk || 0),
  }));

  const sorted = [...classified].sort((a, b) => (RISK_ORDER[b.riskLevel] || 0) - (RISK_ORDER[a.riskLevel] || 0));

  const counts = { '不正常': 0, '亚正常': 0, '正常': 0 };
  classified.forEach(d => { counts[d.riskLevel]++; });

  return (
    <div>
      {/* Risk summary strip */}
      <div className="flex gap-3 mb-3 text-[11px]">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS['不正常'] }} />不正常: {counts['不正常']}人</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS['亚正常'] }} />亚正常: {counts['亚正常']}人</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS['正常'] }} />正常: {counts['正常']}人</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.4} />
          <XAxis type="number" dataKey="acwr" name="ACWR" domain={[0.4, 2.0]}
            tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            label={{ value: 'ACWR (急慢性负荷比)', position: 'bottom', offset: 8, style: { fontSize: 11, fill: '#94a3b8' } }} />
          <YAxis type="number" dataKey="riskScore" name="综合风险分" domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false}
            label={{ value: '综合风险分', angle: -90, position: 'left', offset: 0, style: { fontSize: 11, fill: '#94a3b8' } }} />
          <ZAxis type="number" dataKey="rssi" range={[40, 240]} name="RSSI" />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />

          {/* Safe zone reference */}
          <ReferenceLine x={0.8} stroke="#f39c12" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.4}
            label={{ value: '0.8', position: 'top', style: { fontSize: 9, fill: '#f39c12' } }} />
          <ReferenceLine x={1.3} stroke="#e74c3c" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.4}
            label={{ value: '1.3', position: 'top', style: { fontSize: 9, fill: '#e74c3c' } }} />
          {/* Risk score threshold */}
          <ReferenceLine y={40} stroke="#f39c12" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.25}
            label={{ value: '亚正常线', position: 'right', style: { fontSize: 9, fill: '#f39c12' } }} />
          <ReferenceLine y={70} stroke="#e74c3c" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.25}
            label={{ value: '高风险线', position: 'right', style: { fontSize: 9, fill: '#e74c3c' } }} />

          <Legend wrapperStyle={{ fontSize: 11 }} />
          {RISK_GROUPS.map(level => {
            const items = sorted.filter(d => d.riskLevel === level);
            if (!items.length) return null;
            return (
              <Scatter key={level} name={level} data={items}
                onClick={(d: any) => onAthleteClick?.(d?.athlete_id)} cursor="pointer">
                {items.map((d, i) => (
                  <Cell key={i} fill={RISK_COLORS[level]} fillOpacity={0.7}
                    stroke={RISK_COLORS[level]} strokeWidth={1} />
                ))}
              </Scatter>
            );
          })}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
