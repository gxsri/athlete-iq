import React, { useState } from 'react';
import { Brain, TrendingUp, AlertTriangle, Smile, Target, Zap, BatteryLow } from 'lucide-react';

interface MentalData {
  mood?: number;
  focus?: number;
  motivation?: number;
  mental_fatigue?: number;
  notes?: string;
}

interface MentalCardProps {
  mentalData: MentalData;
  athleteName: string;
  onSubmit: (data: MentalData) => void | Promise<void>;
  weeklyTrend?: {
    mood_avg: number;
    focus_avg: number;
    motivation_avg: number;
    fatigue_avg: number;
  };
}

export function MentalCard({ mentalData, athleteName, onSubmit, weeklyTrend }: MentalCardProps) {
  const [mood, setMood] = useState(mentalData.mood ?? 3);
  const [focus, setFocus] = useState(mentalData.focus ?? 3);
  const [motivation, setMotivation] = useState(mentalData.motivation ?? 3);
  const [mentalFatigue, setMentalFatigue] = useState(mentalData.mental_fatigue ?? 2);
  const [notes, setNotes] = useState(mentalData.notes ?? '');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fatigueWarning = mentalFatigue >= 4;

  const handleSubmit = async () => {
    setMessage('');
    setError('');
    try {
      await onSubmit({
        mood,
        focus,
        motivation,
        mental_fatigue: mentalFatigue,
        notes: notes || undefined,
      });
      setMessage('心理日志已提交');
    } catch (err: any) {
      setError(err.message || '提交失败');
    }
  };

  const sliders = [
    { label: '情绪状态', value: mood, setter: setMood, icon: Smile, desc: ['1 极差', '5 极佳'], color: 'bg-purple-500' },
    { label: '注意力', value: focus, setter: setFocus, icon: Target, desc: ['1 极分散', '5 极度专注'], color: 'bg-blue-500' },
    { label: '动力', value: motivation, setter: setMotivation, icon: Zap, desc: ['1 无动力', '5 动力十足'], color: 'bg-amber-500' },
    { label: '心理疲劳', value: mentalFatigue, setter: setMentalFatigue, icon: BatteryLow, desc: ['1 精力充沛', '5 极度疲惫'], color: 'bg-red-500' },
  ];

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <Brain className="w-4 h-4" /> 心理监测 - {athleteName}
        </h4>
      </div>

      {/* Fatigue Warning */}
      {fatigueWarning && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-700">心理疲劳预警</p>
            <p className="text-xs text-red-600 mt-0.5">
              当前心理疲劳评分 {mentalFatigue}/5，建议减少训练量、增加心理恢复干预。
            </p>
          </div>
        </div>
      )}

      {/* Weekly Trend Summary */}
      {weeklyTrend && (
        <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-100">
          <p className="text-xs font-medium text-indigo-700 flex items-center gap-1 mb-2">
            <TrendingUp className="w-3.5 h-3.5" /> 本周趋势
          </p>
          <div className="grid grid-cols-4 gap-2">
            <div className="text-center">
              <div className="text-lg font-bold text-indigo-600">{weeklyTrend.mood_avg.toFixed(1)}</div>
              <div className="text-xs text-indigo-400">情绪</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{weeklyTrend.focus_avg.toFixed(1)}</div>
              <div className="text-xs text-blue-400">注意力</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-amber-600">{weeklyTrend.motivation_avg.toFixed(1)}</div>
              <div className="text-xs text-amber-400">动力</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-red-600">{weeklyTrend.fatigue_avg.toFixed(1)}</div>
              <div className="text-xs text-red-400">疲劳</div>
            </div>
          </div>
        </div>
      )}

      {/* Sliders */}
      <div className="space-y-3">
        {sliders.map(s => (
          <div key={s.label}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-500 flex items-center gap-1">
                <s.icon className="w-3 h-3" />
                {s.label} ({s.value}/5)
              </span>
              <span className="font-mono text-slate-600">{s.value}</span>
            </div>
            <input
              type="range"
              value={s.value}
              onChange={e => s.setter(Number(e.target.value))}
              min={1}
              max={5}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>{s.desc[0]}</span><span>{s.desc[1]}</span>
            </div>
          </div>
        ))}
      </div>

      <div>
        <label className="block text-xs text-slate-500 mb-1">备注</label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          placeholder="心理状态补充说明..."
        />
      </div>

      <button
        onClick={handleSubmit}
        className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
      >
        提交心理记录
      </button>

      {message && <p className="text-xs text-green-600 bg-green-50 p-2 rounded">{message}</p>}
      {error && <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{error}</p>}
    </div>
  );
}
