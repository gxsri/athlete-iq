import React, { useState, useMemo, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, ReferenceArea, Legend, BarChart, Bar, Cell, PieChart, Pie,
} from 'recharts';
import {
  Download, FileText, TrendingUp, TrendingDown, Shield, Info, Clock,
  CheckSquare, Square, Settings, Printer, History, Trash2, ChevronDown, ChevronUp,
} from 'lucide-react';
import { getAthletes, getAthleteReport, getTeamHeatmap, getDashboardOverview, getDashboardSummary, exportCSV } from '../services/api';

const REPORT_TYPES = [
  { key: 'team', label: '全队综合报告', desc: '团队整体训练负荷、风险、趋势' },
  { key: 'risk', label: '风险聚焦报告', desc: '突出高风险运动员及干预建议' },
  { key: 'load', label: '训练负荷报告', desc: '周负荷、ACWR趋势、分布' },
  { key: 'individual', label: '个体运动员报告', desc: '单一运动员完整数据' },
];
const TIME_RANGES = [
  { key: '7d', label: '最近7天', days: 7 },
  { key: '30d', label: '最近30天', days: 30 },
  { key: '90d', label: '最近90天', days: 90 },
  { key: 'custom', label: '自定义', days: 0 },
];

const ALL_MODULES = [
  { key: 'kpi', label: '团队关键指标', desc: '平均ACWR、疲劳、风险人数' },
  { key: 'risk_table', label: '风险运动员排序表', desc: '前10名高风险运动员详情' },
  { key: 'load_trend', label: '训练负荷趋势图', desc: '周训练量+ACWR曲线' },
  { key: 'risk_dist', label: '损伤风险分布', desc: '肩/膝风险人数饼图' },
  { key: 'compliance', label: '合规性声明', desc: 'NSCA/CPSS标准符合情况' },
  { key: 'individual', label: '运动员个体详情', desc: '仅个体报告时显示' },
];

const PIE_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6'];

function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex items-center ml-1 cursor-help">
      <Info className="w-3 h-3 text-slate-300 dark:text-slate-600 group-hover:text-cyan-400 transition-colors" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-3 py-1.5 bg-slate-800 text-white text-[11px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 shadow-lg max-w-xs text-center">{text}</span>
    </span>
  );
}

export function Reports() {
  // Config
  const [reportType, setReportType] = useState('team');
  const [timeRange, setTimeRange] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [modules, setModules] = useState<Set<string>>(new Set(['kpi', 'risk_table', 'load_trend', 'risk_dist', 'compliance']));
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [compareMode, setCompareMode] = useState(false);

  // Data
  const [apiAthletes, setApiAthletes] = useState<any[]>([]);
  const [reportData, setReportData] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [error, setError] = useState('');

  // Coach notes per module
  const [notes, setNotes] = useState<Record<string, string>>({});

  // History
  const [history, setHistory] = useState<any[]>(() => {
    try { return JSON.parse(localStorage.getItem('athleteiq-reports') || '[]'); } catch { return []; }
  });
  const [showHistory, setShowHistory] = useState(false);

  // Compliance modal
  const [showCompliance, setShowCompliance] = useState(false);

  useEffect(() => {
    Promise.all([
      getAthletes().catch(() => []),
      getDashboardOverview().catch(() => null),
      getDashboardSummary().catch(() => null),
    ]).then(([athletes, ov, sm]) => {
      setApiAthletes(athletes);
      setOverview(ov);
      setSummary(sm);
    });
  }, []);

  // Auto-adjust modules when report type changes
  useEffect(() => {
    if (reportType === 'individual') {
      setModules(new Set(['kpi', 'load_trend', 'risk_dist', 'individual']));
    } else if (reportType === 'risk') {
      setModules(new Set(['risk_table', 'risk_dist', 'compliance']));
    } else if (reportType === 'load') {
      setModules(new Set(['load_trend', 'kpi', 'compliance']));
    } else {
      setModules(new Set(['kpi', 'risk_table', 'load_trend', 'risk_dist', 'compliance']));
    }
  }, [reportType]);

  const toggleModule = (key: string) => {
    const next = new Set(modules);
    next.has(key) ? next.delete(key) : next.add(key);
    setModules(next);
  };

  const daysFromRange = () => {
    if (timeRange !== 'custom') return TIME_RANGES.find(r => r.key === timeRange)?.days || 30;
    if (customStart && customEnd) {
      return Math.ceil((new Date(customEnd).getTime() - new Date(customStart).getTime()) / 86400000);
    }
    return 30;
  };

  const handleGenerate = async () => {
    setLoading(true); setError(''); setPreviewReady(false);
    try {
      let data: any = {};
      if (reportType === 'individual' && selectedAthleteId) {
        data = await getAthleteReport(selectedAthleteId);
      } else {
        const heatmap = await getTeamHeatmap('all').catch(() => null);
        data.heatmap = heatmap;
        data.overview = overview;
        data.summary = summary;
      }
      setReportData(data);
      setPreviewReady(true);

      // Save to history
      const record = {
        id: Date.now(),
        time: new Date().toLocaleString('zh-CN'),
        type: REPORT_TYPES.find(r => r.key === reportType)?.label || reportType,
        timeRange: timeRange === 'custom' ? `${customStart}~${customEnd}` : TIME_RANGES.find(r => r.key === timeRange)?.label,
        athlete: reportType === 'individual' ? apiAthletes.find(a => a.id === selectedAthleteId)?.name : '',
        modules: [...modules],
      };
      const updated = [record, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem('athleteiq-reports', JSON.stringify(updated));
    } catch (err: any) {
      setError(err.message || '报告生成失败');
      setPreviewReady(true);
    } finally { setLoading(false); }
  };

  const loadHistoryRecord = (record: any) => {
    setReportType(record.type.includes('风险') ? 'risk' : record.type.includes('负荷') ? 'load' : record.type.includes('个体') ? 'individual' : 'team');
    setModules(new Set(record.modules || []));
    if (record.athlete) {
      const found = apiAthletes.find((a: any) => a.name === record.athlete);
      if (found) setSelectedAthleteId(found.id);
    }
    handleGenerate();
  };

  const deleteHistoryRecord = (id: number) => {
    const updated = history.filter(h => h.id !== id);
    setHistory(updated);
    localStorage.setItem('athleteiq-reports', JSON.stringify(updated));
  };

  const handlePrint = () => window.print();

  const handleExportCSV = () => {
    const rows: any[] = [];
    if (reportData?.heatmap?.entries) {
      rows.push(...reportData.heatmap.entries.map((e: any) => ({
        姓名: e.athlete_name, ACWR: e.acwr?.toFixed(2), RSSI: e.rssi_score?.toFixed(1),
        近期负荷: e.recent_load?.toFixed(0) || '', 趋势: e.perf_trend || '', 伤病: e.active_injuries || 0,
      })));
    }
    if (reportData?.acwr_history) {
      rows.push(...reportData.acwr_history.map((m: any) => ({
        日期: m.date, ACWR: m.acwr, 风险区域: m.risk_zone || '',
      })));
    }
    if (rows.length) exportCSV(rows, `report_${Date.now()}.csv`);
  };

  // Compute display values
  const displayDays = daysFromRange();
  const riskDist = overview?.athlete_statuses ? [
    { name: '高风险区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '高风险区').length },
    { name: '谨慎区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '谨慎区').length },
    { name: '安全区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '安全区').length },
  ] : [];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2 no-print">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">报告中心</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">NSCA/CPSS 标准训练分析报告</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowCompliance(true)} className="btn btn-secondary btn-sm"><Shield className="w-3.5 h-3.5" /> NSCA/CPSS 合规</button>
          <button onClick={() => setShowHistory(!showHistory)} className="btn btn-secondary btn-sm"><History className="w-3.5 h-3.5" /> 历史 ({history.length})</button>
          <button onClick={handleExportCSV} className="btn btn-secondary btn-sm"><Download className="w-3.5 h-3.5" /> 导出CSV</button>
          <button onClick={handlePrint} className="btn btn-primary btn-sm"><Printer className="w-3.5 h-3.5" /> 导出PDF</button>
        </div>
      </div>

      {/* History sidebar */}
      {showHistory && (
        <div className="card no-print">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">历史报告</h3>
          {history.length === 0 ? (
            <p className="text-xs text-slate-400">暂无历史报告</p>
          ) : (
            <div className="space-y-1">
              {history.map(h => (
                <div key={h.id} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-xs">
                  <div className="flex items-center gap-3">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span className="font-medium">{h.type}</span>
                    <span className="text-slate-400">{h.timeRange}</span>
                    {h.athlete && <span className="text-blue-500">{h.athlete}</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => loadHistoryRecord(h)} className="text-blue-500 hover:underline text-[10px]">加载</button>
                    <button onClick={() => deleteHistoryRecord(h.id)} className="text-red-400 hover:text-red-600"><Trash2 className="w-3 h-3" /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Config panel */}
      <div className="card no-print">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: report type + time */}
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-500 mb-1.5 block">报告类型</label>
              <div className="grid grid-cols-2 gap-2">
                {REPORT_TYPES.map(rt => (
                  <button key={rt.key} onClick={() => setReportType(rt.key)}
                    className={`p-2.5 rounded-lg border text-left text-xs transition-colors ${reportType === rt.key ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300' : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300'}`}>
                    <div className="font-semibold">{rt.label}</div>
                    <div className="text-[10px] opacity-70">{rt.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {reportType === 'individual' && (
              <div>
                <label className="text-xs font-semibold text-slate-500 mb-1 block">选择运动员</label>
                <select value={selectedAthleteId} onChange={e => setSelectedAthleteId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm">
                  <option value="">请选择运动员</option>
                  {apiAthletes.map((a: any) => <option key={a.id} value={a.id}>{a.name} ({a.sport})</option>)}
                </select>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-500 mb-1.5 block">时间范围</label>
              <div className="flex flex-wrap gap-1.5">
                {TIME_RANGES.map(tr => (
                  <button key={tr.key} onClick={() => setTimeRange(tr.key)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${timeRange === tr.key ? 'bg-blue-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'}`}>
                    {tr.label}
                  </button>
                ))}
              </div>
              {timeRange === 'custom' && (
                <div className="flex gap-2 mt-2">
                  <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} className="input text-xs" />
                  <span className="text-slate-400 self-center">~</span>
                  <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} className="input text-xs" />
                </div>
              )}
            </div>
          </div>

          {/* Right: modules */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-500 block">报告内容模块</label>
            <div className="space-y-1.5">
              {ALL_MODULES.map(m => {
                if (m.key === 'individual' && reportType !== 'individual') return null;
                const checked = modules.has(m.key);
                return (
                  <label key={m.key} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer text-xs transition-colors ${checked ? 'border-blue-300 bg-blue-50/50 dark:bg-blue-950/20' : 'border-slate-100 dark:border-slate-800 hover:border-slate-200'}`}>
                    <input type="checkbox" checked={checked} onChange={() => toggleModule(m.key)} className="rounded" />
                    <div>
                      <div className="font-medium text-slate-700 dark:text-slate-200">{m.label}</div>
                      <div className="text-[10px] text-slate-400">{m.desc}</div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        </div>

        <button onClick={handleGenerate} disabled={loading || (reportType === 'individual' && !selectedAthleteId)}
          className="btn btn-primary mt-4 w-full sm:w-auto">
          <FileText className="w-3.5 h-3.5" /> {loading ? '生成中...' : '生成报告预览'}
        </button>
        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
      </div>

      {/* Preview area */}
      {previewReady && (
        <div className="space-y-5" id="report-preview">
          {/* Report header */}
          <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-blue-100 dark:border-blue-900">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                  {REPORT_TYPES.find(r => r.key === reportType)?.label} — {reportType === 'individual' ? apiAthletes.find(a => a.id === selectedAthleteId)?.name || '' : '全队'}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  {TIME_RANGES.find(r => r.key === timeRange)?.label || '自定义'} ({displayDays}天)
                  · 生成时间: {new Date().toLocaleString('zh-CN')}
                  · {[...modules].length} 个模块
                </p>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-950/40 border border-green-200 dark:border-green-900">
                <Shield className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-[11px] font-medium text-green-700 dark:text-green-400">NSCA/CPSS 合规</span>
              </div>
            </div>
          </div>

          {/* KPI Module */}
          {modules.has('kpi') && overview && (
            <div className="card">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">团队关键指标</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: '运动员总数', val: overview.total_athletes, unit: '人', color: 'text-slate-700' },
                  { label: '活跃预警', val: overview.active_alerts, unit: '条', color: 'text-red-500' },
                  { label: '平均 ACWR', val: overview.avg_team_acwr?.toFixed(2), unit: '', color: overview.avg_team_acwr > 1.3 ? 'text-red-500' : 'text-emerald-500' },
                  { label: '风险运动员', val: overview.athletes_at_risk, unit: '人', color: 'text-amber-500' },
                ].map(kpi => (
                  <div key={kpi.label} className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                    <div className={`text-xl font-bold ${kpi.color}`}>{kpi.val}{kpi.unit && <span className="text-sm font-normal text-slate-400 ml-1">{kpi.unit}</span>}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{kpi.label}</div>
                  </div>
                ))}
              </div>
              <textarea className="input mt-3 text-xs" rows={2} placeholder="教练备注（将显示在报告中）..."
                value={notes['kpi'] || ''} onChange={e => setNotes({ ...notes, kpi: e.target.value })} />
            </div>
          )}

          {/* Risk Table Module */}
          {modules.has('risk_table') && reportData?.heatmap?.entries && (
            <div className="card">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">风险运动员排序 (TOP 10)</h4>
              <div className="overflow-x-auto">
                <table className="data-table w-full text-xs">
                  <thead>
                    <tr>
                      <th>#</th><th>运动员</th><th>项目</th><th className="text-center">ACWR</th>
                      <th className="text-center">RSSI</th><th className="text-center">趋势</th><th className="text-center">伤病</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.heatmap.entries.slice(0, 10).map((e: any, i: number) => (
                      <tr key={i} className={e.acwr > 1.3 || e.acwr < 0.8 ? 'bg-amber-50/50 dark:bg-amber-950/10' : ''}>
                        <td className="text-slate-400">{i + 1}</td>
                        <td className="font-medium">{e.athlete_name}</td>
                        <td className="text-slate-500">{e.sport || '羽毛球'}</td>
                        <td className={`text-center font-mono font-bold ${e.acwr > 1.3 ? 'text-red-500' : e.acwr < 0.8 ? 'text-amber-500' : 'text-emerald-500'}`}>
                          {e.acwr?.toFixed(2)}
                        </td>
                        <td className="text-center font-mono">{e.rssi_score?.toFixed(1)}</td>
                        <td className="text-center">{e.perf_trend || '-'}</td>
                        <td className="text-center">{e.active_injuries || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-4 mt-3 text-[11px] text-slate-500">
                <span>团队平均 ACWR: <strong>{reportData.heatmap.avg_acwr?.toFixed(2)}</strong></span>
                <span>风险比例: <strong>{reportData.heatmap.at_risk_pct?.toFixed(1)}%</strong></span>
              </div>
              <textarea className="input mt-3 text-xs" rows={2} placeholder="教练备注..."
                value={notes['risk_table'] || ''} onChange={e => setNotes({ ...notes, risk_table: e.target.value })} />
            </div>
          )}

          {/* Load Trend Module */}
          {modules.has('load_trend') && reportData?.acwr_history && (
            <div className="card">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">训练负荷趋势 (ACWR)</h4>
              {reportData.acwr_history.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={reportData.acwr_history} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis domain={[0, 'auto']} tick={{ fontSize: 10 }} />
                    <ReferenceArea y1={0.8} y2={1.3} fill="#27ae60" fillOpacity={0.06} />
                    <ReferenceArea y1={1.3} y2={1.5} fill="#f39c12" fillOpacity={0.06} />
                    <ReferenceArea y1={1.5} y2={2.5} fill="#e74c3c" fillOpacity={0.06} />
                    <ReferenceLine y={1.3} stroke="#f39c12" strokeDasharray="5 5" strokeWidth={1} />
                    <ReferenceLine y={1.5} stroke="#e74c3c" strokeDasharray="5 5" strokeWidth={1} />
                    <Line type="monotone" dataKey="acwr" stroke="#3b82f6" strokeWidth={2} dot={false} name="ACWR" />
                    <Tooltip />
                    <Legend />
                  </LineChart>
                </ResponsiveContainer>
              ) : <p className="text-xs text-slate-400 py-8 text-center">暂无数据</p>}
              <textarea className="input mt-3 text-xs" rows={2} placeholder="教练备注..."
                value={notes['load_trend'] || ''} onChange={e => setNotes({ ...notes, load_trend: e.target.value })} />
            </div>
          )}

          {/* Risk Distribution Module */}
          {modules.has('risk_dist') && riskDist.length > 0 && (
            <div className="card">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">损伤风险分布</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={riskDist} cx="50%" cy="50%" innerRadius={45} outerRadius={80} paddingAngle={3} dataKey="value" nameKey="name"
                      label={({ name, value }) => `${name}: ${value}人`}>
                      {riskDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col justify-center gap-3 text-sm">
                  {riskDist.map((d, i) => (
                    <div key={d.name} className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ background: PIE_COLORS[i] }} />
                      <span>{d.name}</span>
                      <span className="font-bold">{d.value} 人</span>
                      <span className="text-slate-400">({overview ? (d.value / overview.total_athletes * 100).toFixed(0) : 0}%)</span>
                    </div>
                  ))}
                </div>
              </div>
              <textarea className="input mt-3 text-xs" rows={2} placeholder="教练备注..."
                value={notes['risk_dist'] || ''} onChange={e => setNotes({ ...notes, risk_dist: e.target.value })} />
            </div>
          )}

          {/* Compliance Module */}
          {modules.has('compliance') && (
            <div className="card">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">合规性声明</h4>
              <div className="text-xs text-slate-500 dark:text-slate-400 space-y-2 leading-relaxed">
                <p>✅ 本报告遵循 <strong>NSCA (National Strength and Conditioning Association)</strong> 训练负荷监控指南。</p>
                <p>✅ ACWR 计算基于 7天滚动急性负荷 / 28天滚动慢性负荷（Gabbett 2016, IJSPP）。</p>
                <p>✅ 风险等级参照 <strong>CPSS (Certified Performance and Sport Scientist)</strong> 过度训练共识（Meeusen et al., 2013）。</p>
                <p>✅ 训练负荷单调性、冲击负荷阈值均基于 CSCS 推荐标准。</p>
                <p>⚠️ 本报告仅作为训练决策辅助工具，不作为医学诊断依据。</p>
                <p className="text-[10px] text-slate-400 mt-2">报告 ID: RPT-{Date.now().toString(36).toUpperCase()} · 保密 · 仅供内部使用</p>
              </div>
            </div>
          )}

          {/* Disclaimer */}
          <div className="text-center text-[10px] text-slate-400 dark:text-slate-600 py-4 border-t border-slate-100 dark:border-slate-800">
            <p>本报告仅用于训练监控，不作为医学诊断依据 · AthleteIQ © {new Date().getFullYear()}</p>
            <p className="mt-0.5">保密 · 仅供内部使用</p>
          </div>
        </div>
      )}

      {!previewReady && !loading && (
        <div className="card text-center py-16">
          <FileText className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">配置报告类型和模块后，点击"生成报告预览"</p>
          <p className="text-xs text-slate-400 mt-1">支持导出PDF（Ctrl+P）和 CSV 格式</p>
        </div>
      )}

      {loading && <div className="text-center py-8 text-slate-400">数据加载中...</div>}

      {/* Compliance Modal */}
      {showCompliance && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 no-print" onClick={e => { if (e.target === e.currentTarget) setShowCompliance(false); }}>
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">NSCA/CPSS 合规说明</h4>
              <button onClick={() => setShowCompliance(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <span className="text-slate-400 text-lg">&times;</span>
              </button>
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-400 space-y-3 leading-relaxed">
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">ACWR 计算方式</h5>
                <p>急性负荷（7天滚动平均 Session Load） / 慢性负荷（28天滚动平均 Session Load）。</p>
                <p className="text-[10px] mt-1">参考: Gabbett TJ. The training-injury prevention paradox. Br J Sports Med. 2016.</p>
              </div>
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">风险区间</h5>
                <p>🟢 安全区 (0.8-1.3): 损伤风险最低，最佳训练窗口</p>
                <p>🟡 谨慎区 (1.3-1.5 或 &lt;0.8): 中等风险，需观察恢复指标</p>
                <p>🔴 高风险区 (&gt;1.5): 损伤风险显著升高 2-4x，建议减量</p>
              </div>
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">训练负荷单调性</h5>
                <p>基于 NSCA Essentials of Strength Training and Conditioning 监测每日训练负荷变异系数。</p>
              </div>
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">RSSI 恢复-应激状态指数</h5>
                <p>综合 ACWR、晨起心率、HRV、主观疲劳、体能表现 5个维度评估过度训练风险（CPSS 共识，Meeusen 2013）。</p>
              </div>
              <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-lg">
                <p className="text-amber-700 dark:text-amber-400">⚠️ 重要提示：本报告中的数据和建议仅作为教练决策辅助工具，并非医学诊断。如有运动员出现持续疼痛、严重疲劳或其他异常症状，应及时咨询运动医学专业人员。</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
