import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { format, subDays, startOfWeek } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import {
  ChevronLeft, ChevronRight, Plus, Trash2, AlertTriangle, BarChart3, Target,
  Heart, Activity, Settings, PenLine, Save, Zap, Clock, TrendingUp, TrendingDown,
  Moon, Droplets, Brain, Calendar, CheckCircle2, X, Download, Edit3,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, ComposedChart, ReferenceLine, Legend } from 'recharts';
import {
  createTrainingLog, submitDailyReadiness, getAthletes, getTrainingLogs, exportCSV,
  getReadinessHistory, getACWRTimeSeries, getPlannedSessions, getCoachComments, getExercises,
  getPlanVsActualTrend, PlanVsActualTrendDay,
  Athlete, TrainingLog as ApiTrainingLog, ExerciseLibrary,
} from '../services/api';

const trainingTypes = ['力量', '耐力', '速度', '技战术', '柔韧', '混合'];

function loadPlanTargets() {
  try { const s = localStorage.getItem('aiq-plan-v2'); return s ? JSON.parse(s) : [
    { dayOfWeek: 0, targetLoad: 0 }, { dayOfWeek: 1, targetLoad: 200 }, { dayOfWeek: 2, targetLoad: 150 },
    { dayOfWeek: 3, targetLoad: 220 }, { dayOfWeek: 4, targetLoad: 120 }, { dayOfWeek: 5, targetLoad: 300 }, { dayOfWeek: 6, targetLoad: 50 },
  ]; } catch { return []; }
}
function savePlanTargets(t: any[]) { localStorage.setItem('aiq-plan-v2', JSON.stringify(t)); }
function loadCoachNotes(): Record<string, string> {
  try { return JSON.parse(localStorage.getItem('aiq-notes-v2') || '{}'); } catch { return {}; }
}
function saveCoachNotes(n: Record<string, string>) { localStorage.setItem('aiq-notes-v2', JSON.stringify(n)); }

const DAYS = ['周一','周二','周三','周四','周五','周六','周日'];

export function TrainingLog() {
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [athleteId, setAthleteId] = useState('');
  const [viewDate, setViewDate] = useState(new Date());
  const dateStr = format(viewDate, 'yyyy-MM-dd');
  const today = new Date().toISOString().split('T')[0];
  const weekStart = startOfWeek(viewDate, { weekStartsOn: 1 });

  // Data
  const [logs, setLogs] = useState<ApiTrainingLog[]>([]);
  const [acwrData, setAcwrData] = useState<any>(null);
  const [readinessList, setReadinessList] = useState<any[]>([]);
  const [exercises, setExercises] = useState<ExerciseLibrary[]>([]);
  const [planVsActual, setPlanVsActual] = useState<PlanVsActualTrendDay[]>([]);
  const [loading, setLoading] = useState(false);

  // Plan & notes
  const [planTargets, setPlanTargets] = useState(loadPlanTargets);
  const [coachNotes, setCoachNotes] = useState(loadCoachNotes);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [planVals, setPlanVals] = useState(planTargets.map((t: any) => t.targetLoad));

  // Log form
  const [showLogForm, setShowLogForm] = useState(false);
  const [logType, setLogType] = useState('力量'); const [logDesc, setLogDesc] = useState('');
  const [logDur, setLogDur] = useState(90); const [logRpe, setLogRpe] = useState(6);
  const [logMsg, setLogMsg] = useState('');

  // Readiness form
  const [showReadiness, setShowReadiness] = useState(false);
  const [rSleep, setRSleep] = useState(3); const [rFatigue, setRFatigue] = useState(2);
  const [rSoreness, setRSoreness] = useState(2); const [rStress, setRStress] = useState(3);
  const [rMsg, setRMsg] = useState('');

  // Nutrition / Mental / Exercise picker
  const [exSearch, setExSearch] = useState(''); const [exCat, setExCat] = useState('全部');
  const [showExPicker, setShowExPicker] = useState(false);
  const [showNutrition, setShowNutrition] = useState(false);
  const [nutMeal, setNutMeal] = useState('午餐'); const [nutDesc, setNutDesc] = useState('');
  const [nutWater, setNutWater] = useState(6); const [nutWell, setNutWell] = useState(4);
  const [nutMsg, setNutMsg] = useState('');
  const [mentalMood, setMentalMood] = useState(3); const [mentalStress, setMentalStress] = useState(3);
  const [mentalFocus, setMentalFocus] = useState(3); const [mentalMsg, setMentalMsg] = useState('');
  const [showMental, setShowMental] = useState(false);

  useEffect(() => {
    getAthletes().then(data => { setAthletes(data); if (data.length && !athleteId) setAthleteId(data[0].id); }).catch(() => {});
    getExercises({}).then((d: any) => setExercises(d.exercises || d || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    Promise.all([
      getTrainingLogs(athleteId, 60),
      getACWRTimeSeries(athleteId, 60),
      getReadinessHistory(athleteId, 30),
      getPlanVsActualTrend(athleteId, 30).catch(() => ({ trend: [] })),
    ]).then(([l, a, r, pv]) => {
      setLogs(l); setAcwrData(a); setReadinessList(r);
      setPlanVsActual((pv as any).trend || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [athleteId]);

  const athlete = athletes.find(a => a.id === athleteId);
  const todayLogs = logs.filter(l => l.training_date === dateStr);
  const weekLogs = logs.filter(l => l.training_date >= format(weekStart, 'yyyy-MM-dd') && l.training_date <= dateStr);
  const todayLoad = todayLogs.reduce((s, l) => s + (l.session_load || 0), 0);
  const weekLoad = weekLogs.reduce((s, l) => s + (l.session_load || 0), 0);
  const todayReadiness = readinessList.find(r => r.record_date === dateStr || r.record_date === today);

  // ACWR
  const acwrVal = useMemo(() => {
    if (acwrData?.acwr?.length) {
      const i = acwrData.acwr.length - 1;
      return { acute: acwrData.acute_load?.[i] || 0, chronic: acwrData.chronic_load?.[i] || 1, ratio: acwrData.acwr[i] || 0 };
    }
    const c7 = subDays(viewDate, 7); const c28 = subDays(viewDate, 28);
    const r7 = logs.filter(l => l.training_date >= format(c7, 'yyyy-MM-dd') && l.training_date <= dateStr);
    const r28 = logs.filter(l => l.training_date >= format(c28, 'yyyy-MM-dd') && l.training_date <= dateStr);
    const a7 = r7.length ? r7.reduce((s, l) => s + (l.session_load || 0), 0) / 7 : 0;
    const a28 = r28.length ? r28.reduce((s, l) => s + (l.session_load || 0), 0) / 28 : 1;
    return { acute: a7, chronic: a28, ratio: a28 > 0 ? a7 / a28 : 0 };
  }, [acwrData, logs, dateStr]);

  const acwrOk = acwrVal.ratio >= 0.8 && acwrVal.ratio <= 1.3;
  const acwrWarn = acwrVal.ratio > 1.3;
  const fatigueLevel = acwrVal.ratio > 1.5 ? '极高' : acwrVal.ratio > 1.3 ? '偏高' : acwrVal.ratio > 0.8 ? '正常' : '偏低';
  const fatigueColor = acwrVal.ratio > 1.3 ? 'text-rose-400' : acwrVal.ratio > 0.8 ? 'text-emerald-400' : 'text-amber-400';

  // Plan vs actual
  const todayPlan = planTargets.find((p: any) => p.dayOfWeek === viewDate.getDay())?.targetLoad || 0;
  const weekPlan = planTargets.reduce((s: number, p: any) => s + p.targetLoad, 0);
  const todayPct = todayPlan > 0 ? Math.round((todayLoad / todayPlan) * 100) : 0;
  const weekPct = weekPlan > 0 ? Math.round((weekLoad / weekPlan) * 100) : 0;

  // Readiness score
  const readinessScore = useMemo(() => {
    if (!todayReadiness) return null;
    const sl = todayReadiness.sleep_quality || 3; const fa = todayReadiness.fatigue_level || 3;
    const so = todayReadiness.muscle_soreness || 3; const st = todayReadiness.stress_motivation || 3;
    return Math.round((sl * 2 + (10 - fa) + (10 - so) + (10 - st)) / 4);
  }, [todayReadiness]);

  // 14-day chart with real plan-vs-actual data
  const chartData = useMemo(() => {
    const d: any[] = [];
    const pvMap = new Map(planVsActual.map(p => [p.date, p]));
    for (let i = 13; i >= 0; i--) {
      const dt = subDays(viewDate, i); const ds = format(dt, 'yyyy-MM-dd');
      const dayLogs = logs.filter(l => l.training_date === ds);
      const actual = dayLogs.reduce((s, l) => s + (l.session_load || 0), 0);
      // Use API plan-vs-actual data if available, fall back to localStorage targets
      const pvDay = pvMap.get(ds);
      const plan = pvDay ? pvDay.planned_load : (planTargets.find((p: any) => p.dayOfWeek === dt.getDay())?.targetLoad || 0);
      const c7 = subDays(dt, 7); const c28 = subDays(dt, 28);
      const l7 = logs.filter(l => l.training_date >= format(c7, 'yyyy-MM-dd') && l.training_date <= ds);
      const l28 = logs.filter(l => l.training_date >= format(c28, 'yyyy-MM-dd') && l.training_date <= ds);
      const a7 = l7.length ? l7.reduce((s, l) => s + (l.session_load || 0), 0) / 7 : 0;
      const a28 = l28.length ? l28.reduce((s, l) => s + (l.session_load || 0), 0) / 28 : 1;
      d.push({
        date: format(dt, 'M/d'), actual, plan,
        completion: pvDay?.completion_rate || (plan > 0 ? Math.round(actual / plan * 100) : 0),
        acwr: a28 > 0 ? +(a7 / a28).toFixed(2) : 0,
        high: a28 > 0 && a7 / a28 > 1.3,
      });
    }
    return d;
  }, [logs, viewDate, planTargets, planVsActual]);

  const weekLoadTrend = useMemo(() => {
    const weeks: any[] = [];
    for (let w = 7; w >= 0; w--) {
      const ws = subDays(viewDate, w * 7);
      const we = subDays(ws, -6);
      const wLogs = logs.filter(l => l.training_date >= format(ws, 'yyyy-MM-dd') && l.training_date <= format(we, 'yyyy-MM-dd'));
      weeks.push({ week: format(ws, 'M/d'), load: wLogs.reduce((s, l) => s + (l.session_load || 0), 0) });
    }
    return weeks;
  }, [logs, viewDate]);

  const coachNoteKey = `${athleteId}_${dateStr}`;
  const coachNote = coachNotes[coachNoteKey] || '';

  // Auto-generate coach note when ACWR > 1.3
  useEffect(() => {
    if (acwrVal.ratio > 1.3 && !coachNotes[coachNoteKey]?.includes('ACWR')) {
      const autoMsg = `⚠️ ACWR过高(${acwrVal.ratio.toFixed(2)})，建议未来1-2天降低训练强度至${Math.round(todayPlan * 0.6)}以下`;
      const n = { ...coachNotes, [coachNoteKey]: autoMsg };
      setCoachNotes(n); saveCoachNotes(n);
    }
  }, [acwrVal.ratio]);

  // Handlers
  const saveLog = async () => {
    if (!logDur || !logRpe) return;
    try { await createTrainingLog({ athlete_id: athleteId, training_date: dateStr, training_type: logType, duration_minutes: logDur, rpe: logRpe, cycle_phase: '准备期', description: logDesc || logType }); setLogMsg('已保存'); setShowLogForm(false); fetchLogs(); } catch (e: any) { setLogMsg(e.message); }
  };
  const deleteLog = async (id: string) => { /* no delete API, just refresh */ fetchLogs(); };
  const fetchLogs = () => { if (athleteId) getTrainingLogs(athleteId, 60).then(setLogs).catch(() => {}); };
  const saveReadiness = async () => {
    try { await submitDailyReadiness({ athlete_id: athleteId, record_date: today, sleep_quality: rSleep, muscle_soreness: rSoreness, fatigue_level: rFatigue, stress_motivation: rStress }); setRMsg('已记录'); setShowReadiness(false); getReadinessHistory(athleteId, 30).then(setReadinessList).catch(() => {}); } catch (e: any) { setRMsg(e.message); }
  };
  const saveNutrition = async () => {
    try { const { submitNutritionLog } = await import('../services/api'); await submitNutritionLog({ athlete_id: athleteId, record_date: today, meal: nutMeal, description: nutDesc, water: nutWater, wellbeing: nutWell }); setNutMsg('已保存'); setShowNutrition(false); } catch (e: any) { setNutMsg(e.message); }
  };
  const saveMental = async () => {
    try { const { submitMentalLog } = await import('../services/api'); await submitMentalLog({ athlete_id: athleteId, record_date: today, mood: mentalMood, stress: mentalStress, focus: mentalFocus }); setMentalMsg('已保存'); setShowMental(false); } catch (e: any) { setMentalMsg(e.message); }
  };

  const filteredEx = exercises.filter(e => {
    if (exCat !== '全部' && e.category !== exCat) return false;
    if (exSearch) { const q = exSearch.toLowerCase(); return e.name.toLowerCase().includes(q) || (e.description||'').toLowerCase().includes(q); }
    return true;
  });

  return (
    <div className="space-y-5">
      {/* ====== COROS-STYLE TOP BAR ====== */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <select value={athleteId} onChange={e => setAthleteId(e.target.value)}
            className="w-auto min-w-[200px] px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-900 dark:text-slate-100">
            {athletes.map(a => <option key={a.id} value={a.id}>{a.name} · {a.sport}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-1">
          <button onClick={() => setViewDate(d => { const n = new Date(d); n.setDate(n.getDate()-1); return n; })} className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><ChevronLeft className="w-4 h-4" /></button>
          <span className="text-sm font-medium px-2 min-w-[130px] text-center">{format(viewDate, 'M月d日 EEE', { locale: zhCN })}</span>
          <button onClick={() => setViewDate(d => { const n = new Date(d); n.setDate(n.getDate()+1); return n; })} className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><ChevronRight className="w-4 h-4" /></button>
          <button onClick={() => setViewDate(new Date())} className="px-2 py-1 text-xs rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">今天</button>
        </div>
      </div>

      {/* ====== SUMMARY METRIC BAR (Coros-style) ====== */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">今日负荷</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">{todayLoad.toFixed(0)}</div>
          <div className="text-[11px] text-slate-400 mt-1">RPE×时长</div>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">本周累计</div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">{weekLoad.toFixed(0)}</div>
          <div className={`text-[11px] mt-1 ${weekPct >= 90 ? 'text-emerald-400' : weekPct < 50 ? 'text-rose-400' : 'text-amber-400'}`}>计划 {weekPct}%</div>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">ACWR</div>
          <div className={`text-2xl font-bold ${acwrOk ? 'text-emerald-400' : acwrWarn ? 'text-rose-400' : 'text-amber-400'}`}>{acwrVal.ratio.toFixed(2)}</div>
          <div className="text-[11px] text-slate-400 mt-1">{acwrOk ? '最佳区间' : acwrWarn ? '高风险' : '需关注'}</div>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4">
          <div className="text-[11px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">恢复状态</div>
          <div className={`text-2xl font-bold ${readinessScore ? (readinessScore >= 7 ? 'text-emerald-400' : readinessScore >= 5 ? 'text-amber-400' : 'text-rose-400') : 'text-slate-300'}`}>
            {readinessScore !== null ? readinessScore : '—'}<span className="text-sm font-normal text-slate-400">{readinessScore !== null ? '/10' : ''}</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">{fatigueLevel}疲劳</div>
        </div>
      </div>

      {/* ====== MAIN CONTENT: Chart + Right Panel ====== */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Chart Area (3 cols) */}
        <div className="lg:col-span-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">训练负荷趋势</h3>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-cyan-400/70" /> 实际</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-slate-300 dark:bg-slate-600" /> 计划</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-0.5 rounded bg-rose-400" style={{width:12}} /> ACWR</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{top:5,right:20,left:-10,bottom:5}}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.4} vertical={false} />
              <XAxis dataKey="date" tick={{fontSize:10,fill:'#94a3b8'}} tickLine={false} axisLine={false} />
              <YAxis yAxisId="left" tick={{fontSize:10,fill:'#94a3b8'}} tickLine={false} axisLine={false} />
              <YAxis yAxisId="right" orientation="right" domain={[0,2.5]} tick={{fontSize:10,fill:'#94a3b8'}} tickLine={false} axisLine={false} />
              <Tooltip content={({active,payload,label}:any) => !active||!payload?.length ? null : (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 shadow-lg text-xs">
                  <p className="font-semibold mb-1">{label}</p>
                  {payload.map((p:any,i:number) => <p key={i} className="flex items-center gap-1.5" style={{color:p.color}}><span className="w-2 h-2 rounded-sm" style={{backgroundColor:p.color}}/>{p.name}: {typeof p.value==='number'?p.value.toFixed(1):p.value}</p>)}
                </div>
              )} />
              <ReferenceLine yAxisId="right" y={1.3} stroke="#f87171" strokeDasharray="5 3" strokeWidth={1} />
              <ReferenceLine yAxisId="right" y={0.8} stroke="#60a5fa" strokeDasharray="5 3" strokeWidth={1} />
              <Bar yAxisId="left" dataKey="actual" name="实际负荷" fill="#22d3ee" fillOpacity={0.55} radius={[3,3,0,0]} maxBarSize={22} />
              <Bar yAxisId="left" dataKey="plan" name="计划负荷" fill="#cbd5e1" fillOpacity={0.5} radius={[3,3,0,0]} maxBarSize={22} />
              <Line yAxisId="right" type="monotone" dataKey="acwr" name="ACWR" stroke="#f87171" strokeWidth={2} dot={(p:any) => p.payload.high ? <circle cx={p.cx} cy={p.cy} r={5} fill="#f87171" stroke="#fff" strokeWidth={2}/> : <circle cx={p.cx} cy={p.cy} r={2} fill="#f87171"/>} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Right Panel (1 col) */}
        <div className="space-y-4">
          {/* Readiness */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300">准备状态</h4>
              <button onClick={() => setShowReadiness(true)} className="text-[10px] text-cyan-500 hover:text-cyan-400 font-medium">
                {todayReadiness ? '更新' : '+ 记录'}
              </button>
            </div>
            {readinessScore !== null ? (
              <div className="text-center">
                <div className={`text-3xl font-bold ${readinessScore >= 7 ? 'text-emerald-400' : readinessScore >= 5 ? 'text-amber-400' : 'text-rose-400'}`}>{readinessScore}/10</div>
                <div className="text-[10px] text-slate-400 mt-1">综合准备指数</div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-3">今日未评估</p>
            )}
          </div>

          {/* Plan vs Actual */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300">计划完成</h4>
              <button onClick={() => setShowPlanModal(true)} className="text-[10px] text-slate-400 hover:text-slate-600"><Settings className="w-3 h-3"/></button>
            </div>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[10px] mb-0.5"><span className="text-slate-400">今日</span><span className={todayPct>110?'text-rose-400':todayPct<70?'text-amber-400':'text-emerald-400'}>{todayPct}%</span></div>
                <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden"><div className={`h-full rounded-full ${todayPct>110?'bg-rose-400':todayPct<70?'bg-amber-400':'bg-cyan-400'}`} style={{width:`${Math.min(todayPct,150)}%`}}/></div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] mb-0.5"><span className="text-slate-400">本周</span><span className={weekPct>110?'text-rose-400':weekPct<70?'text-amber-400':'text-emerald-400'}>{weekPct}%</span></div>
                <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden"><div className={`h-full rounded-full ${weekPct>110?'bg-rose-400':weekPct<70?'bg-amber-400':'bg-cyan-400'}`} style={{width:`${Math.min(weekPct,150)}%`}}/></div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="space-y-2">
            <button onClick={() => setShowLogForm(true)} className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 text-black text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2">
              <Plus className="w-4 h-4" /> 记录训练
            </button>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setShowNutrition(true)} className="py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl text-xs text-slate-600 dark:text-slate-400 flex items-center justify-center gap-1">
                <Droplets className="w-3 h-3" /> 营养
              </button>
              <button onClick={() => setShowMental(true)} className="py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl text-xs text-slate-600 dark:text-slate-400 flex items-center justify-center gap-1">
                <Brain className="w-3 h-3" /> 心理
              </button>
            </div>
          </div>

          {/* ACWR Alert */}
          {acwrVal.ratio > 1.3 && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <div>ACWR 偏高（{acwrVal.ratio.toFixed(2)}），建议未来1-2天将训练负荷降至 {Math.round(todayPlan * 0.6)} 以下</div>
            </div>
          )}
        </div>
      </div>

      {/* ====== TODAY'S PLAN FROM PLANNER ====== */}
      {todayPlan && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            今日训练计划 — {todayPlan.session_name}
            {todayPlan.notes && <span className="text-xs text-slate-400 ml-2 font-normal">{todayPlan.notes}</span>}
          </h3>
          {todayPlan.exercises && todayPlan.exercises.length > 0 ? (
            <div className="space-y-2">
              {todayPlan.exercises.map((ex: any, i: number) => {
                const isLogged = logs.some((l: ApiTrainingLog) => l.training_date === dateStr);
                return (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-sm">
                  <div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">{ex.exercise?.name || `动作${i+1}`}</span>
                    <span className="text-xs text-slate-400 ml-2">
                      {ex.target_sets}组×{ex.target_reps}次 · RPE{ex.target_rpe} · 休息{ex.rest_seconds}s
                    </span>
                  </div>
                  {isLogged ? (
                    <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5"/> 已记录</span>
                  ) : (
                    <button onClick={() => {
                      setLogType(todayPlan?.training_type || '力量');
                      setLogDesc(ex.exercise?.name || '');
                      setLogDur(30); setLogRpe(ex.target_rpe || 6);
                      setLogMsg(''); setShowLogForm(true);
                    }} className="text-cyan-500 text-xs flex items-center gap-1 hover:text-cyan-400">
                      <Edit3 className="w-3.5 h-3.5"/> 快速记录
                    </button>
                  )}
                </div>
              )})}
            </div>
          ) : (
            <p className="text-sm text-slate-400 text-center py-4">计划中暂无训练动作，前往<Link to="/planner" className="text-cyan-500 hover:underline">训练计划器</Link>添加</p>
          )}
        </div>
      )}

      {/* ====== TODAY'S LOGS + NOTES ====== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Training Logs List */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">今日训练记录</h3>
          {todayLogs.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-6">暂无记录 — 点击右侧"记录训练"添加</p>
          ) : (
            <div className="space-y-2">
              {todayLogs.map(log => (
                <div key={log.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                  <div className="flex items-center gap-3">
                    <span className={`w-1.5 h-8 rounded-full ${log.training_type === '力量' ? 'bg-rose-400' : log.training_type === '耐力' ? 'bg-amber-400' : log.training_type === '速度' ? 'bg-purple-400' : log.training_type === '技战术' ? 'bg-blue-400' : 'bg-emerald-400'}`} />
                    <div>
                      <div className="text-sm font-medium text-slate-700 dark:text-slate-200">{log.training_type} · {log.description || '训练'}</div>
                      <div className="text-xs text-slate-400">{log.duration_minutes}分钟 · RPE {log.rpe} · 负荷 {log.session_load?.toFixed(0)}</div>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400">{log.training_date}</span>
                </div>
              ))}
            </div>
          )}
          {/* Recent history */}
          {logs.length > 0 && (
            <details className="mt-3">
              <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-600">最近记录 ({logs.length}条)</summary>
              <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                {logs.slice(0,20).map(log => (
                  <div key={log.id} className="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-slate-50 dark:hover:bg-slate-800">
                    <span className="text-slate-500">{log.training_date}</span>
                    <span>{log.training_type}</span>
                    <span className="font-mono text-slate-400">{log.session_load?.toFixed(0)}</span>
                  </div>
                ))}
              </div>
            </details>
          )}
        </div>

        {/* Coach Notes */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <PenLine className="w-4 h-4 text-slate-400" /> 教练备注
          </h3>
          <textarea
            value={coachNote}
            onChange={e => { const n = {...coachNotes, [coachNoteKey]: e.target.value}; setCoachNotes(n); saveCoachNotes(n); }}
            placeholder="记录教练观察、技术反馈、调整建议..."
            rows={5}
            className="w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-lg text-sm resize-none"
          />
          {/* Week plan mini view */}
          <div>
            <p className="text-[10px] text-slate-400 mb-1.5">本周目标负荷</p>
            <div className="flex gap-1">
              {DAYS.map((d, i) => {
                const target = planTargets.find((p: any) => p.dayOfWeek === (i === 6 ? 0 : i+1))?.targetLoad || 0;
                const isToday = (viewDate.getDay() === (i === 6 ? 0 : i+1));
                return (
                  <div key={i} className={`flex-1 text-center py-1.5 rounded text-[9px] ${isToday ? 'bg-cyan-500 text-black font-bold' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                    <div>{d}</div>
                    <div>{target}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ====== MODALS ====== */}
      {showLogForm && <Modal onClose={()=>setShowLogForm(false)} title="记录训练">
        <div className="space-y-3">
          <select value={logType} onChange={e=>setLogType(e.target.value)}>{trainingTypes.map(t=><option key={t}>{t}</option>)}</select>
          <input value={logDesc} onChange={e=>setLogDesc(e.target.value)} placeholder="训练描述..."/>
          <div className="flex gap-3"><input type="number" value={logDur} onChange={e=>setLogDur(+e.target.value)} placeholder="时长(分)" min={1}/><span className="text-xs text-slate-400 self-center">负荷: {logDur*logRpe}</span></div>
          <div><label className="text-xs text-slate-500">RPE ({logRpe})</label><input type="range" value={logRpe} onChange={e=>setLogRpe(+e.target.value)} min={1} max={10}/></div>
          <button onClick={saveLog} className="btn btn-primary w-full justify-center"><Save className="w-4 h-4"/> 保存</button>
          {logMsg && <p className="text-xs text-center text-green-500">{logMsg}</p>}
        </div>
      </Modal>}

      {showReadiness && <Modal onClose={()=>setShowReadiness(false)} title="准备状态">
        <div className="space-y-3">
          <div><label className="text-xs">睡眠 ({rSleep}/5)</label><input type="range" value={rSleep} onChange={e=>setRSleep(+e.target.value)} min={1} max={5}/></div>
          <div><label className="text-xs">疲劳 ({rFatigue}/10)</label><input type="range" value={rFatigue} onChange={e=>setRFatigue(+e.target.value)} min={0} max={10}/></div>
          <div><label className="text-xs">酸痛 ({rSoreness}/10)</label><input type="range" value={rSoreness} onChange={e=>setRSoreness(+e.target.value)} min={0} max={10}/></div>
          <div><label className="text-xs">压力 ({rStress}/10)</label><input type="range" value={rStress} onChange={e=>setRStress(+e.target.value)} min={0} max={10}/></div>
          <div className="text-center text-lg font-bold text-cyan-500">综合: {Math.round((rSleep*2+(10-rFatigue)+(10-rSoreness)+(10-rStress))/4)}/10</div>
          <button onClick={saveReadiness} className="btn btn-primary w-full justify-center"><Save className="w-4 h-4"/> 保存</button>
          {rMsg && <p className="text-xs text-center text-green-500">{rMsg}</p>}
        </div>
      </Modal>}

      {showNutrition && <Modal onClose={()=>setShowNutrition(false)} title="营养记录">
        <div className="space-y-3">
          <select value={nutMeal} onChange={e=>setNutMeal(e.target.value)}><option>早餐</option><option>午餐</option><option>加餐</option><option>晚餐</option></select>
          <textarea value={nutDesc} onChange={e=>setNutDesc(e.target.value)} placeholder="食物描述..." rows={2}/>
          <div><label className="text-xs">水分 ({nutWater}杯)</label><input type="range" value={nutWater} onChange={e=>setNutWater(+e.target.value)} min={0} max={20}/></div>
          <div><label className="text-xs">健康感 ({nutWell}/5)</label><input type="range" value={nutWell} onChange={e=>setNutWell(+e.target.value)} min={1} max={5}/></div>
          <button onClick={saveNutrition} className="btn btn-primary w-full justify-center">保存</button>
          {nutMsg && <p className="text-xs text-center text-green-500">{nutMsg}</p>}
        </div>
      </Modal>}

      {showMental && <Modal onClose={()=>setShowMental(false)} title="心理状态">
        <div className="space-y-3">
          <div className="flex gap-2">
            <select value={mentalMood} onChange={e=>setMentalMood(+e.target.value)} className="flex-1"><option value={1}>😞 低落</option><option value={2}>😐 一般</option><option value={3}>🙂 良好</option><option value={4}>😊 愉快</option><option value={5}>😄 极佳</option></select>
          </div>
          <div><label className="text-xs">压力 ({mentalStress}/5)</label><input type="range" value={mentalStress} onChange={e=>setMentalStress(+e.target.value)} min={1} max={5}/></div>
          <div><label className="text-xs">专注 ({mentalFocus}/5)</label><input type="range" value={mentalFocus} onChange={e=>setMentalFocus(+e.target.value)} min={1} max={5}/></div>
          <button onClick={saveMental} className="btn btn-primary w-full justify-center">保存</button>
          {mentalMsg && <p className="text-xs text-center text-green-500">{mentalMsg}</p>}
        </div>
      </Modal>}

      {showPlanModal && <Modal onClose={()=>setShowPlanModal(false)} title="周计划设置">
        <div className="space-y-2">
          {DAYS.map((d,i)=><div key={i} className="flex items-center gap-3"><span className="text-xs w-10">{d}</span><input type="number" value={planVals[i]} onChange={e=>{const n=[...planVals];n[i]=+e.target.value;setPlanVals(n)}}/></div>)}
          <button onClick={()=>{const t=planVals.map((v,i)=>({dayOfWeek:i===6?0:i+1,targetLoad:v}));setPlanTargets(t);savePlanTargets(t);setShowPlanModal(false)}} className="btn btn-primary w-full justify-center mt-2">保存</button>
        </div>
      </Modal>}
    </div>
  );
}

function Modal({children,onClose,title}:{children:React.ReactNode;onClose:()=>void;title:string}) {
  return <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
    <div className="bg-white dark:bg-slate-900 rounded-xl p-5 w-full max-w-sm shadow-xl border border-slate-200 dark:border-slate-700" onClick={e=>e.stopPropagation()}>
      <div className="flex items-center justify-between mb-3"><h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">{title}</h4><button onClick={onClose} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"><X className="w-4 h-4"/></button></div>
      {children}
    </div>
  </div>;
}
