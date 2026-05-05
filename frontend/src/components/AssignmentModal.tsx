import React, { useState, useEffect } from 'react';
import { X, ClipboardList, Target, Zap } from 'lucide-react';
import { getTrainingTemplates, createAssignment, TrainingTemplate } from '../services/api';

interface AssignmentModalProps {
  athleteId: string;
  date: string;
  onClose: () => void;
  onAssigned: () => void;
}

export function AssignmentModal({ athleteId, date, onClose, onAssigned }: AssignmentModalProps) {
  const [templates, setTemplates] = useState<TrainingTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState('');
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const selectedTpl = templates.find(t => t.id === selectedId);

  useEffect(() => {
    getTrainingTemplates()
      .then(setTemplates)
      .catch(() => setTemplates([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedTpl?.content) {
      setOverrides({
        target_load: selectedTpl.content.target_load || 50,
        target_rpe: selectedTpl.content.target_rpe || 6,
      });
    }
  }, [selectedId]);

  const handleAssign = async () => {
    if (!selectedId) return;
    setSaving(true);
    setMessage('');
    try {
      await createAssignment({
        athlete_id: athleteId,
        template_id: selectedId,
        scheduled_date: date,
        overrides,
        notes: notes || undefined,
      });
      setMessage('计划已分配 ✓');
      setTimeout(() => onAssigned(), 500);
    } catch (err: any) {
      setMessage(err.message || '分配失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 space-y-4 max-w-md">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1">
          <ClipboardList className="w-4 h-4" /> 分配计划 — {date}
        </h4>
        <button onClick={onClose} className="p-1 rounded hover:bg-slate-100"><X className="w-4 h-4 text-slate-400" /></button>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1,2,3].map(i => <div key={i} className="skeleton h-14 w-full" />)}
        </div>
      ) : templates.length === 0 ? (
        <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">暂无可用模板</p>
      ) : (
        <>
          <div className="space-y-1.5 max-h-64 overflow-y-auto">
            {templates.map(tpl => (
              <div
                key={tpl.id}
                onClick={() => setSelectedId(tpl.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedId === tpl.id
                    ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/30'
                    : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{tpl.name}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${
                    tpl.intensity_zone === '高' ? 'bg-red-50 text-red-600' :
                    tpl.intensity_zone === '中' ? 'bg-amber-50 text-amber-600' :
                    'bg-green-50 text-green-600'
                  }`}>
                    {tpl.intensity_zone}强度
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  {tpl.content?.target_load && (
                    <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                      <Target className="w-2.5 h-2.5" /> 负荷 {tpl.content.target_load}
                    </span>
                  )}
                  {tpl.content?.target_rpe && (
                    <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                      <Zap className="w-2.5 h-2.5" /> RPE {tpl.content.target_rpe}
                    </span>
                  )}
                </div>
                {tpl.description && (
                  <p className="text-[10px] text-slate-400 mt-1">{tpl.description}</p>
                )}
                {tpl.target_focus && tpl.target_focus.length > 0 && (
                  <div className="flex gap-1 mt-1">
                    {tpl.target_focus.map(f => (
                      <span key={f} className="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{f}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Override controls */}
          {selectedTpl && (
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 space-y-2">
              <p className="text-xs font-medium text-slate-600 dark:text-slate-300">微调参数</p>
              <div>
                <label className="text-[10px] text-slate-500">目标负荷</label>
                <input type="range" value={overrides.target_load || 50}
                  onChange={e => setOverrides(prev => ({ ...prev, target_load: Number(e.target.value) }))}
                  min={0} max={100} className="w-full" />
                <span className="text-xs font-mono">{overrides.target_load}</span>
              </div>
              <div>
                <label className="text-[10px] text-slate-500">目标 RPE</label>
                <input type="range" value={overrides.target_rpe || 6}
                  onChange={e => setOverrides(prev => ({ ...prev, target_rpe: Number(e.target.value) }))}
                  min={1} max={10} className="w-full" />
                <span className="text-xs font-mono">{overrides.target_rpe}</span>
              </div>
              <div>
                <label className="text-[10px] text-slate-500">备注</label>
                <input type="text" value={notes} onChange={e => setNotes(e.target.value)}
                  className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs"
                  placeholder="教练备注..." />
              </div>
            </div>
          )}

          <button onClick={handleAssign} disabled={!selectedId || saving}
            className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50">
            {saving ? '分配中...' : '分配计划'}
          </button>

          {message && <p className={`text-xs text-center ${message.includes('✓') ? 'text-green-500' : 'text-red-400'}`}>{message}</p>}
        </>
      )}
    </div>
  );
}
