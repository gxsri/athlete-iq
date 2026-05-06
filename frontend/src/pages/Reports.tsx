import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, ReferenceArea, Legend, PieChart, Pie, Cell, BarChart, Bar,
} from 'recharts';
import {
  Download, FileText, Shield, Info, Clock, Printer, History, Trash2,
  GripVertical, CheckSquare, Square, Save, FolderOpen, X,
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
  { key: 'kpi', label: '关键指标', icon: '📊', desc: 'ACWR、RSSI、负荷等核心指标' },
  { key: 'risk_table', label: '风险运动员排序', icon: '⚠️', desc: 'TOP 10 高风险运动员排名' },
  { key: 'load_trend', label: '训练负荷趋势', icon: '📈', desc: 'ACWR变化曲线与安全区' },
  { key: 'rssi_trend', label: 'RSSI恢复趋势', icon: '💚', desc: '恢复-应激状态指数变化' },
  { key: 'risk_dist', label: '损伤风险分布', icon: '🥧', desc: '高/中/低风险等级饼图' },
  { key: 'sport_breakdown', label: '项目分布分析', icon: '🏅', desc: '按运动项目统计ACWR与风险' },
  { key: 'weekly_load', label: '周训练负荷', icon: '📅', desc: '团队周度总负荷趋势' },
  { key: 'alert_summary', label: '预警摘要', icon: '🔔', desc: '预警类型与严重程度统计' },
  { key: 'athlete_profile', label: '运动员档案', icon: '👤', desc: '个人信息、训练年限、位置' },
  { key: 'performance_tests', label: '体能测试记录', icon: '🏋️', desc: '近期力量、爆发力、耐力数据' },
  { key: 'coach_comments', label: '教练评语', icon: '💬', desc: '近期教练反馈与建议' },
  { key: 'recommendation', label: '训练建议', icon: '🎯', desc: 'AI周期化训练方案' },
  { key: 'compliance', label: '合规性声明', icon: '✅', desc: 'NSCA/CPSS标准符合情况' },
];

const PRESET_TEMPLATES: Record<string, { type: string; modules: string[]; label: string }> = {
  weekly: { type: 'team', modules: ['kpi', 'risk_table', 'load_trend', 'compliance'], label: '日常周报' },
  prerace: { type: 'risk', modules: ['risk_table', 'risk_dist', 'compliance'], label: '赛前风险评估' },
  monthly: { type: 'team', modules: ['kpi', 'risk_table', 'load_trend', 'risk_dist', 'compliance'], label: '月度总结' },
};
const PIE_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6'];

function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex items-center ml-1 cursor-help">
      <Info className="w-3 h-3 text-slate-300 dark:text-slate-500 group-hover:text-cyan-400 transition-colors" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-3 py-1.5 bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-800 text-[11px] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 shadow-lg max-w-xs text-center">{text}</span>
    </span>
  );
}

const skeletonCards: Record<string, string> = {
  kpi: '团队关键指标', risk_table: '风险运动员排序表',
  load_trend: '训练负荷趋势图', risk_dist: '损伤风险分布图',
  compliance: '合规性声明', individual: '运动员个体详情',
};

export function Reports() {
  const [reportType, setReportType] = useState('team');
  const [timeRange, setTimeRange] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [modules, setModules] = useState<Set<string>>(new Set(['kpi', 'risk_table', 'load_trend', 'risk_dist', 'compliance']));
  const [moduleOrder, setModuleOrder] = useState<string[]>(['kpi', 'risk_table', 'load_trend', 'risk_dist', 'compliance']);
  const [selectedAthleteId, setSelectedAthleteId] = useState('');

  const [apiAthletes, setApiAthletes] = useState<any[]>([]);
  const [reportData, setReportData] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [error, setError] = useState('');
  const [notes, setNotes] = useState<Record<string, string>>({});

  const [history, setHistory] = useState<any[]>(() => {
    try { return JSON.parse(localStorage.getItem('athleteiq-reports') || '[]'); } catch { return []; }
  });
  const [showHistory, setShowHistory] = useState(false);
  const [showCompliance, setShowCompliance] = useState(false);
  const [showTemplateMenu, setShowTemplateMenu] = useState(false);

  // Drag state
  const dragItem = useRef<number | null>(null);
  const dragOverItem = useRef<number | null>(null);

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
    let keys: string[];
    if (reportType === 'individual') keys = ['kpi', 'athlete_profile', 'load_trend', 'rssi_trend', 'performance_tests', 'recommendation', 'coach_comments', 'compliance'];
    else if (reportType === 'risk') keys = ['risk_table', 'risk_dist', 'alert_summary', 'kpi', 'compliance'];
    else if (reportType === 'load') keys = ['load_trend', 'weekly_load', 'kpi', 'sport_breakdown', 'compliance'];
    else keys = ['kpi', 'risk_table', 'load_trend', 'risk_dist', 'sport_breakdown', 'weekly_load', 'alert_summary', 'compliance'];
    setModules(new Set(keys));
    setModuleOrder(keys);
  }, [reportType]);

  const toggleModule = (key: string) => {
    const next = new Set(modules);
    if (next.has(key)) { next.delete(key); setModuleOrder(prev => prev.filter(k => k !== key)); }
    else { next.add(key); setModuleOrder(prev => prev.includes(key) ? prev : [...prev, key]); }
    setModules(next);
  };

  const selectAllModules = () => {
    const available = ALL_MODULES.filter(m => m.key !== 'individual' || reportType === 'individual').map(m => m.key);
    setModules(new Set(available));
    setModuleOrder(available);
  };
  const clearAllModules = () => { setModules(new Set()); setModuleOrder([]); };

  // DnD handlers
  const handleDragStart = (index: number) => { dragItem.current = index; };
  const handleDragEnter = (index: number) => { dragOverItem.current = index; };
  const handleDragEnd = () => {
    if (dragItem.current === null || dragOverItem.current === null) return;
    const next = [...moduleOrder];
    const [removed] = next.splice(dragItem.current, 1);
    next.splice(dragOverItem.current, 0, removed);
    setModuleOrder(next);
    dragItem.current = null;
    dragOverItem.current = null;
  };

  const daysFromRange = () => {
    if (timeRange !== 'custom') return TIME_RANGES.find(r => r.key === timeRange)?.days || 30;
    if (customStart && customEnd) return Math.ceil((new Date(customEnd).getTime() - new Date(customStart).getTime()) / 86400000);
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
      const record = {
        id: Date.now(), time: new Date().toLocaleString('zh-CN'),
        type: REPORT_TYPES.find(r => r.key === reportType)?.label || reportType,
        timeRange: timeRange === 'custom' ? `${customStart}~${customEnd}` : TIME_RANGES.find(r => r.key === timeRange)?.label,
        athlete: reportType === 'individual' ? apiAthletes.find(a => a.id === selectedAthleteId)?.name : '',
        modules: [...modules], reportTypeKey: reportType,
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
    setReportType(record.reportTypeKey || 'team');
    setModules(new Set(record.modules || []));
    setModuleOrder(record.modules || []);
    if (record.athlete) {
      const found = apiAthletes.find((a: any) => a.name === record.athlete);
      if (found) setSelectedAthleteId(found.id);
    }
    setShowHistory(false);
    setTimeout(() => handleGenerate(), 100);
  };

  const deleteHistoryRecord = (id: number) => {
    const updated = history.filter(h => h.id !== id);
    setHistory(updated);
    localStorage.setItem('athleteiq-reports', JSON.stringify(updated));
  };

  const saveTemplate = () => {
    const name = prompt('模板名称：');
    if (!name) return;
    const templates = JSON.parse(localStorage.getItem('athleteiq-templates') || '{}');
    templates[name] = { type: reportType, modules: [...modules], order: [...moduleOrder] };
    localStorage.setItem('athleteiq-templates', JSON.stringify(templates));
    setShowTemplateMenu(false);
  };

  const loadTemplate = (key: string) => {
    const preset = PRESET_TEMPLATES[key];
    if (preset) {
      setReportType(preset.type);
      setModules(new Set(preset.modules));
      setModuleOrder(preset.modules);
    } else {
      const templates = JSON.parse(localStorage.getItem('athleteiq-templates') || '{}');
      const t = templates[key];
      if (t) {
        setReportType(t.type);
        setModules(new Set(t.modules));
        setModuleOrder(t.order || t.modules);
      }
    }
    setShowTemplateMenu(false);
  };

  const getCustomTemplates = () => {
    try { return JSON.parse(localStorage.getItem('athleteiq-templates') || '{}'); } catch { return {}; }
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

  const displayDays = daysFromRange();
  const riskDist = overview?.athlete_statuses ? [
    { name: '高风险区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '高风险区').length },
    { name: '谨慎区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '谨慎区').length },
    { name: '安全区', value: overview.athlete_statuses.filter((a: any) => a.acwr_risk_zone === '安全区').length },
  ] : [];
  const activeModuleCount = ALL_MODULES.filter(m => modules.has(m.key)).length;
  const availableModules = ALL_MODULES.filter(m => {
    if (reportType === 'individual') return ['kpi','load_trend','rssi_trend','athlete_profile','performance_tests','coach_comments','recommendation','alert_summary','compliance'].includes(m.key);
    if (reportType === 'risk') return ['kpi','risk_table','risk_dist','alert_summary','compliance'].includes(m.key);
    if (reportType === 'load') return ['kpi','load_trend','weekly_load','sport_breakdown','compliance'].includes(m.key);
    return true; // team report: all modules except individual-only ones
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2 no-print">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">报告中心</h2>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">NSCA/CPSS 标准训练分析报告</p>
          </div>
          <button onClick={() => setShowCompliance(true)} className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-green-100 dark:bg-green-950/40 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-900 hover:bg-green-200 dark:hover:bg-green-950/60 transition-colors" title="点击查看合规详情">
            <Shield className="w-3 h-3" /> 合规
          </button>
        </div>
        <div className="flex items-center gap-1.5">
          <button onClick={() => setShowHistory(true)} className="btn btn-secondary btn-sm relative"><History className="w-3.5 h-3.5" /> 历史{history.length > 0 && <span className="ml-0.5 text-[10px] bg-slate-200 dark:bg-slate-700 px-1 rounded-full">{history.length}</span>}</button>
          <button onClick={handleExportCSV} className="btn btn-secondary btn-sm"><Download className="w-3.5 h-3.5" /> CSV</button>
          <button onClick={handlePrint} className="btn btn-primary btn-sm"><Printer className="w-3.5 h-3.5" /> PDF</button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-4">
        {/* Left: Config (30%) */}
        <div className="lg:col-span-2 space-y-3 no-print">
          <div className="card space-y-3">
            {/* Report type */}
            <div>
              <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">报告类型</label>
              <div className="space-y-1">
                {REPORT_TYPES.map(rt => (
                  <button key={rt.key} onClick={() => setReportType(rt.key)}
                    className={`w-full p-2 rounded-lg border text-left text-xs transition-colors ${reportType === rt.key ? 'border-blue-400 dark:border-blue-500 bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300' : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}>
                    <div className="font-semibold">{rt.label}</div>
                    <div className="text-[10px] opacity-70 mt-0.5">{rt.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {reportType === 'individual' && (
              <div>
                <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 block">选择运动员</label>
                <select value={selectedAthleteId} onChange={e => setSelectedAthleteId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">请选择运动员</option>
                  {apiAthletes.map((a: any) => <option key={a.id} value={a.id}>{a.name} ({a.sport})</option>)}
                </select>
              </div>
            )}

            {/* Time range */}
            <div>
              <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">时间范围</label>
              <div className="flex flex-wrap gap-1">
                {TIME_RANGES.map(tr => (
                  <button key={tr.key} onClick={() => setTimeRange(tr.key)}
                    className={`px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-colors ${timeRange === tr.key ? 'bg-blue-500 text-white shadow-sm' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'}`}>
                    {tr.label}
                  </button>
                ))}
              </div>
              {timeRange === 'custom' && (
                <div className="flex gap-2 mt-2">
                  <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} max={new Date().toISOString().slice(0,10)}
                    className="flex-1 px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                  <span className="text-slate-400 self-center text-xs">~</span>
                  <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} max={new Date().toISOString().slice(0,10)}
                    className="flex-1 px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                </div>
              )}
            </div>

            {/* Templates */}
            <div className="relative">
              <label className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 block">配置模板</label>
              <div className="flex gap-1">
                <button onClick={() => setShowTemplateMenu(!showTemplateMenu)} className="btn btn-secondary btn-sm flex-1 text-[11px]"><FolderOpen className="w-3 h-3" /> 加载</button>
                <button onClick={saveTemplate} className="btn btn-secondary btn-sm flex-1 text-[11px]"><Save className="w-3 h-3" /> 保存</button>
              </div>
              {showTemplateMenu && (
                <div className="absolute top-full mt-1 left-0 right-0 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-xl z-30 py-1">
                  <p className="text-[10px] text-slate-400 px-3 py-1">预设模板</p>
                  {Object.entries(PRESET_TEMPLATES).map(([k, v]) => (
                    <button key={k} onClick={() => loadTemplate(k)} className="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200">{v.label}</button>
                  ))}
                  {Object.keys(getCustomTemplates()).length > 0 && <p className="text-[10px] text-slate-400 px-3 py-1 mt-1 border-t border-slate-100 dark:border-slate-700">自定义模板</p>}
                  {Object.entries(getCustomTemplates()).map(([k]) => (
                    <button key={k} onClick={() => loadTemplate(k)} className="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200">{k}</button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Modules */}
          <div className="card space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                内容模块
                <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 font-bold">{activeModuleCount}/{availableModules.length}</span>
              </span>
              <div className="flex gap-1">
                <button onClick={selectAllModules} className="text-[10px] text-slate-400 hover:text-blue-500 transition-colors">全选</button>
                <button onClick={clearAllModules} className="text-[10px] text-slate-400 hover:text-red-500 transition-colors">清空</button>
              </div>
            </div>
            <div className="space-y-1">
              {moduleOrder.map((key, idx) => {
                const m = ALL_MODULES.find(m => m.key === key);
                if (!m) return null;
                if (m.key === 'individual' && reportType !== 'individual') return null;
                const checked = modules.has(key);
                return (
                  <div key={m.key} draggable onDragStart={() => handleDragStart(idx)} onDragEnter={() => handleDragEnter(idx)} onDragEnd={handleDragEnd} onDragOver={e => e.preventDefault()}
                    className={`flex items-center gap-1.5 p-1.5 rounded-lg border cursor-pointer text-xs transition-all ${checked ? 'border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-950/20' : 'border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700'}`}>
                    <GripVertical className="w-3 h-3 text-slate-300 dark:text-slate-600 cursor-grab shrink-0" />
                    <input type="checkbox" checked={checked} onChange={() => toggleModule(m.key)} className="rounded shrink-0" />
                    <div className="flex-1 min-w-0" onClick={() => toggleModule(m.key)}>
                      <div className="font-medium text-slate-700 dark:text-slate-200 truncate">{m.icon} {m.label}</div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 truncate">{m.desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <button onClick={handleGenerate} disabled={loading || (reportType === 'individual' && !selectedAthleteId)}
              className="btn btn-primary w-full text-sm mt-2">
              <FileText className="w-3.5 h-3.5" /> {loading ? '生成中...' : '生成报告预览'}
            </button>
            {error && <p className="text-[11px] text-red-500 bg-red-50 dark:bg-red-950/30 p-2 rounded">{error}</p>}
          </div>
        </div>

        {/* Right: Preview (70%) */}
        <div className="lg:col-span-5 space-y-4">
          {previewReady ? (
            <div className="space-y-4" id="report-preview">
              <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-100 dark:border-blue-900">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {REPORT_TYPES.find(r => r.key === reportType)?.label} — {reportType === 'individual' ? apiAthletes.find(a => a.id === selectedAthleteId)?.name || '' : '全队'}
                    </h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      {TIME_RANGES.find(r => r.key === timeRange)?.label || '自定义'} ({displayDays}天) · {new Date().toLocaleString('zh-CN')} · {activeModuleCount} 个模块
                    </p>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-950/40 border border-green-200 dark:border-green-900">
                    <Shield className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                    <span className="text-[10px] font-medium text-green-700 dark:text-green-400">NSCA/CPSS</span>
                  </div>
                </div>
              </div>

              {/* KPI Module — context-aware: individual vs team */}
              {modules.has('kpi') && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">
                    {reportType === 'individual' ? '运动员关键指标' : '团队关键指标'}
                  </h4>
                  {reportType === 'individual' && reportData?.athlete ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { label: '当前 ACWR', val: reportData.acwr_history?.slice(-1)[0]?.acwr?.toFixed(2) ?? '--', unit: '', color: (reportData.acwr_history?.slice(-1)[0]?.acwr ?? 0) > 1.3 ? 'text-red-500' : 'text-emerald-500 dark:text-emerald-400' },
                        { label: 'RSSI 评分', val: reportData.rssi_history?.slice(-1)[0]?.rssi_score?.toFixed(1) ?? '--', unit: '/100', color: 'text-blue-500 dark:text-blue-400' },
                        { label: '训练年限', val: reportData.athlete.training_years ?? '--', unit: '年', color: 'text-slate-700 dark:text-slate-200' },
                        { label: '运动项目', val: reportData.athlete.sport ?? '--', unit: '', color: 'text-indigo-500 dark:text-indigo-400' },
                        { label: '风险等级', val: reportData.acwr_history?.slice(-1)[0]?.risk_zone ?? '--', unit: '', color: (reportData.acwr_history?.slice(-1)[0]?.risk_zone ?? '') === '高风险区' ? 'text-red-500' : 'text-emerald-500 dark:text-emerald-400' },
                        { label: '最近体能测试', val: reportData.recent_performance_tests?.length ?? 0, unit: '次', color: 'text-slate-700 dark:text-slate-200' },
                        { label: '教练评语', val: reportData.coach_comments?.length ?? 0, unit: '条', color: 'text-slate-700 dark:text-slate-200' },
                        { label: '位置/项群', val: reportData.athlete.position_role || reportData.athlete.position_or_event || '--', unit: '', color: 'text-slate-700 dark:text-slate-200' },
                      ].map(kpi => (
                        <div key={kpi.label} className="text-center p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                          <div className={`text-lg font-bold ${kpi.color}`}>{kpi.val}{kpi.unit && <span className="text-xs font-normal text-slate-400 dark:text-slate-500 ml-0.5">{kpi.unit}</span>}</div>
                          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{kpi.label}</div>
                        </div>
                      ))}
                    </div>
                  ) : reportType !== 'individual' && overview ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { label: '运动员总数', val: overview.total_athletes, unit: '人', color: 'text-slate-700 dark:text-slate-200' },
                        { label: '活跃预警', val: overview.active_alerts, unit: '条', color: 'text-red-500 dark:text-red-400' },
                        { label: '平均 ACWR', val: overview.avg_team_acwr?.toFixed(2), unit: '', color: overview.avg_team_acwr > 1.3 ? 'text-red-500' : 'text-emerald-500 dark:text-emerald-400' },
                        { label: '风险运动员', val: overview.athletes_at_risk, unit: '人', color: 'text-amber-500 dark:text-amber-400' },
                        { label: '高风险预警', val: overview.alerts_by_severity?.['高'] ?? 0, unit: '条', color: 'text-red-500 dark:text-red-400' },
                        { label: '中风险预警', val: overview.alerts_by_severity?.['中'] ?? 0, unit: '条', color: 'text-amber-500 dark:text-amber-400' },
                        { label: '低风险预警', val: overview.alerts_by_severity?.['低'] ?? 0, unit: '条', color: 'text-emerald-500 dark:text-emerald-400' },
                        { label: '风险占比', val: overview.total_athletes > 0 ? ((overview.athletes_at_risk / overview.total_athletes) * 100).toFixed(0) : 0, unit: '%', color: 'text-amber-500 dark:text-amber-400' },
                      ].map(kpi => (
                        <div key={kpi.label} className="text-center p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                          <div className={`text-lg font-bold ${kpi.color}`}>{kpi.val}{kpi.unit && <span className="text-xs font-normal text-slate-400 dark:text-slate-500 ml-0.5">{kpi.unit}</span>}</div>
                          <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{kpi.label}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">暂无数据</p>
                  )}
                  <textarea className="w-full mt-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" rows={2} placeholder="教练备注（将显示在报告中）..."
                    value={notes['kpi'] || ''} onChange={e => setNotes({ ...notes, kpi: e.target.value })} />
                </div>
              )}

              {modules.has('risk_table') && reportData?.heatmap?.entries && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">风险运动员排序 (TOP 10)</h4>
                  <div className="overflow-x-auto">
                    <table className="data-table w-full text-xs">
                      <thead><tr><th>#</th><th>运动员</th><th className="text-center">ACWR</th><th className="text-center">RSSI</th><th className="text-center">趋势</th><th className="text-center">伤病</th></tr></thead>
                      <tbody>
                        {reportData.heatmap.entries.slice(0, 10).map((e: any, i: number) => (
                          <tr key={i} className={e.acwr > 1.3 || e.acwr < 0.8 ? 'bg-amber-50/50 dark:bg-amber-950/10' : ''}>
                            <td className="text-slate-400 dark:text-slate-500">{i + 1}</td>
                            <td className="font-medium text-slate-800 dark:text-slate-200">{e.athlete_name}</td>
                            <td className={`text-center font-mono font-bold ${e.acwr > 1.3 ? 'text-red-500' : e.acwr < 0.8 ? 'text-amber-500' : 'text-emerald-500 dark:text-emerald-400'}`}>{e.acwr?.toFixed(2)}</td>
                            <td className="text-center font-mono text-slate-600 dark:text-slate-300">{e.rssi_score?.toFixed(1)}</td>
                            <td className="text-center text-slate-500 dark:text-slate-400">{e.perf_trend || '-'}</td>
                            <td className="text-center text-slate-500 dark:text-slate-400">{e.active_injuries || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex gap-4 mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                    <span>团队平均 ACWR: <strong className="text-slate-700 dark:text-slate-200">{reportData.heatmap.avg_acwr?.toFixed(2)}</strong></span>
                    <span>风险比例: <strong className="text-slate-700 dark:text-slate-200">{reportData.heatmap.at_risk_pct?.toFixed(1)}%</strong></span>
                  </div>
                  <textarea className="w-full mt-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" rows={2} placeholder="教练备注..."
                    value={notes['risk_table'] || ''} onChange={e => setNotes({ ...notes, risk_table: e.target.value })} />
                </div>
              )}

              {/* ACWR Load Trend — individual: personal ACWR; team: team avg from overview */}
              {modules.has('load_trend') && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">训练负荷趋势 (ACWR)</h4>
                  {reportType === 'individual' && reportData?.acwr_history?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={reportData.acwr_history} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.15} />
                        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} interval="preserveStartEnd" />
                        <YAxis domain={[0, 'auto']} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <ReferenceArea y1={0.8} y2={1.3} fill="#27ae60" fillOpacity={0.06} />
                        <ReferenceArea y1={1.3} y2={1.5} fill="#f39c12" fillOpacity={0.06} />
                        <ReferenceArea y1={1.5} y2={2.5} fill="#e74c3c" fillOpacity={0.06} />
                        <ReferenceLine y={1.3} stroke="#f39c12" strokeDasharray="5 5" strokeWidth={1} />
                        <ReferenceLine y={1.5} stroke="#e74c3c" strokeDasharray="5 5" strokeWidth={1} />
                        <Line type="monotone" dataKey="acwr" stroke="#3b82f6" strokeWidth={2} dot={false} name="ACWR" />
                        <Tooltip contentStyle={{ background: 'var(--gray-card)', border: '1px solid var(--gray-border)', borderRadius: 8, fontSize: 11 }} />
                        <Legend />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : reportType !== 'individual' && overview?.athlete_statuses?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={
                        (() => {
                          const acwrBins = { '安全区(0.8-1.3)': 0, '谨慎区(1.3-1.5)': 0, '高风险区(>1.5)': 0, '低负荷(<0.8)': 0 };
                          overview.athlete_statuses.forEach((a: any) => {
                            const v = a.latest_acwr || 0;
                            if (v > 1.5) acwrBins['高风险区(>1.5)']++;
                            else if (v > 1.3) acwrBins['谨慎区(1.3-1.5)']++;
                            else if (v >= 0.8) acwrBins['安全区(0.8-1.3)']++;
                            else acwrBins['低负荷(<0.8)']++;
                          });
                          return Object.entries(acwrBins).map(([name, count]) => ({ name, count }));
                        })()
                      } margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.12} />
                        <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          <Cell key="low" fill="#f59e0b" />
                          <Cell key="safe" fill="#27ae60" />
                          <Cell key="caution" fill="#f39c12" />
                          <Cell key="high" fill="#e74c3c" />
                        </Bar>
                        <Tooltip contentStyle={{ background: 'var(--gray-card)', border: '1px solid var(--gray-border)', borderRadius: 8, fontSize: 11 }} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-xs text-slate-400 dark:text-slate-500 py-8 text-center">暂无负荷数据</p>
                  )}
                  <div className="flex gap-4 mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                    <span>团队平均 ACWR: <strong className="text-slate-700 dark:text-slate-200">{overview?.avg_team_acwr?.toFixed(2) ?? '--'}</strong></span>
                    {reportType === 'individual' && reportData?.acwr_history?.length > 0 && (
                      <span>最新 ACWR: <strong className={reportData.acwr_history.slice(-1)[0].acwr > 1.3 ? 'text-red-500' : 'text-emerald-500'}>{reportData.acwr_history.slice(-1)[0].acwr?.toFixed(2)}</strong></span>
                    )}
                  </div>
                  <textarea className="w-full mt-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" rows={2} placeholder="教练备注..."
                    value={notes['load_trend'] || ''} onChange={e => setNotes({ ...notes, load_trend: e.target.value })} />
                </div>
              )}

              {/* RSSI Trend Module — individual only */}
              {modules.has('rssi_trend') && reportType === 'individual' && reportData?.rssi_history && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">RSSI 恢复-应激状态趋势</h4>
                  {reportData.rssi_history.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={reportData.rssi_history} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.12} />
                        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} interval="preserveStartEnd" />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <ReferenceLine y={70} stroke="#27ae60" strokeDasharray="5 5" strokeWidth={1} label={{ value: '良好', position: 'right', fontSize: 10, fill: '#27ae60' }} />
                        <ReferenceLine y={40} stroke="#f39c12" strokeDasharray="5 5" strokeWidth={1} label={{ value: '警戒', position: 'right', fontSize: 10, fill: '#f39c12' }} />
                        <Line type="monotone" dataKey="rssi_score" stroke="#8b5cf6" strokeWidth={2} dot={false} name="RSSI" />
                        <Tooltip contentStyle={{ background: 'var(--gray-card)', border: '1px solid var(--gray-border)', borderRadius: 8, fontSize: 11 }} />
                        <Legend />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : <p className="text-xs text-slate-400 dark:text-slate-500 py-8 text-center">暂无 RSSI 数据</p>}
                  <textarea className="w-full mt-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" rows={2} placeholder="教练备注..."
                    value={notes['rssi_trend'] || ''} onChange={e => setNotes({ ...notes, rssi_trend: e.target.value })} />
                </div>
              )}

              {/* Athlete Profile Module — individual only */}
              {modules.has('athlete_profile') && reportType === 'individual' && reportData?.athlete && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">运动员档案</h4>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    {[
                      { label: '姓名', val: reportData.athlete.name },
                      { label: '性别', val: reportData.athlete.gender },
                      { label: '运动项目', val: reportData.athlete.sport },
                      { label: '出生日期', val: reportData.athlete.date_of_birth },
                      { label: '训练年限', val: `${reportData.athlete.training_years ?? '--'} 年` },
                      { label: '位置/项群', val: reportData.athlete.position_role || reportData.athlete.position_or_event || '--' },
                      { label: '惯用手', val: reportData.athlete.hand_dominance || '--' },
                      { label: '惯用脚', val: reportData.athlete.dominant_foot || '--' },
                    ].map(row => (
                      <div key={row.label} className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                        <span className="text-slate-400 dark:text-slate-500">{row.label}</span>
                        <span className="font-medium text-slate-700 dark:text-slate-200">{row.val}</span>
                      </div>
                    ))}
                  </div>
                  {reportData.athlete.coach_notes && (
                    <div className="mt-3 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/50">
                      <p className="text-[10px] font-semibold text-amber-700 dark:text-amber-400 mb-0.5">教练备注</p>
                      <p className="text-xs text-amber-600 dark:text-amber-300">{reportData.athlete.coach_notes}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Performance Tests Module — individual only */}
              {modules.has('performance_tests') && reportType === 'individual' && reportData?.recent_performance_tests && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">体能测试记录 (最近5次)</h4>
                  {reportData.recent_performance_tests.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="data-table w-full text-xs">
                        <thead><tr>
                          <th>日期</th><th className="text-center">深蹲1RM</th><th className="text-center">卧推1RM</th><th className="text-center">硬拉1RM</th><th className="text-center">CMJ高度</th><th className="text-center">VO2max</th><th className="text-center">30m冲刺</th>
                        </tr></thead>
                        <tbody>
                          {reportData.recent_performance_tests.map((t: any, i: number) => (
                            <tr key={i}>
                              <td className="text-slate-500 dark:text-slate-400">{t.test_date}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.squat_1rm_kg ?? '--'}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.bench_press_1rm_kg ?? '--'}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.deadlift_1rm_kg ?? '--'}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.cmj_height_cm ?? '--'}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.vo2max_ml_kg_min ?? '--'}</td>
                              <td className="text-center font-mono text-slate-700 dark:text-slate-200">{t.sprint_30m_sec ?? '--'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">暂无体能测试数据</p>}
                </div>
              )}

              {/* Coach Comments Module — individual only */}
              {modules.has('coach_comments') && reportType === 'individual' && reportData?.coach_comments && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">教练评语 (最近20条)</h4>
                  {reportData.coach_comments.length > 0 ? (
                    <div className="space-y-1.5 max-h-60 overflow-y-auto">
                      {reportData.coach_comments.map((c: any, i: number) => (
                        <div key={i} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-xs">
                          <p className="text-slate-700 dark:text-slate-200">{c.comment_text}</p>
                          {c.created_at && <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{new Date(c.created_at).toLocaleString('zh-CN')}</p>}
                        </div>
                      ))}
                    </div>
                  ) : <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">暂无教练评语</p>}
                </div>
              )}

              {/* Training Recommendation Module — individual only */}
              {modules.has('recommendation') && reportType === 'individual' && reportData?.recommendation && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">AI 训练建议</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400 dark:text-slate-500">当前周期:</span>
                      <span className="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 font-medium">{reportData.recommendation.cycle_phase || '--'}</span>
                    </div>
                    {reportData.recommendation.focus_areas?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-slate-400 dark:text-slate-500">重点方向:</span>
                        {reportData.recommendation.focus_areas.map((f: string, i: number) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 text-[10px]">{f}</span>
                        ))}
                      </div>
                    )}
                    {reportData.recommendation.summary && (
                      <p className="text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">{reportData.recommendation.summary}</p>
                    )}
                    {reportData.recommendation.weekly_template?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <p className="text-[10px] font-semibold text-slate-500">周计划建议:</p>
                        {reportData.recommendation.weekly_template.map((s: any, i: number) => (
                          <div key={i} className="flex items-center justify-between p-1.5 rounded bg-slate-50 dark:bg-slate-800/50 text-[10px]">
                            <span className="font-medium text-slate-600 dark:text-slate-300">{s.day || `第${i+1}天`}</span>
                            <span className="text-slate-500 dark:text-slate-400">{s.focus || s.type || ''}</span>
                            <span className="text-slate-400 dark:text-slate-500">RPE {s.rpe || '--'}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Weekly Load Module — team only */}
              {modules.has('weekly_load') && reportType !== 'individual' && summary?.risk_trend && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">团队周度风险趋势</h4>
                  {summary.risk_trend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={summary.risk_trend} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.12} />
                        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} interval="preserveStartEnd" />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Line type="monotone" dataKey="avg_shoulder_risk" stroke="#ef4444" strokeWidth={1.5} dot={false} name="肩部风险" />
                        <Line type="monotone" dataKey="avg_knee_risk" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="膝部风险" />
                        <Line type="monotone" dataKey="avg_fatigue" stroke="#8b5cf6" strokeWidth={1.5} dot={false} name="疲劳度" />
                        <Tooltip contentStyle={{ background: 'var(--gray-card)', border: '1px solid var(--gray-border)', borderRadius: 8, fontSize: 11 }} />
                        <Legend />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : <p className="text-xs text-slate-400 dark:text-slate-500 py-8 text-center">暂无趋势数据</p>}
                </div>
              )}

              {/* Sport Breakdown Module — team only */}
              {modules.has('sport_breakdown') && reportType !== 'individual' && overview?.athlete_statuses && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">按运动项目分布</h4>
                  {(() => {
                    const sportMap: Record<string, { count: number; atRisk: number; avgAcwr: number; acwrSum: number }> = {};
                    overview.athlete_statuses.forEach((a: any) => {
                      const s = a.sport || '其他';
                      if (!sportMap[s]) sportMap[s] = { count: 0, atRisk: 0, avgAcwr: 0, acwrSum: 0 };
                      sportMap[s].count++;
                      sportMap[s].acwrSum += a.latest_acwr || 0;
                      if (a.acwr_risk_zone === '高风险区' || a.acwr_risk_zone === '谨慎区') sportMap[s].atRisk++;
                    });
                    Object.keys(sportMap).forEach(s => {
                      sportMap[s].avgAcwr = sportMap[s].count > 0 ? sportMap[s].acwrSum / sportMap[s].count : 0;
                    });
                    const sports = Object.entries(sportMap).sort((a, b) => b[1].count - a[1].count);
                    return sports.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="data-table w-full text-xs">
                          <thead><tr>
                            <th>项目</th><th className="text-center">人数</th><th className="text-center">平均ACWR</th><th className="text-center">风险人数</th><th className="text-center">风险率</th>
                          </tr></thead>
                          <tbody>
                            {sports.map(([sport, data]) => (
                              <tr key={sport}>
                                <td className="font-medium text-slate-700 dark:text-slate-200">{sport}</td>
                                <td className="text-center text-slate-600 dark:text-slate-300">{data.count}</td>
                                <td className={`text-center font-mono font-bold ${data.avgAcwr > 1.3 ? 'text-red-500' : 'text-emerald-500 dark:text-emerald-400'}`}>{data.avgAcwr.toFixed(2)}</td>
                                <td className="text-center text-amber-500 dark:text-amber-400">{data.atRisk}</td>
                                <td className="text-center text-slate-500 dark:text-slate-400">{data.count > 0 ? ((data.atRisk / data.count) * 100).toFixed(0) : 0}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">暂无数据</p>;
                  })()}
                </div>
              )}

              {/* Alert Summary Module — both team and individual */}
              {modules.has('alert_summary') && overview && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">预警摘要</h4>
                  {reportType === 'individual' && reportData?.athlete ? (
                    <div className="space-y-2 text-xs">
                      {(() => {
                        const athleteAlerts = overview.athlete_statuses?.find((a: any) => a.athlete_id === reportData.athlete.id);
                        return athleteAlerts ? (
                          <div className="grid grid-cols-3 gap-2">
                            <div className="text-center p-2 rounded bg-slate-50 dark:bg-slate-800/50">
                              <div className="text-lg font-bold text-slate-700 dark:text-slate-200">{athleteAlerts.active_alerts ?? 0}</div>
                              <div className="text-[10px] text-slate-400">活跃预警</div>
                            </div>
                            <div className="text-center p-2 rounded bg-slate-50 dark:bg-slate-800/50">
                              <div className={`text-lg font-bold ${athleteAlerts.acwr_risk_zone === '高风险区' ? 'text-red-500' : 'text-emerald-500'}`}>{athleteAlerts.acwr_risk_zone || '--'}</div>
                              <div className="text-[10px] text-slate-400">ACWR区域</div>
                            </div>
                            <div className="text-center p-2 rounded bg-slate-50 dark:bg-slate-800/50">
                              <div className={`text-lg font-bold ${athleteAlerts.rssi_risk_level === '高' ? 'text-red-500' : 'text-emerald-500'}`}>{athleteAlerts.rssi_risk_level || '正常'}</div>
                              <div className="text-[10px] text-slate-400">RSSI等级</div>
                            </div>
                          </div>
                        ) : <p className="text-xs text-slate-400 py-4 text-center">暂无预警数据</p>;
                      })()}
                    </div>
                  ) : (
                    <div className="space-y-2 text-xs">
                      <div className="grid grid-cols-4 gap-2">
                        {[
                          { label: '严重', val: overview.alerts_by_severity?.['严重'] ?? 0, color: 'text-red-600' },
                          { label: '高', val: overview.alerts_by_severity?.['高'] ?? 0, color: 'text-red-500' },
                          { label: '中', val: overview.alerts_by_severity?.['中'] ?? 0, color: 'text-amber-500' },
                          { label: '低', val: overview.alerts_by_severity?.['低'] ?? 0, color: 'text-emerald-500' },
                        ].map(item => (
                          <div key={item.label} className="text-center p-2 rounded bg-slate-50 dark:bg-slate-800/50">
                            <div className={`text-lg font-bold ${item.color}`}>{item.val}</div>
                            <div className="text-[10px] text-slate-400">{item.label}严重度</div>
                          </div>
                        ))}
                      </div>
                      {summary && (
                        <div className="flex gap-4 mt-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                          <span className="text-slate-400">团队平均疲劳: <strong className="text-slate-700 dark:text-slate-200">{summary.avg_fatigue ?? '--'}</strong></span>
                          <span className="text-slate-400">高风险人数: <strong className="text-red-500">{summary.high_risk_count ?? '--'}</strong></span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {modules.has('risk_dist') && riskDist.length > 0 && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">损伤风险分布</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={riskDist} cx="50%" cy="50%" innerRadius={40} outerRadius={75} paddingAngle={3} dataKey="value" nameKey="name" label={({ name, value }) => `${name}: ${value}人`}>
                          {riskDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-col justify-center gap-2 text-sm">
                      {riskDist.map((d, i) => (
                        <div key={d.name} className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full" style={{ background: PIE_COLORS[i] }} />
                          <span className="text-slate-600 dark:text-slate-300">{d.name}</span>
                          <span className="font-bold text-slate-700 dark:text-slate-200">{d.value}</span>
                          <span className="text-slate-400 dark:text-slate-500 text-xs">({overview ? (d.value / overview.total_athletes * 100).toFixed(0) : 0}%)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <textarea className="w-full mt-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" rows={2} placeholder="教练备注..."
                    value={notes['risk_dist'] || ''} onChange={e => setNotes({ ...notes, risk_dist: e.target.value })} />
                </div>
              )}

              {modules.has('compliance') && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">合规性声明</h4>
                  <div className="text-xs text-slate-500 dark:text-slate-400 space-y-2 leading-relaxed">
                    <p>✅ 遵循 <strong className="text-slate-700 dark:text-slate-200">NSCA</strong> 训练负荷监控指南。</p>
                    <p>✅ ACWR 计算基于 7天/28天滚动负荷（Gabbett 2016, IJSPP）。</p>
                    <p>✅ 风险等级参照 <strong className="text-slate-700 dark:text-slate-200">CPSS</strong> 过度训练共识（Meeusen 2013）。</p>
                    <p>⚠️ 本报告仅作为训练决策辅助工具，不作为医学诊断依据。</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-600 mt-2">报告 ID: RPT-{Date.now().toString(36).toUpperCase()} · 保密 · 仅供内部使用</p>
                  </div>
                </div>
              )}

              <div className="text-center text-[10px] text-slate-400 dark:text-slate-600 py-4 border-t border-slate-100 dark:border-slate-800">
                <p>本报告仅用于训练监控，不作为医学诊断依据 · AthleteIQ © {new Date().getFullYear()}</p>
                <p className="mt-0.5">保密 · 仅供内部使用</p>
              </div>
            </div>
          ) : (
            /* Skeleton preview placeholders */
            <div className="space-y-3">
              <div className="card bg-slate-50 dark:bg-slate-800/30 border-dashed border-slate-200 dark:border-slate-700">
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-2">
                  报告预览区域 — 已选 <span className="font-bold text-slate-600 dark:text-slate-300">{activeModuleCount}</span> 个模块
                </p>
              </div>
              {moduleOrder.filter(k => modules.has(k)).map(key => (
                <div key={key} className="card border-dashed border-slate-200 dark:border-slate-700 bg-slate-50/30 dark:bg-slate-800/20 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-lg">
                      {ALL_MODULES.find(m => m.key === key)?.icon || '📄'}
                    </div>
                    <div className="flex-1">
                      <div className="h-3 w-32 bg-slate-200 dark:bg-slate-700 rounded mb-1.5" />
                      <div className="h-2 w-48 bg-slate-100 dark:bg-slate-700/50 rounded" />
                    </div>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">待生成</span>
                  </div>
                </div>
              ))}
              {activeModuleCount === 0 && (
                <div className="card text-center py-12">
                  <FileText className="w-10 h-10 text-slate-200 dark:text-slate-700 mx-auto mb-2" />
                  <p className="text-xs text-slate-400 dark:text-slate-500">请勾选左侧内容模块后点击"生成报告预览"</p>
                </div>
              )}
            </div>
          )}

          {loading && <div className="text-center py-6 text-slate-400 dark:text-slate-500 text-sm">数据加载中...</div>}
        </div>
      </div>

      {/* History Drawer */}
      {showHistory && (
        <div className="fixed inset-0 z-40 flex justify-end no-print">
          <div className="absolute inset-0 bg-black/30 dark:bg-black/50" onClick={() => setShowHistory(false)} />
          <div className="relative w-full max-w-sm bg-white dark:bg-slate-900 h-full overflow-y-auto shadow-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">历史报告 ({history.length})</h3>
              <button onClick={() => setShowHistory(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            {history.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500">暂无历史报告，生成报告后自动保存在此。</p>
            ) : (
              <div className="space-y-1.5">
                {history.map(h => (
                  <div key={h.id} className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-700 dark:text-slate-200">{h.type}</span>
                      <button onClick={() => deleteHistoryRecord(h.id)} className="text-slate-300 dark:text-slate-600 hover:text-red-500"><Trash2 className="w-3 h-3" /></button>
                    </div>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 space-y-0.5">
                      <div><Clock className="w-2.5 h-2.5 inline mr-1" />{h.time}</div>
                      <div>时间: {h.timeRange} · {h.modules?.length || 0} 模块</div>
                      {h.athlete && <div className="text-blue-500 dark:text-blue-400">运动员: {h.athlete}</div>}
                    </div>
                    <button onClick={() => loadHistoryRecord(h)} className="mt-2 text-[10px] text-blue-500 hover:text-blue-400 font-medium">加载此配置</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Compliance Modal */}
      {showCompliance && (
        <div className="fixed inset-0 bg-black/40 dark:bg-black/60 flex items-center justify-center z-50 no-print" onClick={e => { if (e.target === e.currentTarget) setShowCompliance(false); }}>
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">NSCA/CPSS 合规说明</h4>
              <button onClick={() => setShowCompliance(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><span className="text-slate-400 text-lg">&times;</span></button>
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-400 space-y-3 leading-relaxed">
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">ACWR 计算方式</h5>
                <p>急性负荷（7天滚动平均 Session Load） / 慢性负荷（28天滚动平均 Session Load）。</p>
                <p className="text-[10px] mt-1 text-slate-400 dark:text-slate-500">参考: Gabbett TJ. Br J Sports Med. 2016.</p>
              </div>
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">风险区间</h5>
                <p>🟢 安全区 (0.8-1.3): 损伤风险最低</p>
                <p>🟡 谨慎区 (1.3-1.5 / &lt;0.8): 中等风险</p>
                <p>🔴 高风险区 (&gt;1.5): 损伤风险升高 2-4x</p>
              </div>
              <div>
                <h5 className="font-semibold text-slate-700 dark:text-slate-300 mb-1">RSSI</h5>
                <p>综合 ACWR、晨起心率、HRV、主观疲劳、体能表现 5个维度（CPSS 共识，Meeusen 2013）。</p>
              </div>
              <div className="bg-amber-50 dark:bg-amber-950/30 p-3 rounded-lg">
                <p className="text-amber-700 dark:text-amber-400 text-[11px]">⚠️ 本报告仅作为教练决策辅助工具，并非医学诊断。如有持续疼痛或严重疲劳，应咨询运动医学专业人员。</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
