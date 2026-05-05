import React, { useState } from 'react';
import { Trash2, ChevronUp, ChevronDown, GripVertical } from 'lucide-react';

export interface ExerciseData {
  id?: string;
  exerciseId?: string;
  name: string;
  weight: number;
  reps: number;
  sets: number;
  rpe: number;
  rest?: number;
  notes?: string;
}

interface ExerciseCardProps {
  exercise: ExerciseData;
  planned?: ExerciseData;
  onChange?: (field: string, value: number | string) => void;
  onRemove?: () => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  index?: number;
}

export function ExerciseCard({ exercise, planned, onChange, onRemove, onMoveUp, onMoveDown, index }: ExerciseCardProps) {
  const [notes, setNotes] = useState(exercise.notes || '');

  const showPlanned = !!planned;

  return (
    <div className="p-3 rounded-lg bg-white border border-slate-200 hover:border-blue-200 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <GripVertical className="w-4 h-4 text-slate-300 cursor-grab" />
          <span className="text-sm font-semibold text-slate-700">{exercise.name}</span>
          {index !== undefined && (
            <span className="text-xs text-slate-400">#{index + 1}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {onMoveUp && (
            <button onClick={onMoveUp} className="p-1 rounded hover:bg-slate-100">
              <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
            </button>
          )}
          {onMoveDown && (
            <button onClick={onMoveDown} className="p-1 rounded hover:bg-slate-100">
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>
          )}
          {onRemove && (
            <button onClick={onRemove} className="p-1 rounded hover:bg-red-50">
              <Trash2 className="w-3.5 h-3.5 text-red-400" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-2">
        <Field label="重量(kg)" value={exercise.weight} field="weight" onChange={onChange} />
        <Field label="次数" value={exercise.reps} field="reps" onChange={onChange} />
        <Field label="组数" value={exercise.sets} field="sets" onChange={onChange} />
        <Field label="间歇(s)" value={exercise.rest || 60} field="rest" onChange={onChange} />
        <Field label="RPE" value={exercise.rpe} field="rpe" onChange={onChange} min={1} max={10} />
      </div>

      {showPlanned && (
        <div className="mt-2 grid grid-cols-5 gap-2 text-xs">
          <CompareValue label="计划重量" planned={planned.weight} actual={exercise.weight} unit="kg" />
          <CompareValue label="计划次数" planned={planned.reps} actual={exercise.reps} />
          <CompareValue label="计划组数" planned={planned.sets} actual={exercise.sets} />
          <CompareValue label="计划间歇" planned={planned.rest || 60} actual={exercise.rest || 60} unit="s" />
          <CompareValue label="计划RPE" planned={planned.rpe} actual={exercise.rpe} />
        </div>
      )}

      <div className="mt-2">
        <input
          type="text"
          placeholder="备注..."
          value={notes}
          onChange={e => { setNotes(e.target.value); onChange?.('notes', e.target.value); }}
          className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 text-slate-600"
        />
      </div>
    </div>
  );
}

function Field({ label, value, field, onChange, min = 0, max = 999 }: {
  label: string; value: number; field: string;
  onChange?: (field: string, value: number) => void; min?: number; max?: number;
}) {
  return (
    <div>
      <label className="block text-xs text-slate-400 mb-0.5">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={e => onChange?.(field, Number(e.target.value))}
        className="w-full px-2 py-1 text-sm border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 text-center"
      />
    </div>
  );
}

function CompareValue({ label, planned, actual, unit }: {
  label: string; planned: number; actual: number; unit?: string;
}) {
  const diff = actual - planned;
  const isOver = diff > 0;
  const isUnder = diff < 0;
  return (
    <div className="text-center">
      <div className="text-slate-400 mb-0.5">{label}</div>
      <div className={`font-mono font-bold ${isOver ? 'text-red-500' : isUnder ? 'text-blue-500' : 'text-green-500'}`}>
        {isOver ? '+' : ''}{diff}{unit || ''}
      </div>
    </div>
  );
}
