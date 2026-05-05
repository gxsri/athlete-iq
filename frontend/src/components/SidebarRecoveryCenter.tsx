import React, { useState, useEffect } from 'react';
import {
  Heart, ChevronDown, ChevronUp, CheckCircle2, Circle, Dumbbell,
  Activity, BookOpen, Plus, RefreshCw, TrendingUp, Target,
} from 'lucide-react';
import {
  getRehabSchedule, getAthleteRehabPlans, completeRehabExercise,
  autoGenerateRehabPlan, getRehabExercises,
  RehabScheduleItem, RehabPlanSummary, RehabExercise,
} from '../services/api';

interface SidebarRecoveryCenterProps {
  athleteId: string;
}

const PHASE_LABELS: Record<string, { label: string; color: string }> = {
  inhibit: { label: '抑制', color: 'bg-blue-100 text-blue-600' },
  lengthen: { label: '拉长', color: 'bg-green-100 text-green-600' },
  activate: { label: '激活', color: 'bg-orange-100 text-orange-600' },
  integrate: { label: '整合', color: 'bg-purple-100 text-purple-600' },
};

export function SidebarRecoveryCenter({ athleteId }: SidebarRecoveryCenterProps) {
  const [expanded, setExpanded] = useState(false);
  const [plans, setPlans] = useState<RehabPlanSummary[]>([]);
  const [todayTasks, setTodayTasks] = useState<RehabScheduleItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Check-in modal
  const [checkinItem, setCheckinItem] = useState<RehabScheduleItem | null>(null);
  const [painBefore, setPainBefore] = useState(3);
  const [painAfter, setPainAfter] = useState(2);

  // Exercise browser modal
  const [showBrowser, setShowBrowser] = useState(false);
  const [exercises, setExercises] = useState<RehabExercise[]>([]);
  const [browserFilter, setBrowserFilter] = useState('');

  // Auto-generate
  const [generating, setGenerating] = useState(false);
  const [genPart, setGenPart] = useState('');
  const [message, setMessage] = useState('');

  const today = new Date().toISOString().split('T')[0];

  const fetchData = async () => {
    if (!athleteId) return;
    setLoading(true);
    try {
      const [planData, scheduleData] = await Promise.all([
        getAthleteRehabPlans(athleteId),
        getRehabSchedule(athleteId, today, today),
      ]);
      setPlans(planData);
      setTodayTasks(scheduleData);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchData();
  }, [athleteId]);

  const handleComplete = async () => {
    if (!checkinItem) return;
    try {
      await completeRehabExercise(checkinItem.id, painBefore, painAfter);
      setCheckinItem(null);
      fetchData();
      setMessage('打卡成功 ✓');
      setTimeout(() => setMessage(''), 2000);
    } catch { setMessage('操作失败'); }
  };

  const handleAutoGenerate = async () => {
    setGenerating(true);
    setMessage('');
    try {
      await autoGenerateRehabPlan(athleteId, genPart || undefined);
      setGenPart('');
      fetchData();
      setMessage('计划已生成 ✓');
    } catch { setMessage('生成失败'); }
    finally { setGenerating(false); };
  };

  const activePlan = plans.find(p => p.status === 'active');

  if (!athleteId) return null;

  return (
    <div className="border-t border-[#e5e5ea]">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2.5 text-xs font-semibold text-slate-600 hover:bg-[#e5e5ea]/30 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Heart className="w-3 h-3 text-red-400" /> 康复中心
          {activePlan && (
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" title="有活跃计划" />
          )}
        </span>
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3 max-h-[500px] overflow-y-auto">
          {loading ? (
            <div className="space-y-2">
              <div className="skeleton h-3 w-full" />
              <div className="skeleton h-10 w-full" />
              <div className="skeleton h-10 w-full" />
            </div>
          ) : (
            <>
              {/* Active Plan Summary */}
              {activePlan ? (
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                  <p className="text-[10px] font-semibold text-slate-700">{activePlan.name}</p>
                  <div className="flex items-center justify-between text-[9px] text-slate-400">
                    <span>{activePlan.start_date} ~ {activePlan.end_date}</span>
                    <span>{activePlan.completion_pct}%</span>
                  </div>
                  <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full transition-all"
                      style={{ width: `${activePlan.completion_pct}%` }} />
                  </div>
                </div>
              ) : (
                <p className="text-[10px] text-slate-400 text-center py-1">暂无活跃康复计划</p>
              )}

              {/* Today's Tasks */}
              {todayTasks.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold text-slate-500 flex items-center gap-1">
                    <Activity className="w-3 h-3" /> 今日任务 ({todayTasks.filter(t => t.completed).length}/{todayTasks.length})
                  </p>
                  {todayTasks.map(task => (
                    <div key={task.id}
                      className={`p-2 rounded-lg border text-[10px] transition-colors ${
                        task.completed
                          ? 'bg-green-50 border-green-200 opacity-60'
                          : 'bg-white border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${task.completed ? 'text-green-600 line-through' : 'text-slate-700'}`}>
                          {task.exercise_name}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] ${
                          PHASE_LABELS[task.target_body_part === 'shoulder' ? 'activate' : 'integrate']?.color || 'bg-slate-100 text-slate-500'
                        }`}>
                          {task.target_body_part}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-[9px] text-slate-400">
                        <span>{task.sets}组 × {task.reps}次</span>
                        <span>· 休息{task.rest_seconds}s</span>
                      </div>
                      {!task.completed && (
                        <button
                          onClick={() => setCheckinItem(task)}
                          className="mt-1.5 text-[9px] text-blue-500 hover:underline flex items-center gap-0.5"
                        >
                          <CheckCircle2 className="w-3 h-3" /> 打卡
                        </button>
                      )}
                      {task.completed && (
                        <div className="mt-1 text-[9px] text-green-500 flex items-center gap-0.5">
                          <CheckCircle2 className="w-3 h-3" /> 已完成
                          {task.pain_before != null && ` (疼痛: ${task.pain_before}→${task.pain_after})`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-1.5">
                <button onClick={() => setShowBrowser(true)}
                  className="flex-1 py-1.5 rounded-lg bg-blue-50 text-blue-600 text-[10px] font-medium hover:bg-blue-100 transition-colors flex items-center justify-center gap-1">
                  <BookOpen className="w-3 h-3" /> 动作库
                </button>
                <button onClick={handleAutoGenerate} disabled={generating}
                  className="flex-1 py-1.5 rounded-lg bg-purple-50 text-purple-600 text-[10px] font-medium hover:bg-purple-100 transition-colors flex items-center justify-center gap-1 disabled:opacity-50">
                  <RefreshCw className={`w-3 h-3 ${generating ? 'animate-spin' : ''}`} /> 自动生成
                </button>
              </div>

              {/* Auto-gen target selector */}
              {generating === false && genPart !== '' && (
                <div className="flex gap-1">
                  {['shoulder', 'knee', 'ankle', 'core'].map(p => (
                    <button key={p} onClick={() => { setGenPart(p); handleAutoGenerate(); }}
                      className={`px-2 py-1 rounded text-[9px] ${genPart === p ? 'bg-purple-500 text-white' : 'bg-slate-100 text-slate-500'}`}>
                      {p === 'shoulder' ? '肩' : p === 'knee' ? '膝' : p === 'ankle' ? '踝' : '核心'}
                    </button>
                  ))}
                  <button onClick={() => setGenPart('')} className="text-[9px] text-slate-400 px-1">✕</button>
                </div>
              )}

              {message && (
                <p className={`text-[9px] text-center ${message.includes('✓') ? 'text-green-500' : 'text-red-400'}`}>{message}</p>
              )}
            </>
          )}
        </div>
      )}

      {/* Check-in Modal */}
      {checkinItem && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-5 w-full max-w-xs shadow-xl animate-scale-in">
            <h4 className="text-sm font-bold text-slate-800 mb-3">康复打卡 — {checkinItem.exercise_name}</h4>
            <p className="text-xs text-slate-500 mb-3">{checkinItem.sets}组 × {checkinItem.reps}次</p>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-500">训练前疼痛评分 ({painBefore}/10)</label>
                <input type="range" value={painBefore} onChange={e => setPainBefore(Number(e.target.value))}
                  min={0} max={10} className="w-full" />
                <div className="flex justify-between text-[8px] text-slate-400">
                  <span>0 无痛</span><span>10 剧痛</span>
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500">训练后疼痛评分 ({painAfter}/10)</label>
                <input type="range" value={painAfter} onChange={e => setPainAfter(Number(e.target.value))}
                  min={0} max={10} className="w-full" />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={() => setCheckinItem(null)}
                className="flex-1 py-2 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium hover:bg-slate-200">
                取消
              </button>
              <button onClick={handleComplete}
                className="flex-1 py-2 rounded-lg bg-green-500 text-white text-xs font-medium hover:bg-green-600">
                确认完成
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Exercise Browser Modal */}
      {showBrowser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-5 w-full max-w-md max-h-[85vh] overflow-y-auto shadow-xl animate-scale-in">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-slate-800 flex items-center gap-1">
                <BookOpen className="w-4 h-4" /> 康复动作库
              </h4>
              <button onClick={() => setShowBrowser(false)}
                className="p-1 rounded hover:bg-slate-100 text-slate-400">✕</button>
            </div>
            <div className="flex gap-1 mb-3">
              {[
                { key: '', label: '全部' },
                { key: 'shoulder', label: '肩部' },
                { key: 'knee', label: '膝部' },
                { key: 'ankle', label: '踝部' },
                { key: 'core', label: '核心' },
              ].map(f => (
                <button key={f.key}
                  onClick={() => setBrowserFilter(f.key)}
                  className={`px-2 py-1 rounded text-[9px] ${browserFilter === f.key ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-500'}`}>
                  {f.label}
                </button>
              ))}
              <button onClick={() => {
                setShowBrowser(false);
                getRehabExercises(browserFilter || undefined).then(setExercises).catch(() => {});
              }}
                className="px-2 py-1 rounded text-[9px] bg-blue-50 text-blue-600 ml-auto">
                筛选
              </button>
            </div>
            <div className="space-y-2">
              {exercises.length === 0 && (
                <p className="text-xs text-slate-400 text-center py-4">点击筛选加载动作</p>
              )}
              {exercises.map(ex => (
                <div key={ex.id} className="p-3 rounded-lg border border-slate-200 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-700">{ex.name}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] ${PHASE_LABELS[ex.nasm_phase]?.color || 'bg-slate-100'}`}>
                      {PHASE_LABELS[ex.nasm_phase]?.label || ex.nasm_phase}
                    </span>
                  </div>
                  <p className="text-[9px] text-slate-500">{ex.purpose}</p>
                  <details className="text-[9px]">
                    <summary className="text-blue-500 cursor-pointer">查看步骤</summary>
                    <p className="text-slate-500 mt-1">{ex.instructions}</p>
                    {ex.common_mistakes && (
                      <p className="text-red-400 mt-0.5">⚠️ 常见错误: {ex.common_mistakes}</p>
                    )}
                  </details>
                  <div className="flex items-center gap-1 text-[8px] text-slate-400">
                    <span>难度: {'⭐'.repeat(ex.difficulty)}</span>
                    {ex.equipment_needed?.length > 0 && <span>· {ex.equipment_needed.join(', ')}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
