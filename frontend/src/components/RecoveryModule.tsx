import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, Circle, Heart, Zap, Dumbbell, Moon } from 'lucide-react';
import {
  getTodayRecovery, completeSuggestion,
  RecoverySuggestionResponse, RecoveryExercise,
} from '../services/api';

interface RecoveryModuleProps {
  athleteId: string;
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  recovery: <Heart className="w-3 h-3" />,
  strength_balance: <Dumbbell className="w-3 h-3" />,
  technique: <Zap className="w-3 h-3" />,
  active_recovery: <RefreshCw className="w-3 h-3" />,
  load_management: <Zap className="w-3 h-3" />,
  sleep: <Moon className="w-3 h-3" />,
};

export function RecoveryModule({ athleteId }: RecoveryModuleProps) {
  const [suggestion, setSuggestion] = useState<RecoverySuggestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exercises, setExercises] = useState<RecoveryExercise[]>([]);
  const [message, setMessage] = useState('');

  const fetchRecovery = async () => {
    if (!athleteId) return;
    setLoading(true);
    setMessage('');
    try {
      const data = await getTodayRecovery(athleteId);
      setSuggestion(data);
      setExercises(data.exercises?.map((e: any) => ({ ...e, completed: e.completed || false })) || []);
    } catch (err: any) {
      setMessage(err.message || '暂无恢复建议');
      setSuggestion(null);
      setExercises([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecovery();
  }, [athleteId]);

  const toggleExercise = (index: number) => {
    setExercises(prev => prev.map((e, i) => i === index ? { ...e, completed: !e.completed } : e));
  };

  const handleCompleteAll = async () => {
    if (!suggestion) return;
    try {
      await completeSuggestion(suggestion.id);
      setMessage('恢复训练已标记完成 ✓');
      setSuggestion(prev => prev ? { ...prev, status: 'completed' } : null);
    } catch {
      setMessage('操作失败');
    }
  };

  if (!athleteId) {
    return (
      <div className="p-3 text-center text-xs text-slate-400">
        请先选择运动员
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h5 className="text-xs font-semibold text-slate-600 flex items-center gap-1">
          <Heart className="w-3 h-3 text-red-400" /> 今日恢复指南
        </h5>
        <button
          onClick={fetchRecovery}
          disabled={loading}
          className="p-1 rounded hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">
          <div className="skeleton h-3 w-full" />
          <div className="skeleton h-3 w-3/4" />
          <div className="skeleton h-8 w-full" />
        </div>
      ) : suggestion ? (
        <div className="space-y-2">
          {suggestion.status === 'completed' && (
            <div className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
              <CheckCircle2 className="w-3 h-3" /> 今日已完成
            </div>
          )}

          {/* Exercise list */}
          {exercises.length > 0 && (
            <div className="space-y-1">
              {exercises.map((ex, i) => (
                <label
                  key={i}
                  className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                    ex.completed ? 'bg-green-50 border border-green-100' : 'bg-slate-50 border border-slate-100 hover:bg-slate-100'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={ex.completed || false}
                    onChange={() => toggleExercise(i)}
                    className="mt-0.5 rounded border-slate-300 text-green-500 focus:ring-green-500 shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1">
                      <span className="text-[10px]">
                        {CATEGORY_ICONS[ex.category || 'recovery'] || null}
                      </span>
                      <p className={`text-xs font-medium ${ex.completed ? 'text-green-600 line-through' : 'text-slate-700'}`}>
                        {ex.name}
                      </p>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">
                      {ex.sets && ex.reps ? `${ex.sets}组 × ${ex.reps}次` : ''}
                      {ex.duration_min ? ` · ${ex.duration_min}分钟` : ''}
                    </p>
                    {ex.notes && (
                      <p className="text-[10px] text-slate-400 mt-0.5">{ex.notes}</p>
                    )}
                  </div>
                </label>
              ))}
            </div>
          )}

          {/* Complete button */}
          {suggestion.status !== 'completed' && (
            <button
              onClick={handleCompleteAll}
              className="w-full py-1.5 bg-green-500 text-white rounded-lg text-[11px] font-medium hover:bg-green-600 transition-colors flex items-center justify-center gap-1"
            >
              <CheckCircle2 className="w-3 h-3" /> 标记完成
            </button>
          )}

          {message && (
            <p className={`text-[10px] text-center ${message.includes('✓') ? 'text-green-500' : 'text-red-400'}`}>
              {message}
            </p>
          )}
        </div>
      ) : (
        <p className="text-xs text-slate-400 text-center py-3">
          {message || '暂无恢复建议，请先录入今日身体数据'}
        </p>
      )}
    </div>
  );
}
