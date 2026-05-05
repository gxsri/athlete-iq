import React, { useState, useEffect } from 'react';
import { Save, X, Zap, Battery, Activity, Camera, BarChart3 } from 'lucide-react';
import { createOrUpdateLog, getDailyMetrics, DailyMetricFull } from '../services/api';

interface TrainingLogFormProps {
  athleteId: string;
  date: string;
  onClose: () => void;
  onSaved: () => void;
}

const MUSCLE_GROUPS = [
  { key: 'shoulder', label: '肩部' },
  { key: 'quad', label: '股四' },
  { key: 'calf', label: '小腿' },
  { key: 'back', label: '背部' },
  { key: 'core', label: '核心' },
  { key: 'hip', label: '髋部' },
];

export function TrainingLogForm({ athleteId, date, onClose, onSaved }: TrainingLogFormProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  // Form state
  const [rpe, setRpe] = useState(6);
  const [energyLevel, setEnergyLevel] = useState(7);
  const [trainingLoad, setTrainingLoad] = useState(50);
  const [fatigue, setFatigue] = useState(30);
  const [sleepQuality, setSleepQuality] = useState(5.5);
  const [soreness, setSoreness] = useState<Record<string, number>>({
    shoulder: 2, quad: 2, calf: 2, back: 2, core: 2, hip: 2,
  });
  const [technicalNotes, setTechnicalNotes] = useState('');
  const [trainingContent, setTrainingContent] = useState('');
  const [notes, setNotes] = useState('');
  const [completionRate, setCompletionRate] = useState(100);

  // Load existing data
  useEffect(() => {
    if (!athleteId || !date) return;
    setLoading(true);
    getDailyMetrics(athleteId, date)
      .then((data: DailyMetricFull | null) => {
        if (data) {
          setRpe(data.rpe || 6);
          setEnergyLevel(data.energy_level || 7);
          setTrainingLoad(data.training_load || 50);
          setFatigue(data.fatigue || 30);
          setSleepQuality(data.sleep_quality || 5.5);
          if (data.muscle_soreness && typeof data.muscle_soreness === 'object') {
            setSoreness(prev => ({ ...prev, ...data.muscle_soreness }));
          }
          setTechnicalNotes(data.technical_notes || '');
          setTrainingContent(data.training_content || '');
          setNotes(data.notes || '');
          setCompletionRate(data.completion_rate || 100);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [athleteId, date]);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await createOrUpdateLog(athleteId, {
        metric_date: date,
        rpe, energy_level: energyLevel,
        training_load: trainingLoad, fatigue,
        sleep_quality: sleepQuality,
        muscle_soreness: soreness,
        technical_notes: technicalNotes,
        training_content: trainingContent,
        notes, completion_rate: completionRate,
      });
      setMessage('保存成功 ✓');
      setTimeout(() => onSaved(), 500);
    } catch (err: any) {
      setMessage(err.message || '保存失败');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4"><div className="skeleton h-64 w-full" /></div>;

  return (
    <div className="p-4 space-y-4 max-h-[80vh] overflow-y-auto">
      <div className="flex items-center justify-between sticky top-0 bg-white pb-2 border-b">
        <h4 className="text-sm font-bold text-slate-800">训练日志 — {date}</h4>
        <button onClick={onClose} className="p-1 rounded hover:bg-slate-100"><X className="w-4 h-4 text-slate-400" /></button>
      </div>

      {/* RPE + Energy + Load */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-500 flex items-center gap-1">
            <Zap className="w-3 h-3" /> RPE ({rpe}/10)
          </label>
          <input type="range" value={rpe} onChange={e => setRpe(Number(e.target.value))} min={1} max={10} className="w-full" />
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>1 极轻</span><span>10 极限</span></div>
        </div>
        <div>
          <label className="text-xs text-slate-500 flex items-center gap-1">
            <Battery className="w-3 h-3" /> 精力 ({energyLevel}/10)
          </label>
          <input type="range" value={energyLevel} onChange={e => setEnergyLevel(Number(e.target.value))} min={1} max={10} className="w-full" />
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>1 耗竭</span><span>10 充沛</span></div>
        </div>
      </div>

      {/* Load + Fatigue */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-500">训练负荷 ({trainingLoad})</label>
          <input type="range" value={trainingLoad} onChange={e => setTrainingLoad(Number(e.target.value))} min={0} max={100} className="w-full" />
        </div>
        <div>
          <label className="text-xs text-slate-500">疲劳度 ({fatigue})</label>
          <input type="range" value={fatigue} onChange={e => setFatigue(Number(e.target.value))} min={0} max={100} className="w-full" />
        </div>
      </div>

      {/* Muscle Soreness */}
      <div>
        <label className="text-xs text-slate-500 flex items-center gap-1 mb-1">
          <Activity className="w-3 h-3" /> 肌肉酸痛
        </label>
        <div className="grid grid-cols-3 gap-2">
          {MUSCLE_GROUPS.map(g => (
            <div key={g.key} className="flex items-center gap-2 p-1.5 rounded bg-slate-50">
              <span className="text-[10px] text-slate-500 w-8">{g.label}</span>
              <input
                type="range" value={soreness[g.key] || 0}
                onChange={e => setSoreness(prev => ({ ...prev, [g.key]: Number(e.target.value) }))}
                min={0} max={10} className="w-full h-1"
              />
              <span className="text-[10px] font-mono w-5 text-right">{soreness[g.key] || 0}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sleep Quality */}
      <div>
        <label className="text-xs text-slate-500">睡眠质量 ({sleepQuality}/7)</label>
        <input type="range" value={sleepQuality} onChange={e => setSleepQuality(Number(e.target.value))} min={1} max={7} step={0.5} className="w-full" />
      </div>

      {/* Training Content */}
      <div>
        <label className="text-xs text-slate-500">训练内容</label>
        <textarea value={trainingContent} onChange={e => setTrainingContent(e.target.value)}
          rows={2} className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="今天训练了哪些内容？" />
      </div>

      {/* Technical Notes */}
      <div>
        <label className="text-xs text-slate-500">技术备注</label>
        <textarea value={technicalNotes} onChange={e => setTechnicalNotes(e.target.value)}
          rows={2} className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="技术动作质量、需要改进的地方..." />
      </div>

      {/* Completion Rate */}
      <div>
        <label className="text-xs text-slate-500 flex items-center gap-1">
          <BarChart3 className="w-3 h-3" /> 完成率 ({completionRate}%)
        </label>
        <input type="range" value={completionRate} onChange={e => setCompletionRate(Number(e.target.value))} min={0} max={150} className="w-full" />
      </div>

      {/* Notes */}
      <div>
        <label className="text-xs text-slate-500">备注</label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)}
          rows={1} className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs resize-none focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      {/* Media Upload Placeholder */}
      <div>
        <label className="text-xs text-slate-500 flex items-center gap-1 mb-1">
          <Camera className="w-3 h-3" /> 图片/视频
        </label>
        <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 text-center">
          <p className="text-xs text-slate-400">拖拽文件到此处上传（功能开发中）</p>
        </div>
      </div>

      {/* Save */}
      <button onClick={handleSave} disabled={saving}
        className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50 flex items-center justify-center gap-1">
        <Save className="w-3.5 h-3.5" /> {saving ? '保存中...' : '保存日志'}
      </button>

      {message && <p className={`text-xs text-center ${message.includes('✓') ? 'text-green-500' : 'text-red-400'}`}>{message}</p>}
    </div>
  );
}
