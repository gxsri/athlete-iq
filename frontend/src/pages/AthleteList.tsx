import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Upload, Plus, X, ChevronLeft, ChevronRight,
  AlertTriangle, TrendingUp, TrendingDown, Shield, Download, Send,
  LayoutGrid, List, CheckSquare, Square, Bell,
} from 'lucide-react';
import { createAthlete, getAthletes, getDashboardOverview, exportCSV } from '../services/api';

const sportOptions = ['篮球', '足球', '游泳', '田径', '羽毛球', '排球', '网球', '乒乓球', '其他'];
const handOptions = ['左', '右', '双'];
const PAGE_SIZE = 12;
const RISK_COLORS: Record<string, string> = { '安全区': '#27ae60', '谨慎区': '#f39c12', '高风险区': '#e74c3c' };
const RISK_ORDER: Record<string, number> = { '高风险区': 3, '谨慎区': 2, '安全区': 1 };

type ViewMode = 'card' | 'table';

export function AthleteList() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [sportFilter, setSportFilter] = useState('全部');
  const [riskFilter, setRiskFilter] = useState('全部');
  const [acwrFilter, setAcwrFilter] = useState('all');
  const [fatigueFilter, setFatigueFilter] = useState(false);
  const [sortBy, setSortBy] = useState('risk');
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [athletes, setAthletes] = useState<any[]>([]);
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // Form state
  const [formName, setFormName] = useState('');
  const [formDob, setFormDob] = useState('');
  const [formGender, setFormGender] = useState('男');
  const [formSport, setFormSport] = useState(sportOptions[0]);
  const [formPosition, setFormPosition] = useState('');
  const [formTrainingYears, setFormTrainingYears] = useState('');
  const [formInjuryHistory, setFormInjuryHistory] = useState('');
  const [formHandDominance, setFormHandDominance] = useState('右');
  const [formDominantFoot, setFormDominantFoot] = useState('右');
  const [formCoachNotes, setFormCoachNotes] = useState('');
  const [formContactEmail, setFormContactEmail] = useState('');
  const [formContactPhone, setFormContactPhone] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [formSuccess, setFormSuccess] = useState('');
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [csvMsg, setCsvMsg] = useState('');
  const [csvLoading, setCsvLoading] = useState(false);

  useEffect(() => {
    Promise.all([getAthletes(), getDashboardOverview().catch(() => null)])
      .then(([athleteList, overviewData]) => {
        setAthletes(athleteList);
        setOverview(overviewData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Merge athlete data with overview status
  const enriched = useMemo(() => {
    if (!overview?.athlete_statuses) return athletes;
    const statusMap = new Map(overview.athlete_statuses.map((s: any) => [s.athlete_id, s]));
    return athletes.map(a => ({ ...a, status: statusMap.get(a.id) || null }));
  }, [athletes, overview]);

  // Filtering
  const filtered = useMemo(() => {
    let list = [...enriched];
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(a => a.name.toLowerCase().includes(q) || a.sport.toLowerCase().includes(q));
    }
    if (sportFilter !== '全部') list = list.filter(a => a.sport === sportFilter);
    if (riskFilter !== '全部') {
      list = list.filter(a => {
        const zone = a.status?.acwr_risk_zone || '安全区';
        if (riskFilter === '高风险') return zone === '高风险区';
        if (riskFilter === '中风险') return zone === '谨慎区';
        if (riskFilter === '安全') return zone === '安全区';
        return true;
      });
    }
    if (acwrFilter === 'high') list = list.filter(a => (a.status?.latest_acwr || 0) > 1.3);
    if (acwrFilter === 'low') list = list.filter(a => (a.status?.latest_acwr || 1) < 0.8);
    if (acwrFilter === 'safe') list = list.filter(a => { const v = a.status?.latest_acwr || 0; return v >= 0.8 && v <= 1.3; });
    if (fatigueFilter) list = list.filter(a => (a.status?.rssi_score || 0) > 40);
    return list;
  }, [enriched, search, sportFilter, riskFilter, acwrFilter, fatigueFilter]);

  // Sorting
  const sorted = useMemo(() => {
    return [...filtered].sort((a: any, b: any) => {
      if (sortBy === 'risk') return (RISK_ORDER[b.status?.acwr_risk_zone] || 0) - (RISK_ORDER[a.status?.acwr_risk_zone] || 0);
      if (sortBy === 'acwr') return (b.status?.latest_acwr || 0) - (a.status?.latest_acwr || 0);
      if (sortBy === 'fatigue') return (b.status?.rssi_score || 0) - (a.status?.rssi_score || 0);
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'recent') return (b.status?.last_updated || '') > (a.status?.last_updated || '') ? 1 : -1;
      return 0;
    });
  }, [filtered, sortBy]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const paged = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Risk summary
  const riskSummary = useMemo(() => {
    const high = enriched.filter(a => a.status?.acwr_risk_zone === '高风险区').length;
    const mid = enriched.filter(a => a.status?.acwr_risk_zone === '谨慎区').length;
    const safe = enriched.filter(a => a.status?.acwr_risk_zone === '安全区').length;
    return { high, mid, safe, total: enriched.length };
  }, [enriched]);

  const toggleSelect = (id: string) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };
  const toggleAll = () => {
    if (selected.size === paged.length) setSelected(new Set());
    else setSelected(new Set(paged.map((a: any) => a.id)));
  };
  const batchExport = () => {
    const chosen = enriched.filter((a: any) => selected.has(a.id));
    if (!chosen.length) return;
    const rows = chosen.map((a: any) => ({
      姓名: a.name, 项目: a.sport, 出生日期: a.date_of_birth, 性别: a.gender,
      训练年限: a.training_years, ACWR: a.status?.latest_acwr?.toFixed(2) || '',
      风险等级: a.status?.acwr_risk_zone || '', RSSI: a.status?.rssi_score?.toFixed(1) || '',
    }));
    exportCSV(rows, 'athletes_export.csv');
  };
  const batchNotify = () => {
    const chosen = enriched.filter((a: any) => selected.has(a.id));
    if (!chosen.length) return alert('请先勾选运动员');
    alert(`已为以下运动员发送训练建议：\n${chosen.map((a: any) => a.name).join('、')}`);
  };
  const exportCurrent = () => {
    const rows = sorted.map((a: any) => ({
      姓名: a.name, 项目: a.sport, 出生日期: a.date_of_birth, 性别: a.gender,
      训练年限: a.training_years, ACWR: a.status?.latest_acwr?.toFixed(2) || '',
      风险等级: a.status?.acwr_risk_zone || '', RSSI: a.status?.rssi_score?.toFixed(1) || '',
    }));
    exportCSV(rows, 'athletes_all_export.csv');
  };

  const resetForm = () => {
    setFormName(''); setFormDob(''); setFormGender('男'); setFormSport(sportOptions[0]);
    setFormPosition(''); setFormTrainingYears(''); setFormInjuryHistory('');
    setFormHandDominance('右'); setFormDominantFoot('右'); setFormCoachNotes('');
    setFormContactEmail(''); setFormContactPhone(''); setFormErrors({}); setFormSuccess('');
  };

  const handleCreateAthlete = async () => {
    const errors: Record<string, string> = {};
    if (!formName.trim()) errors.name = '姓名为必填项';
    if (!formDob) errors.dateOfBirth = '出生日期为必填项';
    if (!formSport) errors.sport = '运动项目为必填项';
    if (Object.keys(errors).length > 0) { setFormErrors(errors); return; }

    setFormSubmitting(true); setFormErrors({}); setFormSuccess('');
    try {
      const payload = {
        name: formName.trim(), date_of_birth: formDob, gender: formGender,
        sport: formSport, position_or_event: formPosition.trim() || undefined,
        training_years: formTrainingYears ? Number(formTrainingYears) : undefined,
        injury_history: formInjuryHistory.trim() || undefined,
        hand_dominance: formHandDominance, dominant_foot: formDominantFoot,
        coach_notes: formCoachNotes.trim() || undefined,
        contact_email: formContactEmail.trim() || undefined,
        contact_phone: formContactPhone.trim() || undefined,
      };
      const newAthlete = await createAthlete(payload);
      setAthletes(prev => [...prev, newAthlete]);
      setFormSuccess('运动员添加成功！');
      setTimeout(() => { setShowModal(false); resetForm(); }, 800);
    } catch (err: any) {
      setFormErrors({ submit: err.message || '添加失败，请重试' });
    } finally { setFormSubmitting(false); }
  };

  const openModal = () => { resetForm(); setShowModal(true); };

  if (loading) return <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="skeleton h-32 rounded-xl" />)}</div>;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">运动员管理</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">运动员档案 · 状态监控 · 批量管理</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={openModal} className="btn btn-primary btn-sm"><Plus className="w-3.5 h-3.5" /> 添加运动员</button>
          <label className="btn btn-secondary btn-sm cursor-pointer">
            <Upload className="w-3.5 h-3.5" /> 导入 CSV
            <input type="file" accept=".csv" className="hidden" disabled={csvLoading}
              onChange={async (e) => {
                const file = e.target.files?.[0]; if (!file) return;
                setCsvLoading(true); setCsvMsg('');
                try {
                  const text = await file.text();
                  const lines = text.split('\n').filter(l => l.trim());
                  if (lines.length < 2) { setCsvMsg('CSV 格式无效'); return; }
                  const headers = lines[0].split(',').map(h => h.trim());
                  const nameIdx = headers.findIndex(h => h === 'name' || h === '姓名');
                  const dobIdx = headers.findIndex(h => h === 'date_of_birth' || h === '出生日期');
                  const genderIdx = headers.findIndex(h => h === 'gender' || h === '性别');
                  const sportIdx = headers.findIndex(h => h === 'sport' || h === '运动项目');
                  if (nameIdx < 0 || dobIdx < 0 || genderIdx < 0 || sportIdx < 0) {
                    setCsvMsg('CSV 缺少必要列: name, date_of_birth, gender, sport'); return;
                  }
                  let imported = 0;
                  for (let i = 1; i < lines.length; i++) {
                    const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
                    try {
                      const athlete = await createAthlete({ name: cols[nameIdx], date_of_birth: cols[dobIdx], gender: cols[genderIdx], sport: cols[sportIdx] });
                      setAthletes(prev => [...prev, athlete]); imported++;
                    } catch {}
                  }
                  setCsvMsg(`导入完成: ${imported} 人`);
                } catch { setCsvMsg('文件读取失败'); }
                finally { setCsvLoading(false); e.target.value = ''; }
              }}
            />
          </label>
          <button onClick={exportCurrent} className="btn btn-secondary btn-sm"><Download className="w-3.5 h-3.5" /> 导出当前</button>
        </div>
      </div>

      {/* Risk Summary Bar */}
      {riskSummary.total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button onClick={() => setRiskFilter('全部')} className={`card text-center py-2.5 cursor-pointer transition-colors ${riskFilter === '全部' ? 'ring-2 ring-blue-400' : ''}`}>
            <div className="text-lg font-bold text-slate-700 dark:text-slate-200">{riskSummary.total}</div>
            <div className="text-[11px] text-slate-400">全部运动员</div>
          </button>
          <button onClick={() => setRiskFilter('安全')} className={`card text-center py-2.5 cursor-pointer transition-colors ${riskFilter === '安全' ? 'ring-2 ring-emerald-400' : ''}`}>
            <div className="text-lg font-bold text-emerald-500">🟢 {riskSummary.safe}</div>
            <div className="text-[11px] text-slate-400">安全</div>
          </button>
          <button onClick={() => setRiskFilter('中风险')} className={`card text-center py-2.5 cursor-pointer transition-colors ${riskFilter === '中风险' ? 'ring-2 ring-amber-400' : ''}`}>
            <div className="text-lg font-bold text-amber-500">🟡 {riskSummary.mid}</div>
            <div className="text-[11px] text-slate-400">中度风险</div>
          </button>
          <button onClick={() => setRiskFilter('高风险')} className={`card text-center py-2.5 cursor-pointer transition-colors ${riskFilter === '高风险' ? 'ring-2 ring-red-400' : ''}`}>
            <div className="text-lg font-bold text-red-500">🔴 {riskSummary.high}</div>
            <div className="text-[11px] text-slate-400">高风险</div>
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="card space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="搜索姓名、项目..." value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 dark:text-slate-200" />
          </div>
          <select value={sportFilter} onChange={e => { setSportFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="全部">全部项目</option>
            {sportOptions.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={acwrFilter} onChange={e => { setAcwrFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="all">ACWR: 全部</option>
            <option value="safe">ACWR: 0.8-1.3 安全</option>
            <option value="high">ACWR: &gt;1.3 偏高</option>
            <option value="low">ACWR: &lt;0.8 偏低</option>
          </select>
          <label className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-sm cursor-pointer select-none text-slate-700 dark:text-slate-200">
            <input type="checkbox" checked={fatigueFilter} onChange={e => { setFatigueFilter(e.target.checked); setPage(1); }} className="rounded" />
            高疲劳 (RSSI&gt;40)
          </label>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
            <option value="risk">排序: 风险等级 ↓</option>
            <option value="acwr">排序: ACWR ↓</option>
            <option value="fatigue">排序: 疲劳 ↓</option>
            <option value="name">排序: 姓名</option>
            <option value="recent">排序: 最近更新</option>
          </select>
          <div className="flex items-center gap-0.5 ml-auto">
            <button onClick={() => setViewMode('card')} className={`p-2 rounded-lg text-sm ${viewMode === 'card' ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}><LayoutGrid className="w-4 h-4" /></button>
            <button onClick={() => setViewMode('table')} className={`p-2 rounded-lg text-sm ${viewMode === 'table' ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}><List className="w-4 h-4" /></button>
          </div>
        </div>
      </div>

      {/* Card View */}
      {viewMode === 'card' && (
        <>
          <div className="flex items-center gap-2">
            <button onClick={toggleAll} className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1">
              {selected.size === paged.length && paged.length > 0 ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
              {selected.size > 0 ? `已选 ${selected.size} 人` : '全选'}
            </button>
            {selected.size > 0 && (
              <div className="flex gap-1">
                <button onClick={batchExport} className="btn btn-secondary btn-sm text-[11px]"><Download className="w-3 h-3" /> 导出所选</button>
                <button onClick={batchNotify} className="btn btn-sm text-[11px]" style={{ background: '#fef3c7', color: '#92400e' }}><Send className="w-3 h-3" /> 发送提醒</button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {paged.map((athlete: any) => {
              const status = athlete.status;
              const zone = status?.acwr_risk_zone || '安全区';
              const acwr = status?.latest_acwr || 0;
              const rssi = status?.rssi_score || 0;
              const isHigh = zone === '高风险区';
              const isCaution = zone === '谨慎区';
              const borderColor = isHigh ? 'border-l-red-500' : isCaution ? 'border-l-amber-500' : 'border-l-emerald-400';
              const bg = isHigh ? 'bg-red-50/50 dark:bg-red-950/10' : isCaution ? 'bg-amber-50/50 dark:bg-amber-950/10' : '';
              const age = athlete.date_of_birth ? Math.floor((Date.now() - new Date(athlete.date_of_birth).getTime()) / 31557600000) : '?';

              return (
                <div key={athlete.id} className={`metric-card ${borderColor} ${bg} cursor-pointer group relative`}>
                  {/* Select checkbox */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
                    <input type="checkbox" checked={selected.has(athlete.id)} onChange={() => toggleSelect(athlete.id)} className="rounded" />
                  </div>

                  <div onClick={() => navigate(`/athletes/${athlete.id}`)}>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-slate-800 dark:text-slate-100 text-[15px]">{athlete.name}</h3>
                        <p className="text-[11px] text-slate-400">{athlete.sport} · {athlete.position_role || athlete.position_or_event || '未指定'}</p>
                      </div>
                      {isHigh && <AlertTriangle className="w-4 h-4 text-red-500 animate-pulse" />}
                      {(acwr > 1.3 || acwr < 0.8) && <span className="text-[11px] text-amber-500">⚠</span>}
                    </div>

                    {/* Age & Training Years */}
                    <div className="flex items-center gap-3 text-[11px] text-slate-400 mb-2">
                      <span>{age} 岁</span>
                      <span>训练 {athlete.training_years || '?'} 年</span>
                      <span>{athlete.gender}</span>
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-3 gap-2 mb-2">
                      <div className="text-center p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                        <div className={`text-sm font-bold font-mono ${acwr > 1.3 ? 'text-red-500' : acwr > 0 ? 'text-emerald-500' : 'text-slate-400'}`}>{acwr > 0 ? acwr.toFixed(2) : '--'}</div>
                        <div className="text-[10px] text-slate-400">ACWR</div>
                      </div>
                      <div className="text-center p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                        <div className={`text-sm font-bold font-mono ${rssi > 40 ? 'text-red-500' : rssi > 15 ? 'text-amber-500' : 'text-emerald-500'}`}>{rssi.toFixed(0)}</div>
                        <div className="text-[10px] text-slate-400">RSSI</div>
                      </div>
                      <div className={`text-center p-1.5 rounded-lg ${isHigh ? 'bg-red-100 dark:bg-red-900/30' : isCaution ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-emerald-100 dark:bg-emerald-900/30'}`}>
                        <span className="text-[10px] font-bold" style={{ color: RISK_COLORS[zone] || '#95a5a6' }}>{zone}</span>
                        <div className="text-[10px] text-slate-400">风险</div>
                      </div>
                    </div>

                    {/* Risk details */}
                    {status?.active_alerts > 0 && (
                      <div className="flex items-center gap-1 text-[10px] text-red-500">
                        <Bell className="w-3 h-3" /> {status.active_alerts} 条预警
                      </div>
                    )}
                    {rssi > 55 && (
                      <div className="text-[10px] text-red-500 mt-0.5">建议安排恢复日</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-auto max-h-[600px]">
            <table className="data-table w-full text-xs">
              <thead className="sticky top-0 z-10 bg-white dark:bg-slate-900">
                <tr>
                  <th className="w-8"><input type="checkbox" checked={selected.size === paged.length && paged.length > 0} onChange={toggleAll} /></th>
                  <th>姓名</th><th>项目</th><th>年龄</th><th>训练年限</th>
                  <th className="text-center">ACWR</th><th className="text-center">风险等级</th>
                  <th className="text-center">RSSI</th><th className="text-center">预警</th>
                  <th className="text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((athlete: any) => {
                  const status = athlete.status;
                  const zone = status?.acwr_risk_zone || '安全区';
                  const acwr = status?.latest_acwr || 0;
                  const rssi = status?.rssi_score || 0;
                  const age = athlete.date_of_birth ? Math.floor((Date.now() - new Date(athlete.date_of_birth).getTime()) / 31557600000) : '?';
                  const isHigh = zone === '高风险区';
                  return (
                    <tr key={athlete.id} className={`${isHigh ? 'bg-red-50/50 dark:bg-red-950/10 border-l-2 border-l-red-500' : ''}`}>
                      <td><input type="checkbox" checked={selected.has(athlete.id)} onChange={() => toggleSelect(athlete.id)} /></td>
                      <td className="font-medium text-slate-800 dark:text-slate-200">{athlete.name}</td>
                      <td className="text-slate-500">{athlete.sport}</td>
                      <td className="text-slate-500">{age}</td>
                      <td className="text-slate-500">{athlete.training_years || '-'}</td>
                      <td className={`text-center font-mono font-bold ${acwr > 1.3 ? 'text-red-500' : acwr > 0 ? 'text-emerald-500' : 'text-slate-400'}`}>{acwr > 0 ? acwr.toFixed(2) : '--'}</td>
                      <td className="text-center"><span className={`badge ${zone === '高风险区' ? 'badge-high' : zone === '谨慎区' ? 'badge-mid' : 'badge-safe'}`}>{zone}</span></td>
                      <td className="text-center font-mono">{rssi.toFixed(0)}</td>
                      <td className="text-center">{status?.active_alerts > 0 ? <span className="badge badge-warn">{status.active_alerts}</span> : '-'}</td>
                      <td className="text-right">
                        <button onClick={() => navigate(`/athletes/${athlete.id}`)} className="text-xs text-cyan-500 hover:text-cyan-400 font-medium">详情</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sorted.length === 0 && !loading && (
        <div className="card text-center py-12"><p className="text-slate-400">无匹配运动员</p></div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 disabled:opacity-30 hover:bg-slate-50 dark:hover:bg-slate-800">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-slate-500">{page} / {totalPages} ({sorted.length} 人)</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 disabled:opacity-30 hover:bg-slate-50 dark:hover:bg-slate-800">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Add Athlete Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={e => { if (e.target === e.currentTarget) { setShowModal(false); resetForm(); }}}>
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">添加运动员</h3>
              <button onClick={() => { setShowModal(false); resetForm(); }} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><X className="w-5 h-5 text-slate-400" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">姓名 *</label>
                <input type="text" value={formName} onChange={e => setFormName(e.target.value)} className="input" placeholder="运动员姓名" />
                {formErrors.name && <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">出生日期 *</label>
                  <input type="date" value={formDob} onChange={e => setFormDob(e.target.value)} className="input" />
                  {formErrors.dateOfBirth && <p className="text-xs text-red-500 mt-1">{formErrors.dateOfBirth}</p>}
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">性别 *</label>
                  <select value={formGender} onChange={e => setFormGender(e.target.value)} className="input">
                    <option value="男">男</option><option value="女">女</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">运动项目 *</label>
                  <select value={formSport} onChange={e => setFormSport(e.target.value)} className="input">
                    {sportOptions.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  {formErrors.sport && <p className="text-xs text-red-500 mt-1">{formErrors.sport}</p>}
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">位置/项目</label>
                  <input type="text" value={formPosition} onChange={e => setFormPosition(e.target.value)} className="input" placeholder="如: 前锋、自由泳100m" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">训练年限</label>
                <input type="number" value={formTrainingYears} onChange={e => setFormTrainingYears(e.target.value)} className="input" placeholder="如: 3" min={0} max={30} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">惯用手</label>
                  <select value={formHandDominance} onChange={e => setFormHandDominance(e.target.value)} className="input">
                    {handOptions.map(h => <option key={h} value={h}>{h}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">惯用脚</label>
                  <select value={formDominantFoot} onChange={e => setFormDominantFoot(e.target.value)} className="input">
                    <option value="左">左</option><option value="右">右</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">伤病历史</label>
                <textarea value={formInjuryHistory} onChange={e => setFormInjuryHistory(e.target.value)} rows={2} className="input resize-none" placeholder="简要描述过往伤病..." />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">联系邮箱</label>
                  <input type="email" value={formContactEmail} onChange={e => setFormContactEmail(e.target.value)} className="input" placeholder="athlete@example.com" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">联系电话</label>
                  <input type="tel" value={formContactPhone} onChange={e => setFormContactPhone(e.target.value)} className="input" placeholder="138xxxxxxxx" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">教练备注</label>
                <textarea value={formCoachNotes} onChange={e => setFormCoachNotes(e.target.value)} rows={2} className="input resize-none" placeholder="教练对运动员的备注..." />
              </div>
              {formErrors.submit && <p className="text-xs text-red-500 bg-red-50 dark:bg-red-950/30 p-2 rounded">{formErrors.submit}</p>}
              {formSuccess && <p className="text-xs text-green-600 bg-green-50 dark:bg-green-950/30 p-2 rounded">{formSuccess}</p>}
              <button onClick={handleCreateAthlete} disabled={formSubmitting}
                className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50 mt-2">
                {formSubmitting ? '添加中...' : '确认添加'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
