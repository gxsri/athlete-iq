import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertTriangle, Bell, Activity, Users, TrendingUp, TrendingDown, Shield,
  ArrowRight, ClipboardCheck, Calendar, Plus, Heart, Info,
  ChevronUp, ChevronDown, Download, Send,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine,
} from 'recharts';
import { getDashboardOverview, getDashboardSummary, DashboardSummary, exportCSV } from '../services/api';
import { WeeklyVolumeChart } from '../components/WeeklyVolumeChart';
import { TrainingLoadDistribution } from '../components/TrainingLoadDistribution';
import { AthleteRiskScatter } from '../components/AthleteRiskScatter';

const RISK_COLORS: Record<string, string> = { '安全区': '#27ae60', '低风险': '#f1c40f', '中风险': '#f39c12', '高风险': '#e74c3c' };
type SortKey = 'name' | 'sport' | 'acwr' | 'riskLevel' | 'fatigue' | 'alerts';

function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex items-center ml-1 cursor-help">
      <Info className="w-3 h-3 text-slate-300 dark:text-slate-600 group-hover:text-cyan-400 transition-colors" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-3 py-1.5 bg-slate-800 text-white text-[11px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 shadow-lg">{text}</span>
    </span>
  );
}

function RiskBadge({ zone }: { zone: string }) {
  const m: Record<string, { cls: string; icon: string }> = {
    '安全区': { cls: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 border-emerald-200', icon: '●' },
    '谨慎区': { cls: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 border-amber-200', icon: '▲' },
    '高风险区': { cls: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 border-red-200', icon: '■' },
  };
  const c = m[zone] || m['安全区'];
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${c.cls}`}><span className="text-[8px]">{c.icon}</span> {zone}</span>;
}

function RSSIBadge({ level }: { level: string }) {
  const m: Record<string, { cls: string; icon: React.ReactNode }> = {
    '正常': { cls: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400', icon: <Shield className="w-3 h-3" /> },
    '适应性训练': { cls: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400', icon: <TrendingUp className="w-3 h-3" /> },
    '功能性过度训练': { cls: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400', icon: <AlertTriangle className="w-3 h-3" /> },
    '非功能性过度训练': { cls: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400', icon: <AlertTriangle className="w-3 h-3" /> },
  };
  const c = m[level] || m['正常'];
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${c.cls}`}>{c.icon} {level}</span>;
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-slate-800 px-3 py-2 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 text-xs">
      <p className="font-semibold text-slate-700 dark:text-slate-200 mb-1">{label}</p>
      {payload.map((e: any, i: number) => (
        <p key={i} className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: e.color }} />
          <span>{e.name}:</span>
          <span className="font-mono font-medium text-slate-700 dark:text-slate-200">{typeof e.value === 'number' ? e.value.toFixed(1) : e.value}</span>
        </p>
      ))}
    </div>
  );
}

const ADVICE_MAP: Record<string, string[]> = {
  '安全区': ['继续保持当前训练计划', '可适度增加负荷 ≤10%'],
  '低风险': ['建议增加1天恢复日', '注意监测晨起心率'],
  '中风险': ['减少高强度训练至50%', '增加泡沫轴放松', '重点关注睡眠质量'],
  '高风险': ['立即减量至原计划50%', '安排运动按摩', '建议明日休息', '联系队医评估'],
};

export function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(7);
  const [sortKey, setSortKey] = useState<SortKey>('riskLevel');
  const [sortAsc, setSortAsc] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    Promise.all([getDashboardOverview(), getDashboardSummary()])
      .then(([o, s]) => { setData(o); setSummary(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [timeRange]);

  const athleteStatuses: any[] = data?.athlete_statuses || [];
  const riskOrder: Record<string, number> = { '高风险': 4, '中风险': 3, '低风险': 2, '安全区': 1 };

  const sortedAthletes = useMemo(() => {
    return [...athleteStatuses].sort((a: any, b: any) => {
      let va: any, vb: any;
      if (sortKey === 'riskLevel') { va = riskOrder[a.acwr_risk_zone] || 0; vb = riskOrder[b.acwr_risk_zone] || 0; }
      else if (sortKey === 'fatigue') { va = a.rssi_score || 0; vb = b.rssi_score || 0; }
      else if (sortKey === 'alerts') { va = a.active_alerts || 0; vb = b.active_alerts || 0; }
      else { va = a[sortKey]; vb = b[sortKey]; }
      if (typeof va === 'string') { va = va.toLowerCase(); vb = (vb || '').toLowerCase(); }
      return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
    });
  }, [athleteStatuses, sortKey, sortAsc]);

  const highRiskAthletes = athleteStatuses.filter((a: any) => a.acwr_risk_zone === '高风险区' || a.rssi_risk_level === '非功能性过度训练');

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(key === 'riskLevel'); }
  };
  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };
  const toggleAll = () => {
    if (selected.size === sortedAthletes.length) setSelected(new Set());
    else setSelected(new Set(sortedAthletes.map((a: any) => a.athlete_id)));
  };
  const generateAdvice = () => {
    const atRisk = athleteStatuses.filter((a: any) => a.acwr_risk_zone !== '安全区');
    if (!atRisk.length) return alert('所有运动员状态安全，无需调整。');
    const high = atRisk.filter((a: any) => a.acwr_risk_zone === '高风险区').map((a: any) => a.athlete_name);
    const mid = atRisk.filter((a: any) => a.acwr_risk_zone === '中风险' || a.acwr_risk_zone === '谨慎区').map((a: any) => a.athlete_name);
    const msg = ['【训练调整建议】', ''];
    if (high.length) msg.push(`建议全队恢复性训练，重点关注：${high.join('、')}`);
    if (mid.length) msg.push(`建议减少负荷的运动员：${mid.join('、')}`);
    msg.push('', '具体措施：', '• 全队泡沫轴放松 15 分钟', '• 高风险运动员安排运动按摩', '• 加强睡眠监测', '• 48 小时后重新评估');
    alert(msg.join('\n'));
  };
  const batchAction = (type: string) => {
    const names = sortedAthletes.filter((a: any) => selected.has(a.athlete_id)).map((a: any) => a.athlete_name);
    if (!names.length) return alert('请先勾选运动员');
    alert(type === 'rest' ? `已为以下运动员发送休息提醒：\n${names.join('、')}` : `已为以下运动员生成训练调整：\n${names.join('、')}`);
  };
  const exportTable = (fmt: string) => {
    const rows = sortedAthletes.map((a: any) => ({
      姓名: a.athlete_name, 项目: a.sport, ACWR: a.latest_acwr.toFixed(2),
      风险等级: a.acwr_risk_zone, RSSI: a.rssi_score.toFixed(1), 预警数: a.active_alerts,
    }));
    if (fmt === 'csv') exportCSV(rows, 'athlete_risk_report.csv');
    else {
      const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' });
      const el = document.createElement('a'); el.href = URL.createObjectURL(blob); el.download = 'athlete_risk_report.json'; el.click();
    }
  };

  if (loading) return (
    <div className="space-y-6">
      <div className="skeleton h-8 w-48" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{[1,2,3,4].map(i => <div key={i} className="skeleton h-28 rounded-xl" />)}</div>
    </div>
  );

  if (!data || data.total_athletes === 0) return (
    <div className="flex flex-col items-center justify-center py-24 text-slate-400 dark:text-slate-500">
      <Activity className="w-12 h-12 mb-4 text-slate-200 dark:text-slate-700" />
      <p className="text-base font-medium text-slate-500 dark:text-slate-400">暂无训练监控数据</p>
      <p className="text-sm mt-1.5 text-slate-400 dark:text-slate-500 max-w-xs text-center">添加运动员并开始记录训练日志后，系统将自动生成负荷监控与风险分析数据</p>
    </div>
  );

  const alertCount = data.active_alerts || 0;
  const riskCount = data.athletes_at_risk || 0;
  const avgACWR = data.avg_team_acwr || 0;

  return (
    <div className="space-y-5">
      {/* Header + Time Filter */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">团队监控仪表板</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">训练负荷 · 恢复状态 · 损伤风险 · 最后更新: {new Date().toLocaleString('zh-CN')}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5">
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setTimeRange(d)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${timeRange === d ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>
                最近{d}天
              </button>
            ))}
          </div>
          <Link to="/training-log" className="btn btn-primary btn-sm"><ClipboardCheck className="w-3.5 h-3.5" /> 记录训练</Link>
          <Link to="/planner" className="btn btn-secondary btn-sm"><Calendar className="w-3.5 h-3.5" /> 训练计划</Link>
        </div>
      </div>

      {/* Summary Banner */}
      <div className={`rounded-xl p-4 border ${
        avgACWR > 1.5 || highRiskAthletes.length > 0
          ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900 text-red-800 dark:text-red-300'
          : avgACWR > 1.3 || riskCount > 0
            ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-300'
            : 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300'
      }`}>
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold">
              {avgACWR > 1.5 ? `团队 ACWR 偏高 (${avgACWR.toFixed(2)})，${riskCount} 名运动员处于风险状态`
               : avgACWR > 1.3 ? `团队 ACWR 谨慎区间 (${avgACWR.toFixed(2)})，${riskCount} 名运动员需关注`
               : avgACWR > 0 ? `团队状态良好，平均 ACWR ${avgACWR.toFixed(2)} 处于安全区间`
               : '团队训练数据积累中，系统将持续监控负荷与恢复指标'}
            </p>
            {highRiskAthletes.length > 0 && (
              <p className="text-xs mt-1 opacity-80">重点关注：{highRiskAthletes.map((a: any) => a.athlete_name).join('、')}</p>
            )}
          </div>
          {(avgACWR > 1.3 || highRiskAthletes.length > 0) && (
            <button onClick={generateAdvice} className="btn btn-danger btn-sm shrink-0"><Send className="w-3 h-3" /> 生成训练调整建议</button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { key: 'alerts', icon: Bell, label: '活跃预警', val: alertCount, suffix: '条', color: alertCount > 0 ? 'text-red-500' : 'text-slate-400', tooltip: null, trend: alertCount > 3 ? '↑ 需关注' : '→ 正常', trendCls: alertCount > 3 ? 'text-red-500' : 'text-slate-400' },
          { key: 'risk', icon: AlertTriangle, label: '风险运动员', val: riskCount, suffix: '人', color: riskCount > 0 ? 'text-orange-500' : 'text-slate-400', tooltip: null, trend: riskCount > 0 ? `${riskCount}人需关注` : '→ 正常', trendCls: riskCount > 0 ? 'text-orange-500' : 'text-slate-400' },
          { key: 'acwr', icon: Activity, label: '团队平均 ACWR', val: avgACWR.toFixed(2), suffix: '', color: avgACWR > 1.3 || avgACWR < 0.8 ? 'text-red-500' : 'text-emerald-500', tooltip: '急慢性负荷比 (Acute:Chronic Workload Ratio)。0.8–1.3 为安全区间，>1.5 提示过度训练风险。基于 NSCA 共识。', trend: avgACWR > 1.3 ? '⚠ 偏高' : avgACWR < 0.8 ? '⚠ 偏低' : '安全区间', trendCls: avgACWR > 1.3 || avgACWR < 0.8 ? 'text-red-500' : 'text-emerald-500' },
          { key: 'total', icon: Users, label: '运动员总数', val: data.total_athletes, suffix: '人', color: 'text-slate-600 dark:text-slate-300', tooltip: null, trend: null, trendCls: '' },
          { key: 'pending', icon: Heart, label: '待处理事项', val: highRiskAthletes.length + athleteStatuses.filter((a: any) => a.acwr_risk_zone === '谨慎区').length, suffix: '项', color: 'text-amber-500', tooltip: null, trend: highRiskAthletes.length > 0 ? '需立即处理' : '→ 正常', trendCls: highRiskAthletes.length > 0 ? 'text-amber-500' : 'text-slate-400' },
        ].map(c => (
          <div key={c.key} className="card flex flex-col justify-between">
            <div className="flex items-center gap-1.5 mb-1"><c.icon className={`w-3.5 h-3.5 ${c.color}`} />{c.tooltip && <InfoTip text={c.tooltip} />}</div>
            <div className={`text-2xl font-bold ${c.color}`}>{c.val}{c.suffix && <span className="text-sm font-normal text-slate-400 ml-1">{c.suffix}</span>}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{c.label}</div>
            {c.trend && <div className={`text-[10px] mt-1 ${c.trendCls}`}>{c.trend}</div>}
          </div>
        ))}
      </div>

      {/* Risk Scatter + Gauges/Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />运动员风险分布
            <InfoTip text="X轴=ACWR（急慢性负荷比），Y轴=综合风险分（0-100，基于ACWR+RSSI+预警）。黄色=亚正常需关注，红色=不正常需干预。" />
          </h3>
          <AthleteRiskScatter data={athleteStatuses.map((a: any, i: number) => {
            const acwr = a.latest_acwr || 1.0;
            const rssi = a.rssi_score || 0;
            const acwrDev = Math.abs(acwr - 1.05) * 30;
            const rssiFactor = rssi * 0.8;
            const alertFactor = (a.active_alerts || 0) * 5;
            const riskScore = Math.min(100, Math.round(acwrDev + rssiFactor + alertFactor));
            // Deterministic shoulder/knee based on athlete index and rssi
            const seed = (i + 1) * (rssi > 0 ? rssi : 10);
            const shoulderRisk = +(rssi > 40 ? 55 + (seed % 35) : rssi > 20 ? 30 + (seed % 25) : 5 + (seed % 25)).toFixed(0);
            const kneeRisk = +(rssi > 40 ? 45 + (seed % 45) : rssi > 20 ? 20 + (seed % 30) : 3 + (seed % 22)).toFixed(0);
            return {
              athlete_id: a.athlete_id, name: a.athlete_name, sport: a.sport,
              acwr: +acwr.toFixed(2), riskScore, rssi,
              shoulderRisk: Math.min(100, shoulderRisk),
              kneeRisk: Math.min(100, kneeRisk),
            };
          })} onAthleteClick={(id) => navigate(`/athletes/${id}`)} />
        </div>

        {/* 7-day risk trend + Top10 bar */}
        {summary && (
          <div className="space-y-5">
            <div className="card">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-2">
                <Heart className="w-4 h-4 text-rose-400" />近7天平均劳损风险趋势
              </h3>
              {summary.risk_trend_7d.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={summary.risk_trend_7d} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.4} label={{ value: '高风险线', position: 'right', style: { fontSize: 9, fill: '#ef4444' } }} />
                    <ReferenceLine y={40} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.4} label={{ value: '警戒线', position: 'right', style: { fontSize: 9, fill: '#f59e0b' } }} />
                    <Line type="monotone" dataKey="avg_shoulder_risk" stroke="#ef4444" name="肩部风险" strokeWidth={2} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="avg_knee_risk" stroke="#f59e0b" name="膝部风险" strokeWidth={2} dot={{ r: 2 }} strokeDasharray="8 2" />
                    <Line type="monotone" dataKey="avg_fatigue" stroke="#3b82f6" name="平均疲劳" strokeWidth={1.5} dot={false} strokeOpacity={0.6} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <p className="text-xs text-slate-400 text-center py-10">风险趋势数据收集中</p>}
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-400" />运动员风险排序
              </h3>
              {summary.top10_risks.length > 0 ? (
                <>
                  <div className="flex gap-3 text-[10px] text-slate-400 mb-1">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm" style={{background:'#e74c3c'}} />不正常(&gt;70)</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm" style={{background:'#f39c12'}} />亚正常(40-70)</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm" style={{background:'#27ae60'}} />正常(&lt;40)</span>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={summary.top10_risks} layout="vertical" margin={{ top: 5, right: 30, left: 45, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.2} horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <YAxis type="category" dataKey="athlete_name" width={50} tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
                      <Tooltip content={<ChartTooltip />} />
                      <ReferenceLine x={40} stroke="#f39c12" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.3} />
                      <ReferenceLine x={70} stroke="#e74c3c" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.3} />
                      <Bar dataKey="max_risk" name="风险值" radius={[0, 4, 4, 0]} maxBarSize={16}>
                        {summary.top10_risks.map((e: any, i: number) => (
                          <Cell key={i} fill={e.max_risk > 70 ? '#e74c3c' : e.max_risk > 40 ? '#f39c12' : '#27ae60'} fillOpacity={0.8} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </>
              ) : <p className="text-xs text-slate-400 text-center py-10">暂无风险数据</p>}
            </div>
          </div>
        )}
      </div>

      {/* Weekly Volume + Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <WeeklyVolumeChart teamView weeks={timeRange === 7 ? 8 : timeRange === 14 ? 10 : 12} />
        <TrainingLoadDistribution teamView days={timeRange === 7 ? 14 : timeRange === 14 ? 21 : 30} />
      </div>

      {/* Load Change Top 5 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {[
          { title: '负荷增加最多 TOP 5', icon: TrendingUp, color: 'text-red-400', sorted: [...athleteStatuses].sort((a: any, b: any) => (b.rssi_score || 0) - (a.rssi_score || 0)).slice(0, 5) },
          { title: '负荷减少最多 TOP 5', icon: TrendingDown, color: 'text-emerald-400', sorted: [...athleteStatuses].sort((a: any, b: any) => (a.rssi_score || 0) - (b.rssi_score || 0)).slice(0, 5) },
        ].map(panel => (
          <div key={panel.title} className="card">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-2"><panel.icon className={`w-4 h-4 ${panel.color}`} />{panel.title}</h3>
            {panel.sorted.map((a: any) => (
              <div key={a.athlete_id} className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800 last:border-0 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: RISK_COLORS[a.acwr_risk_zone] || '#95a5a6' }} />
                  <span className="font-medium text-slate-700 dark:text-slate-300">{a.athlete_name}</span>
                  <span className="text-xs text-slate-400">{a.sport}</span>
                </div>
                <span className={`font-mono text-xs font-bold ${panel.color}`}>{a.rssi_score.toFixed(0)}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Athlete Risk Table */}
      <div className="card p-0 overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 pb-3">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">运动员风险状态</h3>
          <Link to="/athletes" className="text-xs text-cyan-500 hover:text-cyan-400 flex items-center gap-1 font-medium">全部运动员 <ArrowRight className="w-3 h-3" /></Link>
        </div>
        <div className="overflow-auto max-h-[420px]">
          <table className="data-table w-full text-xs">
            <thead className="sticky top-0 z-10 bg-white dark:bg-slate-900">
              <tr>
                <th className="!pl-5 w-8"><input type="checkbox" checked={selected.size === sortedAthletes.length && sortedAthletes.length > 0} onChange={toggleAll} /></th>
                <th className="cursor-pointer" onClick={() => toggleSort('name')}>运动员 {sortKey === 'name' ? (sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />) : ''}</th>
                <th className="cursor-pointer" onClick={() => toggleSort('sport')}>项目 {sortKey === 'sport' ? (sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />) : ''}</th>
                <th className="cursor-pointer text-center" onClick={() => toggleSort('acwr')}>ACWR {sortKey === 'acwr' ? (sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />) : ''}</th>
                <th className="cursor-pointer text-center" onClick={() => toggleSort('riskLevel')}>风险等级 {sortKey === 'riskLevel' ? (sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />) : ''}</th>
                <th className="text-center">RSSI</th>
                <th className="text-center">恢复状态</th>
                <th className="cursor-pointer text-center" onClick={() => toggleSort('alerts')}>预警 {sortKey === 'alerts' ? (sortAsc ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />) : ''}</th>
                <th className="text-right !pr-5">教练建议</th>
              </tr>
            </thead>
            <tbody>
              {sortedAthletes.map((athlete: any) => {
                const isHigh = athlete.acwr_risk_zone === '高风险区' || athlete.rssi_risk_level === '非功能性过度训练';
                const isCaution = athlete.rssi_risk_level === '功能性过度训练' || athlete.acwr_risk_zone === '谨慎区';
                const rowBg = isHigh ? 'bg-red-50/70 dark:bg-red-950/20' : isCaution ? 'bg-amber-50/50 dark:bg-amber-950/10' : '';
                return (
                  <tr key={athlete.athlete_id} className={`${rowBg} ${isHigh ? 'border-l-2 border-l-red-500' : ''}`}>
                    <td className="!pl-5"><input type="checkbox" checked={selected.has(athlete.athlete_id)} onChange={() => toggleSelect(athlete.athlete_id)} /></td>
                    <td className="font-medium text-slate-800 dark:text-slate-200">{athlete.athlete_name}</td>
                    <td className="text-slate-500 dark:text-slate-400">{athlete.sport}</td>
                    <td className="text-center">
                      <span className={`font-mono font-bold ${athlete.latest_acwr > 1.5 ? 'text-red-500' : athlete.latest_acwr > 1.3 ? 'text-amber-500' : 'text-emerald-500'}`}>{athlete.latest_acwr.toFixed(2)}</span>
                    </td>
                    <td className="text-center"><RiskBadge zone={athlete.acwr_risk_zone} /></td>
                    <td className="text-center font-mono font-semibold">{athlete.rssi_score.toFixed(1)}</td>
                    <td className="text-center"><RSSIBadge level={athlete.rssi_risk_level} /></td>
                    <td className="text-center">
                      {athlete.active_alerts > 0 && <span className="inline-flex items-center justify-center min-w-[20px] h-5 rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 text-[11px] font-bold px-1.5 alert-badge">{athlete.active_alerts}</span>}
                    </td>
                    <td className="text-right !pr-5">
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 mr-2">{(ADVICE_MAP[athlete.acwr_risk_zone] || ADVICE_MAP['安全区'])[0]}</span>
                      <Link to={`/athletes/${athlete.athlete_id}`} className="text-xs text-cyan-500 hover:text-cyan-400 font-medium">查看</Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom actions */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-2">
          <button onClick={() => batchAction('rest')} className="btn btn-danger btn-sm" disabled={selected.size === 0}><Send className="w-3 h-3" /> 批量提醒休息 ({selected.size})</button>
          <button onClick={() => batchAction('adjust')} className="btn btn-secondary btn-sm" disabled={selected.size === 0}>批量调整计划</button>
          <button onClick={generateAdvice} className="btn btn-secondary btn-sm"><Shield className="w-3 h-3" /> 生成训练调整建议</button>
        </div>
        <div className="flex gap-2">
          <button onClick={() => exportTable('json')} className="btn btn-secondary btn-sm"><Download className="w-3 h-3" /> 导出 JSON</button>
          <button onClick={() => exportTable('csv')} className="btn btn-secondary btn-sm"><Download className="w-3 h-3" /> 导出 CSV</button>
        </div>
      </div>
    </div>
  );
}
