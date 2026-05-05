import React, { useState, useEffect } from 'react';
import {
  Heart, Activity, BookOpen, CheckCircle2, Circle, TrendingUp,
  RefreshCw, Plus, Target, Dumbbell, Search, ChevronDown, ChevronUp,
} from 'lucide-react';
import {
  getAthletes, getRehabExercises, getAthleteRehabPlans, getRehabSchedule,
  getRehabProgress, autoGenerateRehabPlan, completeRehabExercise,
  Athlete, RehabExercise, RehabPlanSummary, RehabScheduleItem, RehabProgress,
} from '../services/api';

const PHASE_LABELS: Record<string, string> = {
  inhibit: 'bg-blue-100 text-blue-600',
  lengthen: 'bg-green-100 text-green-600',
  activate: 'bg-orange-100 text-orange-600',
  integrate: 'bg-purple-100 text-purple-600',
};

const PHASE_NAMES: Record<string, string> = {
  inhibit: '抑制', lengthen: '拉长', activate: '激活', integrate: '整合',
};

const BODY_PART_NAMES: Record<string, string> = {
  shoulder: '肩部', knee: '膝部', ankle: '踝部', core: '核心',
};

export function RehabCenter() {
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [loading, setLoading] = useState(false);

  // Data
  const [plans, setPlans] = useState<RehabPlanSummary[]>([]);
  const [schedule, setSchedule] = useState<RehabScheduleItem[]>([]);
  const [exercises, setExercises] = useState<RehabExercise[]>([]);
  const [progress, setProgress] = useState<RehabProgress | null>(null);

  // Filters
  const [exFilterPart, setExFilterPart] = useState('');
  const [exFilterPhase, setExFilterPhase] = useState('');
  const [exSearch, setExSearch] = useState('');

  // Modals
  const [showCheckin, setShowCheckin] = useState<RehabScheduleItem | null>(null);
  const [painBefore, setPainBefore] = useState(3);
  const [painAfter, setPainAfter] = useState(2);
  const [generating, setGenerating] = useState(false);
  const [genPart, setGenPart] = useState('');
  const [message, setMessage] = useState('');

  const today = new Date().toISOString().split('T')[0];

  useEffect(() => {
    getAthletes().then(setAthletes).catch(() => {});
    getRehabExercises().then(setExercises).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedAthleteId) return;
    setLoading(true);
    Promise.all([
      getAthleteRehabPlans(selectedAthleteId),
      getRehabSchedule(selectedAthleteId),
      getRehabProgress(selectedAthleteId, 30),
    ]).then(([p, s, pr]) => {
      setPlans(p);
      setSchedule(s);
      setProgress(pr);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [selectedAthleteId]);

  const handleCheckin = async () => {
    if (!showCheckin) return;
    try {
      await completeRehabExercise(showCheckin.id, painBefore, painAfter);
      setShowCheckin(null);
      // Refresh
      const [p, s, pr] = await Promise.all([
        getAthleteRehabPlans(selectedAthleteId),
        getRehabSchedule(selectedAthleteId),
        getRehabProgress(selectedAthleteId, 30),
      ]);
      setPlans(p); setSchedule(s); setProgress(pr);
      setMessage('打卡成功 ✓');
      setTimeout(() => setMessage(''), 2000);
    } catch { setMessage('操作失败'); }
  };

  const handleAutoGenerate = async () => {
    setGenerating(true);
    try {
      await autoGenerateRehabPlan(selectedAthleteId, genPart || undefined);
      const [p, s, pr] = await Promise.all([
        getAthleteRehabPlans(selectedAthleteId),
        getRehabSchedule(selectedAthleteId),
        getRehabProgress(selectedAthleteId, 30),
      ]);
      setPlans(p); setSchedule(s); setProgress(pr);
      setMessage('计划已生成 ✓');
    } catch { setMessage('生成失败'); }
    finally { setGenerating(false); }
  };

  const activePlan = plans.find(p => p.status === 'active');
  const todayTasks = schedule.filter(s => s.scheduled_date === today);
  const filteredEx = exercises.filter(e => {
    if (exFilterPart && e.target_body_part !== exFilterPart) return false;
    if (exFilterPhase && e.nasm_phase !== exFilterPhase) return false;
    if (exSearch && !e.name.includes(exSearch) && !e.purpose?.includes(exSearch)) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">康复中心</h2>
          <p className="text-sm text-slate-500 mt-1">NASM OPT 纠正性训练 · 个性化康复计划 · 进度追踪</p>
        </div>
        <select
          value={selectedAthleteId}
          onChange={e => setSelectedAthleteId(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
        >
          <option value="">选择运动员...</option>
          {athletes.map(a => <option key={a.id} value={a.id}>{a.name} ({a.sport})</option>)}
        </select>
      </div>

      {!selectedAthleteId ? (
        <div className="card text-center py-16">
          <Heart className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500 font-medium">请先选择运动员</p>
          <p className="text-sm text-slate-400 mt-1">选择运动员后查看康复计划与动作库</p>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          <div className="skeleton h-32 w-full rounded-xl" />
          <div className="grid grid-cols-2 gap-4">
            <div className="skeleton h-64 rounded-xl" />
            <div className="skeleton h-64 rounded-xl" />
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Plan + Today Tasks */}
          <div className="lg:col-span-1 space-y-4">
            {/* Active Plan */}
            <div className="card space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-500" /> 当前康复计划
              </h3>
              {activePlan ? (
                <>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                    <p className="text-sm font-bold text-slate-800">{activePlan.name}</p>
                    <p className="text-xs text-slate-500">{activePlan.start_date} ~ {activePlan.end_date}</p>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">完成率</span>
                      <span className="font-bold text-green-600">{activePlan.completion_pct}%</span>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${activePlan.completion_pct}%` }} />
                    </div>
                  </div>
                  {/* Auto-generate */}
                  <div className="space-y-2">
                    <p className="text-xs text-slate-500">自动生成新计划</p>
                    <div className="flex gap-1">
                      {['shoulder', 'knee', 'ankle', 'core'].map(p => (
                        <button key={p} onClick={() => { setGenPart(p); handleAutoGenerate(); }}
                          disabled={generating}
                          className={`flex-1 py-1.5 rounded text-[10px] font-medium transition-colors ${
                            genPart === p && generating
                              ? 'bg-purple-200 text-purple-400'
                              : 'bg-purple-50 text-purple-600 hover:bg-purple-100'
                          }`}>
                          {BODY_PART_NAMES[p]}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-4">
                  <p className="text-xs text-slate-400 mb-2">暂无活跃康复计划</p>
                  <div className="flex gap-1 justify-center">
                    {['shoulder', 'knee', 'ankle', 'core'].map(p => (
                      <button key={p} onClick={() => { setGenPart(p); handleAutoGenerate(); }}
                        disabled={generating}
                        className={`px-3 py-1.5 rounded text-[10px] font-medium ${
                          generating ? 'bg-slate-100 text-slate-400' : 'bg-purple-50 text-purple-600 hover:bg-purple-100'
                        }`}>
                        {BODY_PART_NAMES[p]}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {message && (
                <p className={`text-xs text-center ${message.includes('✓') ? 'text-green-500' : 'text-red-400'}`}>{message}</p>
              )}
            </div>

            {/* Today's Tasks */}
            <div className="card space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">
                今日任务 ({todayTasks.filter(t => t.completed).length}/{todayTasks.length})
              </h3>
              {todayTasks.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-3">今日暂无康复任务</p>
              ) : (
                todayTasks.map(task => (
                  <div key={task.id}
                    className={`p-2.5 rounded-lg border text-xs transition-colors ${
                      task.completed ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'
                    }`}>
                    <div className="flex items-center justify-between">
                      <span className={`font-medium ${task.completed ? 'text-green-600 line-through' : 'text-slate-700'}`}>
                        {task.exercise_name}
                      </span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] ${PHASE_LABELS[task.target_body_part === 'shoulder' ? 'activate' : 'inhibit'] || 'bg-slate-100 text-slate-500'}`}>
                        {BODY_PART_NAMES[task.target_body_part] || task.target_body_part}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {task.sets}组 × {task.reps}次 · 休息{task.rest_seconds}s
                    </div>
                    {!task.completed ? (
                      <button onClick={() => setShowCheckin(task)}
                        className="mt-1.5 text-[10px] text-blue-500 hover:underline">
                        打卡完成
                      </button>
                    ) : (
                      <span className="mt-1 text-[10px] text-green-500 flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" /> 已完成
                        {task.pain_before != null && ` (VAS ${task.pain_before}→${task.pain_after})`}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Progress */}
            {progress && (
              <div className="card space-y-2">
                <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-500" /> 进度追踪
                </h3>
                <div className="text-center">
                  <span className="text-2xl font-bold text-blue-600">{progress.progress_pct}%</span>
                  <p className="text-xs text-slate-400">{progress.completed_count}/{progress.total_exercises} 已完成</p>
                </div>
                {progress.pain_trend.length > 0 && (
                  <div>
                    <p className="text-[10px] text-slate-400 mb-1">疼痛趋势（平均VAS）</p>
                    <div className="flex gap-0.5">
                      {progress.pain_trend.slice(-7).map((d, i) => (
                        <div key={i} className="flex-1 text-center">
                          <div className="h-10 bg-slate-100 rounded relative">
                            <div className="absolute bottom-0 left-0 right-0 bg-red-400 rounded-b opacity-30"
                              style={{ height: `${d.avg_pain_before * 10}%` }} />
                            <div className="absolute bottom-0 left-0 right-0 bg-green-400 rounded-b opacity-50"
                              style={{ height: `${d.avg_pain_after * 10}%` }} />
                          </div>
                          <span className="text-[8px] text-slate-400">{d.date.slice(5)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column: Exercise Library */}
          <div className="lg:col-span-2">
            <div className="card space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-amber-500" /> 康复动作库
                <span className="text-xs text-slate-400 font-normal">({exercises.length} 个动作)</span>
              </h3>

              {/* Filters */}
              <div className="flex flex-wrap gap-2">
                <div className="relative flex-1 min-w-[160px]">
                  <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input type="text" value={exSearch} onChange={e => setExSearch(e.target.value)}
                    placeholder="搜索动作..." className="w-full pl-7 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs" />
                </div>
                <select value={exFilterPart} onChange={e => setExFilterPart(e.target.value)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-white">
                  <option value="">全部部位</option>
                  {Object.entries(BODY_PART_NAMES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <select value={exFilterPhase} onChange={e => setExFilterPhase(e.target.value)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-white">
                  <option value="">全部阶段</option>
                  {Object.entries(PHASE_NAMES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>

              {/* Exercise Grid */}
              {filteredEx.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">未找到匹配动作</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[600px] overflow-y-auto">
                  {filteredEx.map(ex => (
                    <div key={ex.id} className="p-3 rounded-lg border border-slate-200 space-y-2 hover:border-blue-200 transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-700">{ex.name}</span>
                        <div className="flex items-center gap-1">
                          <span className={`px-1.5 py-0.5 rounded text-[9px] ${PHASE_LABELS[ex.nasm_phase] || 'bg-slate-100 text-slate-500'}`}>
                            {PHASE_NAMES[ex.nasm_phase]}
                          </span>
                          <span className="text-[9px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                            {BODY_PART_NAMES[ex.target_body_part]}
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">{ex.purpose}</p>
                      <details className="text-xs">
                        <summary className="text-blue-500 cursor-pointer">详细步骤</summary>
                        <p className="text-slate-500 mt-1">{ex.instructions}</p>
                        {ex.common_mistakes && (
                          <p className="text-red-400 mt-1 text-[11px]">⚠️ {ex.common_mistakes}</p>
                        )}
                      </details>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span>难度 {'⭐'.repeat(ex.difficulty)}</span>
                        {ex.equipment_needed?.length > 0 && (
                          <span>· {ex.equipment_needed.join(', ')}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Check-in Modal */}
      {showCheckin && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-5 w-full max-w-xs shadow-xl">
            <h4 className="text-sm font-bold mb-3">打卡 — {showCheckin.exercise_name}</h4>
            <p className="text-xs text-slate-500 mb-3">{showCheckin.instructions?.slice(0, 80)}...</p>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-500">训练前疼痛 ({painBefore}/10)</label>
                <input type="range" value={painBefore} onChange={e => setPainBefore(Number(e.target.value))} min={0} max={10} className="w-full" />
              </div>
              <div>
                <label className="text-[10px] text-slate-500">训练后疼痛 ({painAfter}/10)</label>
                <input type="range" value={painAfter} onChange={e => setPainAfter(Number(e.target.value))} min={0} max={10} className="w-full" />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={() => setShowCheckin(null)} className="flex-1 py-2 rounded-lg bg-slate-100 text-xs">取消</button>
              <button onClick={handleCheckin} className="flex-1 py-2 rounded-lg bg-green-500 text-white text-xs hover:bg-green-600">确认完成</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
