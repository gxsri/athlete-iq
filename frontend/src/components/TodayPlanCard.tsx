import React, { useState, useEffect } from 'react';
import { CheckCircle, Circle, Play, Clock, Dumbbell, Target, Calendar } from 'lucide-react';
import { getTodayPlan, logExerciseForPlan, getACWRStatus, autoAdjustPlan, ACWRStatus } from '../services/api';

interface TodayExercise {
  planned_exercise_id: string;
  exercise_id: string;
  exercise_name: string;
  category: string;
  target_sets: number | null;
  target_reps: number | null;
  target_rpe: number | null;
  target_weight_kg: number | null;
  rest_seconds: number | null;
}

interface TodaySession {
  session_id: string;
  session_name: string;
  training_type: string;
  planned_load: number;
  status: string;
  exercises: TodayExercise[];
}

export function TodayPlanCard({ athleteId }: { athleteId: string }) {
  const [sessions, setSessions] = useState<TodaySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [recordingId, setRecordingId] = useState<string | null>(null);
  const [actualSets, setActualSets] = useState('');
  const [actualRpe, setActualRpe] = useState('6');
  const [actualWeight, setActualWeight] = useState('');
  const [actualDuration, setActualDuration] = useState('30');
  const [message, setMessage] = useState('');
  const [loggedIds, setLoggedIds] = useState<Set<string>>(new Set());
  const [acwrStatus, setAcwrStatus] = useState<ACWRStatus | null>(null);
  const [adjusting, setAdjusting] = useState(false);

  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    getTodayPlan(athleteId)
      .then((data: any) => {
        setSessions(data.sessions || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    getACWRStatus(athleteId)
      .then(setAcwrStatus)
      .catch(() => {});
  }, [athleteId]);

  const handleRecord = async (sessionId: string, ex: TodayExercise) => {
    if (!actualSets || !actualRpe) return;
    try {
      await logExerciseForPlan(sessionId, {
        planned_exercise_id: ex.planned_exercise_id,
        actual_sets_completed: parseInt(actualSets) || ex.target_sets || 0,
        actual_reps_completed: ex.target_reps || 0,
        actual_rpe: parseInt(actualRpe) || 6,
        actual_duration_min: parseInt(actualDuration) || 30,
        actual_weight_kg: parseFloat(actualWeight) || ex.target_weight_kg || undefined,
      });
      setLoggedIds(prev => new Set(prev).add(ex.planned_exercise_id));
      setRecordingId(null);
      setMessage(`已记录: ${ex.exercise_name}`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err: any) {
      setMessage(`错误: ${err.message}`);
    }
  };

  const handleAutoAdjust = async () => {
    if (!acwrStatus || !athleteId) return;
    setAdjusting(true);
    try {
      await autoAdjustPlan(athleteId, acwrStatus.recommended_adjustment_pct, 'ACWR预警自动调整');
      setMessage(`已自动调整未来计划 (${acwrStatus.recommended_adjustment_pct}%)`);
      // Refresh ACWR status
      const status = await getACWRStatus(athleteId);
      setAcwrStatus(status);
    } catch (err: any) {
      setMessage(`调整失败: ${err.message}`);
    }
    setAdjusting(false);
  };

  if (loading) {
    return <div className="card"><div className="skeleton h-20 rounded-lg" /></div>;
  }

  const totalPlannedLoad = sessions.reduce((sum, s) => sum + (s.planned_load || 0), 0);
  const totalExercises = sessions.reduce((sum, s) => sum + s.exercises.length, 0);

  return (
    <div className="space-y-4">
      {/* ACWR Alert Banner */}
      {acwrStatus && acwrStatus.needs_adjustment && (
        <div className={`rounded-xl p-4 border ${
          acwrStatus.current_acwr > 1.5
            ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900'
            : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900'
        }`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-red-800 dark:text-red-300">
                ACWR = {acwrStatus.current_acwr.toFixed(2)} · {acwrStatus.risk_zone}
              </p>
              <p className="text-xs mt-1 text-red-600 dark:text-red-400">{acwrStatus.suggestion}</p>
              <p className="text-xs mt-0.5 text-slate-500 dark:text-slate-400">
                急性负荷: {acwrStatus.acute_load_7d.toFixed(1)} | 慢性负荷: {acwrStatus.chronic_load_28d.toFixed(1)}
              </p>
            </div>
            <button
              onClick={handleAutoAdjust}
              disabled={adjusting}
              className="shrink-0 px-3 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
            >
              {adjusting ? '调整中...' : `自动调整 (${acwrStatus.recommended_adjustment_pct}%)`}
            </button>
          </div>
        </div>
      )}

      {/* Today's Plan */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-500" /> 今日训练计划
          </h3>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1"><Dumbbell className="w-3 h-3" /> {totalExercises} 动作</span>
            <span className="font-mono font-medium text-cyan-600 dark:text-cyan-400">计划负荷: {totalPlannedLoad.toFixed(1)}</span>
          </div>
        </div>

        {message && (
          <div className={`p-2 rounded text-xs ${message.startsWith('错误') ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400'}`}>
            {message}
          </div>
        )}

        {sessions.length === 0 ? (
          <div className="text-center py-6 text-slate-400 dark:text-slate-500">
            <Calendar className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">今日暂无训练计划</p>
            <p className="text-xs mt-0.5">前往训练计划器为运动员安排课次</p>
          </div>
        ) : (
          sessions.map(session => (
            <div key={session.session_id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${session.status === 'completed' ? 'bg-emerald-500' : 'bg-cyan-500'}`} />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{session.session_name}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                    {session.training_type}
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                  负荷: {session.planned_load?.toFixed(1) || '0'}
                </span>
              </div>

              {/* Exercise list */}
              <div className="space-y-1.5 pl-4">
                {session.exercises.map(ex => {
                  const isLogged = loggedIds.has(ex.planned_exercise_id);
                  return (
                    <div key={ex.planned_exercise_id} className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                      <div className="flex items-center gap-2 min-w-0">
                        {isLogged ? (
                          <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-300 dark:text-slate-600 shrink-0" />
                        )}
                        <div className="min-w-0">
                          <div className="text-sm text-slate-700 dark:text-slate-200 truncate">{ex.exercise_name}</div>
                          <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                            {ex.target_sets && ex.target_reps ? `${ex.target_sets}组×${ex.target_reps}次` : ''}
                            {ex.target_weight_kg ? ` ${ex.target_weight_kg}kg` : ''}
                            {ex.target_rpe ? ` · RPE ${ex.target_rpe}` : ''}
                            {ex.rest_seconds ? ` · 休${ex.rest_seconds}s` : ''}
                          </div>
                        </div>
                      </div>

                      {!isLogged && (
                        recordingId === ex.planned_exercise_id ? (
                          <div className="flex items-center gap-1.5 shrink-0">
                            <input
                              type="number" placeholder="组" value={actualSets}
                              onChange={e => setActualSets(e.target.value)}
                              className="w-10 px-1 py-0.5 text-xs rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700"
                              autoFocus
                            />
                            <input
                              type="number" placeholder="RPE" value={actualRpe}
                              onChange={e => setActualRpe(e.target.value)}
                              className="w-10 px-1 py-0.5 text-xs rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700"
                            />
                            <button
                              onClick={() => handleRecord(session.session_id, ex)}
                              className="px-2 py-0.5 bg-emerald-500 text-white rounded text-xs font-medium hover:bg-emerald-600"
                            >
                              <CheckCircle className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setRecordingId(null)}
                              className="px-1 py-0.5 text-slate-400 hover:text-slate-600 rounded text-xs"
                            >
                              ×
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => {
                              setRecordingId(ex.planned_exercise_id);
                              setActualSets(String(ex.target_sets || 0));
                              setActualRpe(String(ex.target_rpe || 6));
                            }}
                            className="flex items-center gap-1 px-2 py-1 bg-cyan-500 text-white rounded text-xs font-medium hover:bg-cyan-600 transition-colors shrink-0"
                          >
                            <Play className="w-3 h-3" /> 记录
                          </button>
                        )
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
