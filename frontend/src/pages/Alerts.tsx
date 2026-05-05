import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell, AlertTriangle, CheckCircle2, X, Settings, RefreshCw,
  ChevronDown, ChevronUp, Download, Search, Filter, FileText,
  TrendingUp, TrendingDown, Shield,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, BarChart, Bar, Cell, PieChart, Pie,
} from 'recharts';
import {
  getAlertsOverview, getAthleteAlertsDetail, getAlertConfigs,
  upsertAlertConfig, acknowledgeAlert, exportCSV,
  AlertOverview, AlertConfigItem,
} from '../services/api';

const METRIC_LABELS: Record<string, string> = {
  shoulder_overuse_risk: '肩部劳损风险', shoulder_acute_risk: '肩部急性风险',
  knee_overuse_risk: '膝部劳损风险', knee_acute_risk: '膝部急性风险',
};
const GRADE_CONFIG: Record<string, { bg: string; text: string; dot: string }> = {
  A: { bg: 'bg-red-100 dark:bg-red-950/30', text: 'text-red-700 dark:text-red-400', dot: 'bg-red-500' },
  B: { bg: 'bg-amber-100 dark:bg-amber-950/30', text: 'text-amber-700 dark:text-amber-400', dot: 'bg-amber-500' },
  C: { bg: 'bg-yellow-100 dark:bg-yellow-950/30', text: 'text-yellow-700 dark:text-yellow-400', dot: 'bg-yellow-500' },
};
const PIE_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#eab308'];

function RefreshCwIcon({ className }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16" /></svg>;
}

function computeGrade(value: number, threshold: number): string {
  const exceed = (value / threshold - 1) * 100;
  if (exceed > 30) return 'A';
  if (exceed > 10) return 'B';
  return 'C';
}

export function Alerts() {
  const [data, setData] = useState<AlertOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [kpiFilter, setKpiFilter] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [sportFilter, setSportFilter] = useState('全部');
  const [partFilter, setPartFilter] = useState('全部');
  const [gradeFilter, setGradeFilter] = useState('全部');
  const [statusFilter, setStatusFilter] = useState('全部');

  // Detail modal
  const [detailId, setDetailId] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Threshold modal
  const [showThreshold, setShowThreshold] = useState(false);
  const [thresholdAthleteId, setThresholdAthleteId] = useState('');
  const [thresholdAthleteName, setThresholdAthleteName] = useState('');
  const [configs, setConfigs] = useState<AlertConfigItem[]>([]);
  const [configMetric, setConfigMetric] = useState('shoulder_overuse_risk');
  const [configThreshold, setConfigThreshold] = useState(70);
  const [configSeverity, setConfigSeverity] = useState('warning');
  const [configMsg, setConfigMsg] = useState('');

  // Batch
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'risk' | 'name'>('risk');

  const fetchOverview = () => {
    setLoading(true);
    getAlertsOverview()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchOverview(); }, []);

  // Aggregate alerts by athlete
  const athleteAlerts = useMemo(() => {
    if (!data?.alerts) return [];
    const map = new Map<string, { athlete_id: string; athlete_name: string; sport: string; alerts: any[] }>();
    for (const a of data.alerts) {
      if (!map.has(a.athlete_id)) {
        map.set(a.athlete_id, { athlete_id: a.athlete_id, athlete_name: a.athlete_name, sport: a.sport, alerts: [] });
      }
      map.get(a.athlete_id)!.alerts.push(a);
    }
    return Array.from(map.values());
  }, [data]);

  // Historical alerts aggregated
  const historicalAlerts = useMemo(() => {
    return data?.historical_alerts || [];
  }, [data]);

  // Filtered athlete alerts
  const filtered = useMemo(() => {
    let list = [...athleteAlerts];
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(a => a.athlete_name.toLowerCase().includes(q) || a.sport.toLowerCase().includes(q));
    }
    if (sportFilter !== '全部') list = list.filter(a => a.sport === sportFilter);
    if (partFilter !== '全部') {
      list = list.filter(a => a.alerts.some(alert => {
        const m = alert.metric_name || '';
        if (partFilter === '肩部') return m.includes('shoulder');
        if (partFilter === '膝部') return m.includes('knee');
        return false;
      }));
    }
    if (gradeFilter !== '全部') {
      list = list.filter(a => {
        const maxGrade = a.alerts.reduce((g, alert) => {
          const grade = computeGrade(alert.current_value, alert.threshold || 70);
          return grade === 'A' ? 'A' : grade === 'B' && g !== 'A' ? 'B' : g;
        }, 'C');
        return maxGrade === gradeFilter;
      });
    }
    // KPI quick filter
    if (kpiFilter === 'high_risk') {
      list = list.filter(a => a.alerts.some(alert => computeGrade(alert.current_value, alert.threshold || 70) === 'A'));
    }
    return list;
  }, [athleteAlerts, search, sportFilter, partFilter, gradeFilter, kpiFilter]);

  // Sort
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      if (sortBy === 'name') return a.athlete_name.localeCompare(b.athlete_name);
      // risk sort: avg exceedance * alert count
      const scoreA = a.alerts.reduce((s, al) => s + (al.current_value / (al.threshold || 70) - 1) * 100, 0) / a.alerts.length * a.alerts.length;
      const scoreB = b.alerts.reduce((s, al) => s + (al.current_value / (al.threshold || 70) - 1) * 100, 0) / b.alerts.length * b.alerts.length;
      return scoreB - scoreA;
    });
  }, [filtered, sortBy]);

  // KPI stats
  const kpiStats = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const highRiskIds = new Set(athleteAlerts.filter(a => a.alerts.some(al => computeGrade(al.current_value, al.threshold || 70) === 'A')).map(a => a.athlete_id));
    const todayNew = data?.alerts?.filter(a => a.date === today).length || 0;
    const allAlerts = athleteAlerts.flatMap(a => a.alerts);
    const avgExceed = allAlerts.length > 0
      ? +(allAlerts.reduce((s, a) => s + ((a.current_value / (a.threshold || 70)) - 1) * 100, 0) / allAlerts.length).toFixed(1)
      : 0;
    return { highRiskCount: highRiskIds.size, activeCount: allAlerts.length, todayNew, avgExceed };
  }, [athleteAlerts, data]);

  // Risk type distribution for pie chart
  const riskDistData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of athleteAlerts) {
      for (const al of a.alerts) {
        const label = METRIC_LABELS[al.metric_name] || al.metric_name;
        counts[label] = (counts[label] || 0) + 1;
      }
    }
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [athleteAlerts]);

  // 4-week risk trend (from historical data)
  const trendData = useMemo(() => {
    const weeks: Record<string, { shoulder: number; knee: number; count: number }> = {};
    for (const h of historicalAlerts) {
      const d = new Date(h.alert_date);
      const weekStart = new Date(d); weekStart.setDate(d.getDate() - d.getDay());
      const wk = weekStart.toISOString().slice(0, 10);
      if (!weeks[wk]) weeks[wk] = { shoulder: 0, knee: 0, count: 0 };
      if (h.alert_type?.includes('shoulder')) weeks[wk].shoulder++;
      if (h.alert_type?.includes('knee')) weeks[wk].knee++;
      weeks[wk].count++;
    }
    return Object.entries(weeks).slice(-4).map(([week, v]) => ({ week: week.slice(5), '肩部': v.shoulder, '膝部': v.knee }));
  }, [historicalAlerts]);

  // Detail modal
  const openDetail = async (athleteId: string) => {
    setDetailId(athleteId); setDetailLoading(true);
    try { setDetailData(await getAthleteAlertsDetail(athleteId)); }
    catch { setDetailData(null); }
    finally { setDetailLoading(false); }
  };

  // Acknowledge
  const handleAck = async (alertId: string) => {
    await acknowledgeAlert(alertId);
    fetchOverview();
    if (detailId) openDetail(detailId);
  };
  const handleBatchAck = async () => {
    const allAlertIds = athleteAlerts.filter(a => selected.has(a.athlete_id)).flatMap(a => a.alerts);
    for (const al of allAlertIds) {
      const hist = historicalAlerts.find(h => h.alert_type === al.metric_name && h.athlete_id === al.athlete_id);
      if (hist?.id) await acknowledgeAlert(hist.id).catch(() => {});
    }
    setSelected(new Set()); fetchOverview();
  };

  // Threshold config
  const openThreshold = async (athleteId: string, name: string) => {
    setThresholdAthleteId(athleteId); setThresholdAthleteName(name);
    try { setConfigs(await getAlertConfigs(athleteId)); } catch { setConfigs([]); }
    setShowThreshold(true);
  };
  const saveThreshold = async () => {
    try {
      await upsertAlertConfig({ athlete_id: thresholdAthleteId, metric_name: configMetric, threshold: configThreshold, severity: configSeverity, notify: true });
      setConfigMsg('配置已保存'); setConfigs(await getAlertConfigs(thresholdAthleteId));
    } catch { setConfigMsg('保存失败'); }
  };

  // Export
  const exportSelected = () => {
    const chosen = sorted.filter(a => selected.has(a.athlete_id));
    const rows = chosen.flatMap(a => a.alerts.map(al => ({
      运动员: a.athlete_name, 项目: a.sport,
      指标: METRIC_LABELS[al.metric_name] || al.metric_name,
      当前值: al.current_value.toFixed(0), 阈值: al.threshold || 70,
      超出幅度: `${((al.current_value / (al.threshold || 70) - 1) * 100).toFixed(0)}%`,
      等级: computeGrade(al.current_value, al.threshold || 70),
    })));
    if (!rows.length) return;
    exportCSV(rows, 'alerts_export.csv');
  };

  const sports = ['全部', ...new Set(athleteAlerts.map(a => a.sport))];

  if (loading) return <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="skeleton h-24 rounded-xl" />)}</div>;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">预警中心</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">肩/膝劳损与损伤风险监控 · 实时预警</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { setShowThreshold(true); setThresholdAthleteId(''); setThresholdAthleteName('全局'); setConfigs([]); }} className="btn btn-secondary btn-sm"><Settings className="w-3.5 h-3.5" /> 阈值设置</button>
          <button onClick={fetchOverview} className="btn btn-secondary btn-sm"><RefreshCwIcon className="w-3.5 h-3.5" /> 刷新</button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: '高风险运动员', val: kpiStats.highRiskCount, suffix: '人', color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-950/20', filter: 'high_risk' },
          { label: '活跃预警总数', val: kpiStats.activeCount, suffix: '条', color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/20', filter: '' },
          { label: '今日新增预警', val: kpiStats.todayNew, suffix: '条', color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/20', filter: '' },
          { label: '平均超出阈值', val: kpiStats.avgExceed, suffix: '%', color: kpiStats.avgExceed > 20 ? 'text-red-500' : 'text-amber-500', bg: 'bg-orange-50 dark:bg-orange-950/20', filter: '' },
        ].map(c => (
          <button key={c.label} onClick={() => setKpiFilter(kpiFilter === c.filter ? '' : c.filter)}
            className={`card text-left cursor-pointer transition-all ${kpiFilter === c.filter ? 'ring-2 ring-blue-400' : ''} ${c.bg}`}>
            <div className={`text-2xl font-bold ${c.color}`}>{c.val}<span className="text-sm font-normal text-slate-400 ml-1">{c.suffix}</span></div>
            <div className="text-[11px] text-slate-500 mt-0.5">{c.label}</div>
          </button>
        ))}
        {kpiFilter && (
          <div className="col-span-full text-xs text-slate-400">已筛选: {kpiFilter === 'high_risk' ? '仅显示高风险运动员' : ''} <button onClick={() => setKpiFilter('')} className="text-blue-500">清除</button></div>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">近4周风险预警趋势</h3>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.4} />
                <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="肩部" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="膝部" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-xs text-slate-400 text-center py-12">暂无历史数据</p>}
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">风险类型分布</h3>
          {riskDistData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={riskDistData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={3} dataKey="value" nameKey="name" label={({ name, value }) => `${name}: ${value}`}>
                  {riskDistData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-xs text-slate-400 text-center py-12">暂无预警数据</p>}
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[160px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="搜索姓名、项目..." value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 dark:text-slate-200" />
          </div>
          <select value={sportFilter} onChange={e => setSportFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="全部">全部项目</option>
            {sports.filter(s => s !== '全部').map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={partFilter} onChange={e => setPartFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="全部">全部部位</option>
            <option value="肩部">肩部</option>
            <option value="膝部">膝部</option>
          </select>
          <select value={gradeFilter} onChange={e => setGradeFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="全部">全部等级</option>
            <option value="A">A级 (&gt;30%超出)</option>
            <option value="B">B级 (10-30%超出)</option>
            <option value="C">C级 (&lt;10%超出)</option>
          </select>
          <select value={sortBy} onChange={e => setSortBy(e.target.value as any)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="risk">排序: 风险分 ↓</option>
            <option value="name">排序: 姓名</option>
          </select>
        </div>
      </div>

      {/* Alert Cards */}
      {sorted.length === 0 ? (
        <div className="card text-center py-16">
          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">所有运动员状态正常，无活跃预警</p>
          <p className="text-xs text-slate-400 mt-1">系统将持续监控训练负荷与风险指标</p>
        </div>
      ) : (
        <>
          {/* Batch bar */}
          <div className="flex items-center gap-2 flex-wrap">
            <label className="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer select-none">
              <input type="checkbox" checked={selected.size === sorted.length} onChange={() => setSelected(selected.size === sorted.length ? new Set() : new Set(sorted.map(a => a.athlete_id)))} className="rounded" />
              全选 ({selected.size}/{sorted.length})
            </label>
            {selected.size > 0 && (
              <div className="flex gap-1.5">
                <button onClick={handleBatchAck} className="btn btn-sm text-[11px]" style={{ background: '#d4edda', color: '#155724' }}><CheckCircle2 className="w-3 h-3" /> 批量确认处理</button>
                <button onClick={exportSelected} className="btn btn-secondary btn-sm text-[11px]"><Download className="w-3 h-3" /> 导出所选</button>
              </div>
            )}
          </div>

          {/* Cards grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {sorted.map(athlete => {
              const maxGrade = athlete.alerts.reduce((g, al) => {
                const grade = computeGrade(al.current_value, al.threshold || 70);
                return grade === 'A' ? 'A' : grade === 'B' && g !== 'A' ? 'B' : g;
              }, 'C');
              const gc = GRADE_CONFIG[maxGrade];
              const hasCritical = athlete.alerts.some(al => (al.current_value / (al.threshold || 70) - 1) * 100 > 50);
              const hasShoulderAndKnee = athlete.alerts.some(al => al.metric_name?.includes('shoulder')) && athlete.alerts.some(al => al.metric_name?.includes('knee'));
              const isExpanded = expandedCards.has(athlete.athlete_id);
              const avgExceed = athlete.alerts.reduce((s, al) => s + (al.current_value / (al.threshold || 70) - 1) * 100, 0) / athlete.alerts.length;

              return (
                <div key={athlete.athlete_id} className={`card border-l-4 ${maxGrade === 'A' ? 'border-l-red-500' : maxGrade === 'B' ? 'border-l-amber-500' : 'border-l-yellow-500'} ${gc.bg} relative`}>
                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <input type="checkbox" checked={selected.has(athlete.athlete_id)} onChange={() => { const s = new Set(selected); s.has(athlete.athlete_id) ? s.delete(athlete.athlete_id) : s.add(athlete.athlete_id); setSelected(s); }} className="rounded" />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 dark:text-slate-100">{athlete.athlete_name}</span>
                          {hasCritical && <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" title="严重超标" />}
                        </div>
                        <span className="text-[11px] text-slate-400">{athlete.sport}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${gc.text} ${gc.bg}`}>{maxGrade}级</span>
                      <span className="text-[11px] text-slate-400">{athlete.alerts.length}条预警</span>
                    </div>
                  </div>

                  {/* Risk summary */}
                  {hasShoulderAndKnee && (
                    <div className="text-[11px] text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 px-2 py-1 rounded mb-2">
                      ⚠ 综合风险高，建议停训并进行康复评估
                    </div>
                  )}

                  {/* Alerts list */}
                  <div className="space-y-1.5 mb-3">
                    {athlete.alerts.map((al, i) => {
                      const exceed = ((al.current_value / (al.threshold || 70)) - 1) * 100;
                      const grade = computeGrade(al.current_value, al.threshold || 70);
                      const gc2 = GRADE_CONFIG[grade];
                      return (
                        <div key={i} className={`flex items-center justify-between p-2 rounded-lg text-xs ${exceed > 50 ? 'bg-red-100 dark:bg-red-950/30' : 'bg-white/60 dark:bg-slate-800/60'}`}>
                          <div>
                            <span className="font-medium">{METRIC_LABELS[al.metric_name] || al.metric_name}</span>
                            <span className="text-slate-400 ml-2">{al.current_value.toFixed(0)} / {al.threshold || 70}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`font-mono font-bold ${exceed > 30 ? 'text-red-600' : exceed > 10 ? 'text-amber-600' : 'text-yellow-600'}`}>
                              {exceed > 0 ? '+' : ''}{exceed.toFixed(0)}% {exceed > 0 ? <TrendingUp className="w-3 h-3 inline" /> : <TrendingDown className="w-3 h-3 inline" />}
                            </span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${gc2.text} ${gc2.bg}`}>{grade}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Auto-generated advice */}
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2 rounded mb-3">
                    {athlete.alerts.some(al => al.metric_name?.includes('shoulder')) && '肩部负荷过大，建议减量30%，增加YTW伸展训练。'}
                    {athlete.alerts.some(al => al.metric_name?.includes('knee')) && ' 膝部风险偏高，建议减少跳跃频次，增加股四头肌离心训练。'}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <button onClick={async () => {
                      for (const al of athlete.alerts) {
                        const hist = historicalAlerts.find(h => h.alert_type === al.metric_name && h.athlete_id === al.athlete_id);
                        if (hist?.id) await acknowledgeAlert(hist.id).catch(() => {});
                      }
                      fetchOverview();
                    }} className="text-[10px] px-2 py-1 rounded bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 font-medium">
                      <CheckCircle2 className="w-3 h-3 inline mr-1" />确认处理
                    </button>
                    <button onClick={() => openDetail(athlete.athlete_id)} className="text-[10px] px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 hover:bg-blue-200 font-medium">
                      查看详情
                    </button>
                    <button onClick={() => openThreshold(athlete.athlete_id, athlete.athlete_name)} className="text-[10px] px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 font-medium">
                      <Settings className="w-3 h-3 inline mr-1" />阈值
                    </button>
                    <Link to={`/athletes/${athlete.athlete_id}`} className="text-[10px] px-2 py-1 rounded text-cyan-600 dark:text-cyan-400 hover:underline">
                      运动员详情
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Detail Modal */}
      {detailId && (
        <div className="fixed inset-0 z-40 flex justify-end" onClick={e => { if (e.target === e.currentTarget) setDetailId(null); }}>
          <div className="absolute inset-0 bg-black/30" onClick={() => setDetailId(null)} />
          <div className="relative w-full max-w-xl bg-white dark:bg-slate-900 h-full overflow-y-auto shadow-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">预警详情</h3>
              <button onClick={() => setDetailId(null)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><X className="w-5 h-5" /></button>
            </div>
            {detailLoading ? <div className="skeleton h-40" /> : detailData ? (
              <div className="space-y-5">
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">近7天风险趋势</h4>
                {detailData.risk_trend_7d?.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={detailData.risk_trend_7d} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend wrapperStyle={{ fontSize: 10 }} />
                      <Line type="monotone" dataKey="shoulder_overuse_risk" stroke="#ef4444" name="肩劳损" dot strokeWidth={2} />
                      <Line type="monotone" dataKey="knee_overuse_risk" stroke="#f59e0b" name="膝劳损" dot strokeWidth={2} />
                      <Line type="monotone" dataKey="training_load" stroke="#3b82f6" name="训练负荷" dot={false} strokeWidth={1.5} strokeOpacity={0.5} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <p className="text-xs text-slate-400">暂无趋势数据</p>}

                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">预警历史</h4>
                <div className="space-y-2">
                  {(detailData.alerts || []).map((a: any) => (
                    <div key={a.id} className={`p-3 rounded-lg border ${a.is_resolved ? 'bg-slate-50 dark:bg-slate-800/30 border-slate-200' : 'bg-red-50 dark:bg-red-950/20 border-red-200'}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium">{METRIC_LABELS[a.alert_type] || a.alert_type}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${a.severity === 'critical' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{a.severity === 'critical' ? '严重' : '警告'}</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{a.alert_date} · 值: {a.current_value}</p>
                      {a.recommended_action && <p className="text-xs text-slate-600 mt-1 bg-white/50 dark:bg-slate-800/50 p-1.5 rounded">{a.recommended_action}</p>}
                      {!a.is_resolved && (
                        <button onClick={() => handleAck(a.id)} className="mt-2 text-[10px] text-blue-500 hover:underline">标记已处理</button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : <p className="text-sm text-slate-400">加载失败</p>}
          </div>
        </div>
      )}

      {/* Threshold Modal */}
      {showThreshold && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={e => { if (e.target === e.currentTarget) setShowThreshold(false); }}>
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">阈值配置 — {thresholdAthleteName}</h4>
              <button onClick={() => setShowThreshold(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><X className="w-4 h-4" /></button>
            </div>
            {/* Global thresholds */}
            {!thresholdAthleteId && (
              <div className="space-y-3 mb-4">
                <p className="text-[11px] text-slate-400">全局默认阈值（新运动员生效）</p>
                {['shoulder_overuse_risk', 'knee_overuse_risk'].map(m => (
                  <div key={m} className="flex items-center gap-2">
                    <span className="text-xs w-24">{METRIC_LABELS[m]}</span>
                    <input type="range" value={configThreshold} onChange={e => setConfigThreshold(Number(e.target.value))} min={30} max={95} className="flex-1" />
                    <span className="text-xs font-mono w-8">{configThreshold}</span>
                  </div>
                ))}
              </div>
            )}
            {thresholdAthleteId && (
              <div className="space-y-3">
                {configs.length > 0 && (
                  <div className="mb-3 space-y-1">
                    <p className="text-[10px] text-slate-400">现有配置:</p>
                    {configs.map(c => (
                      <div key={c.id} className="text-xs flex justify-between bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded">
                        <span>{METRIC_LABELS[c.metric_name] || c.metric_name}</span>
                        <span className="font-mono">阈值: {c.threshold} ({c.severity})</span>
                      </div>
                    ))}
                  </div>
                )}
                <div>
                  <label className="text-xs text-slate-500">指标</label>
                  <select value={configMetric} onChange={e => setConfigMetric(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
                    {Object.entries(METRIC_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">阈值 ({configThreshold})</label>
                  <input type="range" value={configThreshold} onChange={e => setConfigThreshold(Number(e.target.value))} min={30} max={95} className="w-full" />
                </div>
                <div>
                  <label className="text-xs text-slate-500">等级</label>
                  <select value={configSeverity} onChange={e => setConfigSeverity(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
                    <option value="warning">⚠️ 警告</option>
                    <option value="critical">🚨 严重</option>
                  </select>
                </div>
                <button onClick={saveThreshold}
                  className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600">
                  保存配置
                </button>
                {configMsg && <p className="text-xs text-center text-green-600">{configMsg}</p>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
