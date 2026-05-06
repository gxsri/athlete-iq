import React, { useState, useEffect } from 'react';
import { Save, Plus, Copy, FileText, Calendar, Upload, X, GripVertical, CalendarDays, User, ChevronLeft, ChevronRight } from 'lucide-react';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { QuickAddExercise } from '../components/QuickAddExercise';
import { ExerciseCard, ExerciseData } from '../components/ExerciseCard';
import { getAthletes, createPlannedSession, getTrainingTemplates, getPlannedSessions, getWeekPlan, batchCreateSessions, getExercises, Athlete, TrainingTemplate, WeekPlan, WeekPlanDay } from '../services/api';
import type { ExerciseLibrary } from '../services/api';

const trainingTypes = ['力量', '耐力', '速度', '技战术', '柔韧', '混合'];

export function Planner() {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [sessionName, setSessionName] = useState('');
  const [trainingType, setTrainingType] = useState('力量');
  const [notes, setNotes] = useState('');
  const [exercises, setExercises] = useState<ExerciseData[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showWeekView, setShowWeekView] = useState(true);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [selectedAthleteId, setSelectedAthleteId] = useState<string>('');
  const [selectedAthletes, setSelectedAthletes] = useState<string[]>([]);
  const [copyDate, setCopyDate] = useState('');
  const [apiAthletes, setApiAthletes] = useState<Athlete[]>([]);
  const [templates, setTemplates] = useState<TrainingTemplate[]>([]);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [weekPlan, setWeekPlan] = useState<WeekPlan | null>(null);
  const [weekStart, setWeekStart] = useState(() => {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    return monday.toISOString().split('T')[0];
  });
  const [planMessage, setPlanMessage] = useState('');
  const [planError, setPlanError] = useState('');
  const [batchStartDate, setBatchStartDate] = useState('');
  const [batchEndDate, setBatchEndDate] = useState('');
  const [batchWeekdays, setBatchWeekdays] = useState<number[]>([0, 1, 2, 3, 4, 5]);

  useEffect(() => {
    getAthletes().then(setApiAthletes).catch(() => {});
    setTemplateLoading(true);
    getTrainingTemplates().then(setTemplates).catch(() => {}).finally(() => setTemplateLoading(false));
  }, []);

  useEffect(() => {
    if (selectedAthleteId && showWeekView) {
      getWeekPlan(selectedAthleteId, weekStart).then(setWeekPlan).catch(() => {});
    }
  }, [selectedAthleteId, weekStart, showWeekView]);

  const navigateWeek = (dir: number) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + dir * 7);
    setWeekStart(d.toISOString().split('T')[0]);
  };

  const addExercise = (ex: ExerciseLibrary) => {
    setExercises(prev => [...prev, {
      name: ex.name,
      weight: ex.preset_params?.weight_kg || 0,
      reps: ex.preset_params?.reps || 8,
      sets: ex.preset_params?.sets || 3,
      rpe: ex.preset_params?.rpe || 6,
      rest: ex.preset_params?.rest_seconds || 60,
      notes: '',
      exerciseId: ex.id,
    }]);
    setShowSidebar(false);
  };

  const updateExercise = (index: number, field: string, value: number | string) => {
    setExercises(prev => prev.map((e, i) => i === index ? { ...e, [field]: value } : e));
  };

  const removeExercise = (index: number) => {
    setExercises(prev => prev.filter((_, i) => i !== index));
  };

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const handleDragEnd = (event: any) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setExercises(prev => {
      const oldIdx = prev.findIndex((_, i) => String(i) === active.id);
      const newIdx = prev.findIndex((_, i) => String(i) === over.id);
      if (oldIdx < 0 || newIdx < 0) return prev;
      const arr = [...prev];
      const [moved] = arr.splice(oldIdx, 1);
      arr.splice(newIdx, 0, moved);
      return arr;
    });
  };

  const loadTemplate = (template: TrainingTemplate) => {
    setSessionName(template.name);
    const ttype = template.intensity_zone === '高' || template.intensity_zone === '极高' ? '力量' :
                  template.intensity_zone === '低' ? '柔韧' : '混合';
    setTrainingType(ttype);
    setNotes(template.description || '');
    const content = template.content || {};
    const segments = content.segments || [];
    if (segments.length > 0) {
      const parsed = segments.map((seg: any) => ({
        name: seg.name || '训练段落',
        weight: seg.weight || 0,
        reps: seg.reps || 1,
        sets: seg.sets || 1,
        rpe: seg.rpe || 5,
        rest: seg.rest || seg.rest_seconds || (seg.duration_min ? seg.duration_min * 60 : 60),
        notes: [seg.content, seg.evidence ? `📚 ${seg.evidence}` : ''].filter(Boolean).join('\n'),
      }));
      setExercises(parsed);
    }
    setShowTemplateModal(false);
  };

  const copyFromPrevious = async () => {
    if (!copyDate || !selectedAthleteId) return;
    try {
      const sessions = await getPlannedSessions(selectedAthleteId, copyDate, copyDate);
      const session = sessions[0];
      if (session) {
        setSessionName(session.session_name || '');
        setTrainingType(session.training_type || '力量');
        if (session.exercises) {
          setExercises(session.exercises.map((e: any) => ({
            name: '',
            weight: e.target_weight_kg || 0,
            reps: e.target_reps || 0,
            sets: e.target_sets || 0,
            rpe: e.target_rpe || 0,
            rest: e.rest_seconds || 0,
          })));
        }
      }
    } catch { /* ignore copy errors */ }
    setShowCopyModal(false);
    setCopyDate('');
  };

  const handleBatchCreate = async () => {
    if (!selectedAthleteId || !batchStartDate || !batchEndDate || exercises.length === 0) {
      setPlanError('请选择运动员、日期范围和至少一个训练动作');
      return;
    }
    setPlanError('');
    setPlanMessage('');
    try {
      const result = await batchCreateSessions({
        athlete_id: selectedAthleteId,
        start_date: batchStartDate,
        end_date: batchEndDate,
        weekdays: batchWeekdays,
        session_name: sessionName || '训练课',
        training_type: trainingType,
        exercises: exercises.map((ex, i) => {
          const eid = (ex as any).exerciseId || '';
          const base = {
            order_index: i,
            target_weight_kg: ex.weight || undefined,
            target_reps: ex.reps || undefined,
            target_sets: ex.sets || undefined,
            rest_seconds: ex.rest || undefined,
            target_rpe: ex.rpe || undefined,
            notes: ex.notes || undefined,
          };
          return eid ? { ...base, exercise_id: eid } : base;
        }),
      });
      setPlanMessage(`批量创建了 ${result.sessions_created} 个课次`);
      setShowBatchModal(false);
      if (selectedAthleteId) {
        getWeekPlan(selectedAthleteId, weekStart).then(setWeekPlan).catch(() => {});
      }
    } catch (err: any) {
      setPlanError(err.message || '批量创建失败');
    }
  };

  const handleSave = async () => {
    if (!sessionName || exercises.length === 0) {
      setPlanError('请填写课次名称并添加至少一个训练动作');
      return;
    }
    if (!selectedAthleteId) {
      setPlanError('请先选择运动员');
      return;
    }
    setPlanError('');
    setPlanMessage('');
    try {
      await createPlannedSession({
        athlete_id: selectedAthleteId,
        plan_date: date,
        session_name: sessionName,
        training_type: trainingType,
        notes: notes || undefined,
        exercises: exercises.map((ex, i) => {
          const eid = (ex as any).exerciseId || '';
          const base = {
            order_index: i,
            target_weight_kg: ex.weight || undefined,
            target_reps: ex.reps || undefined,
            target_sets: ex.sets || undefined,
            rest_seconds: ex.rest || undefined,
            target_rpe: ex.rpe || undefined,
            notes: ex.notes || undefined,
          };
          return eid ? { ...base, exercise_id: eid } : base;
        }),
      });
      setPlanMessage(`计划已保存: ${sessionName}`);
      if (selectedAthleteId && showWeekView) {
        getWeekPlan(selectedAthleteId, weekStart).then(setWeekPlan).catch(() => {});
      }
    } catch (err: any) {
      setPlanError(err.message || '保存失败');
    }
  };

  const selectedAthlete = apiAthletes.find(a => a.id === selectedAthleteId);
  const weekdayToggle = (day: number) => {
    setBatchWeekdays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day].sort());
  };
  const dayLabels = ['一', '二', '三', '四', '五', '六', '日'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">训练计划器</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">编辑训练课次 · 分配运动员 · 模板复用</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowWeekView(!showWeekView)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${showWeekView ? 'bg-cyan-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'}`}
          >
            <CalendarDays className="w-4 h-4" /> 周视图
          </button>
          <button
            onClick={() => setShowTemplateModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <FileText className="w-4 h-4" /> 加载模板
          </button>
          <button
            onClick={() => setShowCopyModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <Copy className="w-4 h-4" /> 复制计划
          </button>
          <button
            onClick={() => setShowBatchModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-purple-500 text-white rounded-lg text-sm font-medium hover:bg-purple-600 transition-colors"
          >
            <CalendarDays className="w-4 h-4" /> 批量生成
          </button>
          <button
            onClick={() => setShowAssignModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
          >
            <Upload className="w-4 h-4" /> 分配运动员
          </button>
        </div>
      </div>

      {/* Athlete Selector */}
      <div className="card">
        <div className="flex items-center gap-3">
          <User className="w-5 h-5 text-slate-400" />
          <select
            value={selectedAthleteId}
            onChange={e => setSelectedAthleteId(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">选择运动员...</option>
            {apiAthletes.map(a => (
              <option key={a.id} value={a.id}>{a.name} · {a.sport}</option>
            ))}
          </select>
          {selectedAthlete && (
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {selectedAthlete.position_or_event || ''} · 训练{selectedAthlete.training_years || 0}年
            </span>
          )}
        </div>
      </div>

      {/* Week View */}
      {showWeekView && selectedAthleteId && (
        <div className="card space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              周计划概览 ({weekPlan?.week_start || ''} ~ {weekPlan?.week_end || ''})
            </h4>
            <div className="flex items-center gap-1">
              <button onClick={() => navigateWeek(-1)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <ChevronLeft className="w-4 h-4 text-slate-400" />
              </button>
              <button onClick={() => setWeekStart(new Date().toISOString().split('T')[0])} className="px-2 py-1 text-xs text-cyan-500 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 rounded">
                本周
              </button>
              <button onClick={() => navigateWeek(1)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-7 gap-2">
            {(weekPlan?.days || Array.from({ length: 7 }, (_, i) => {
              const d = new Date(weekStart);
              d.setDate(d.getDate() + i);
              return { date: d.toISOString().split('T')[0], day_name: ['周一','周二','周三','周四','周五','周六','周日'][i], is_today: false, sessions: [] };
            })).map((day: WeekPlanDay, i: number) => {
              const isToday = day.is_today || day.date === date;
              const hasSession = day.sessions.length > 0;
              const totalLoad = day.sessions.reduce((sum, s) => sum + (s.planned_load || 0), 0);
              return (
                <div key={i}
                  onClick={() => setDate(day.date)}
                  className={`p-2 rounded-lg border text-center cursor-pointer text-xs transition-colors ${
                    isToday ? 'border-cyan-400 bg-cyan-50 dark:bg-cyan-900/20' :
                    hasSession ? 'border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10' :
                    'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                  }`}>
                  <div className="text-[10px] text-slate-400">{day.day_name}</div>
                  <div className="font-medium mt-1 text-slate-700 dark:text-slate-200">
                    {new Date(day.date).getDate()}
                  </div>
                  {hasSession ? (
                    <div className="mt-1 space-y-0.5">
                      {day.sessions.map(s => (
                        <div key={s.id} className="text-[9px] leading-tight">
                          <div className="font-medium text-slate-600 dark:text-slate-300 truncate">{s.session_name}</div>
                          <div className={`font-mono ${s.status === 'completed' ? 'text-emerald-500' : 'text-cyan-500'}`}>
                            {s.planned_load || 0}
                          </div>
                        </div>
                      ))}
                      <div className="text-[9px] font-semibold text-slate-500 mt-0.5">
                        计: {totalLoad.toFixed(0)}
                      </div>
                    </div>
                  ) : (
                    <div className="text-[10px] text-slate-300 dark:text-slate-600 mt-1">—</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex gap-4">
        {/* Main Area */}
        <div className="flex-1 space-y-4">
          {/* Session Header */}
          <div className="card space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">训练日期</label>
                <div className="relative">
                  <Calendar className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="date"
                    value={date}
                    onChange={e => setDate(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">课次名称</label>
                <input
                  type="text"
                  placeholder="如: 下肢力量日"
                  value={sessionName}
                  onChange={e => setSessionName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">训练类型</label>
                <select
                  value={trainingType}
                  onChange={e => setTrainingType(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {trainingTypes.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">备注</label>
              <textarea
                placeholder="课次备注..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            {/* Planned Load Preview */}
            {exercises.length > 0 && (
              <div className="flex items-center gap-3 px-3 py-2 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg">
                <span className="text-xs text-cyan-600 dark:text-cyan-400 font-medium">
                  计划负荷: {exercises.reduce((sum, ex) => sum + (ex.sets || 0) * (ex.reps || 0) * ((ex.rpe || 5) / 10) * 10 + (ex.weight || 0) * (ex.sets || 0) * 0.5, 0).toFixed(1)}
                </span>
                <span className="text-xs text-slate-400">|</span>
                <span className="text-xs text-slate-500">{exercises.length} 个动作</span>
              </div>
            )}
          </div>

          {/* Exercise List */}
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">训练动作 ({exercises.length})</h4>
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-medium hover:bg-blue-600 transition-colors"
              >
                <Plus className="w-3 h-3" /> 快速添加
              </button>
            </div>

            {exercises.length > 0 ? (
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={exercises.map((_, i) => String(i))} strategy={verticalListSortingStrategy}>
                  <div className="space-y-2">
                    {exercises.map((ex, i) => (
                      <SortableExercise key={i} id={String(i)}>
                        <ExerciseCard
                          index={i}
                          exercise={ex}
                          onChange={(field, value) => updateExercise(i, field, value)}
                          onRemove={() => removeExercise(i)}
                        />
                      </SortableExercise>
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-slate-400 dark:text-slate-500">点击"快速添加"按钮或从模板加载训练动作</p>
              </div>
            )}
          </div>

          {/* Save */}
          <button
            onClick={handleSave}
            disabled={!selectedAthleteId}
            className="flex items-center gap-2 px-6 py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-4 h-4" /> 保存计划
          </button>
          {planMessage && <p className="text-xs text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400 p-2 rounded">{planMessage}</p>}
          {planError && <p className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 dark:text-red-400 p-2 rounded">{planError}</p>}
        </div>

        {/* Sidebar: Quick Add Exercise */}
        {showSidebar && (
          <div className="w-80 shrink-0">
            <div className="card space-y-3 sticky top-6">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">训练动作库</h4>
                <button onClick={() => setShowSidebar(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              <QuickAddExercise onAdd={addExercise} />
            </div>
          </div>
        )}
      </div>

      {/* Template Picker Modal */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black/40 dark:bg-black/70 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-lg shadow-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">选择训练模板</h3>
              <button onClick={() => setShowTemplateModal(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="space-y-2 max-h-[32rem] overflow-y-auto">
              {templateLoading ? (
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-4">加载中...</p>
              ) : templates.length === 0 ? (
                <p className="text-xs text-slate-400 dark:text-slate-500 text-center py-4">暂无可用模板</p>
              ) : (
                templates.map(t => {
                  const intensityColors: Record<string, string> = {
                    '低': 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
                    '中': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400',
                    '高': 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400',
                    '极高': 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
                  };
                  const segments = t.content?.segments || [];
                  const totalMin = t.content?.total_minutes || t.content?.target_duration_min || 0;
                  return (
                  <div
                    key={t.id}
                    onClick={() => loadTemplate(t)}
                    className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-slate-700 dark:text-slate-200">{t.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${intensityColors[t.intensity_zone || ''] || 'bg-slate-100 text-slate-600'}`}>
                        {t.intensity_zone || '?'}强度
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {totalMin}分钟 · {segments.length}个训练段落
                      {t.weekly_frequency && ` · ${t.weekly_frequency}`}
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 line-clamp-2">{t.description}</div>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {(t.target_focus || []).map(f => (
                        <span key={f} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">{f}</span>
                      ))}
                    </div>
                  </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Copy from Previous Modal */}
      {showCopyModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-sm shadow-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">复制历史计划</h3>
              <button onClick={() => setShowCopyModal(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">选择日期</label>
                <input
                  type="date"
                  value={copyDate}
                  onChange={e => setCopyDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={copyFromPrevious}
                disabled={!copyDate || !selectedAthleteId}
                className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                复制
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Create Modal */}
      {showBatchModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md shadow-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">批量生成计划</h3>
              <button onClick={() => setShowBatchModal(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1">开始日期</label>
                  <input type="date" value={batchStartDate} onChange={e => setBatchStartDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">结束日期</label>
                  <input type="date" value={batchEndDate} onChange={e => setBatchEndDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">每周训练日</label>
                <div className="flex gap-1">
                  {dayLabels.map((label, i) => (
                    <button key={i} onClick={() => weekdayToggle(i)}
                      className={`flex-1 py-1.5 rounded text-xs font-medium transition-colors ${
                        batchWeekdays.includes(i)
                          ? 'bg-blue-500 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                      }`}>{label}</button>
                  ))}
                </div>
              </div>
              <div className="text-xs text-slate-500">
                将当前 {exercises.length} 个动作复制到每个训练日
              </div>
              <button
                onClick={handleBatchCreate}
                disabled={!batchStartDate || !batchEndDate || exercises.length === 0 || !selectedAthleteId}
                className="w-full py-2.5 bg-purple-500 text-white rounded-lg text-sm font-medium hover:bg-purple-600 transition-colors disabled:opacity-50"
              >
                批量生成
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign to Athletes Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md shadow-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">分配运动员</h3>
              <button onClick={() => setShowAssignModal(false)} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
              {apiAthletes.map(a => (
                <label key={a.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedAthletes.includes(a.id)}
                    onChange={e => {
                      if (e.target.checked) {
                        setSelectedAthletes(prev => [...prev, a.id]);
                      } else {
                        setSelectedAthletes(prev => prev.filter(id => id !== a.id));
                      }
                    }}
                    className="rounded border-slate-300 text-blue-500 focus:ring-blue-500"
                  />
                  <div>
                    <div className="text-sm font-medium text-slate-700 dark:text-slate-200">{a.name}</div>
                    <div className="text-xs text-slate-400 dark:text-slate-500">{a.sport} · {a.position_or_event || ''}</div>
                  </div>
                </label>
              ))}
            </div>
            <button
              onClick={() => setShowAssignModal(false)}
              className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
              disabled={selectedAthletes.length === 0}
            >
              确认分配 ({selectedAthletes.length}人)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function SortableExercise({ children, id }: { children: React.ReactNode; id: string }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-1">
      <div {...attributes} {...listeners} className="cursor-grab p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded shrink-0">
        <GripVertical className="w-4 h-4 text-slate-300 dark:text-slate-600" />
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}
