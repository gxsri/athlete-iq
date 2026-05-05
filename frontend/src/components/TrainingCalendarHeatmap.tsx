import React, { useState, useEffect, useMemo } from 'react';
import { getTrainingLogs, TrainingLog } from '../services/api';

interface TrainingCalendarHeatmapProps {
  athleteId: string;
  weeks?: number;
  onDayClick?: (date: string, load: number) => void;
}

const LOAD_COLORS = [
  { max: 0, color: '#e5e5ea', label: '休息' },
  { max: 200, color: '#d1f2d9', label: '低负荷' },
  { max: 400, color: '#34c759', label: '中等' },
  { max: 650, color: '#ff9500', label: '较高' },
  { max: 900, color: '#ff7b00', label: '高负荷' },
  { max: Infinity, color: '#ff3b30', label: '极高' },
];

function getLoadColor(load: number): string {
  for (const level of LOAD_COLORS) {
    if (load <= level.max) return level.color;
  }
  return LOAD_COLORS[LOAD_COLORS.length - 1].color;
}

const DAY_LABELS = ['一', '二', '三', '四', '五', '六', '日'];

export function TrainingCalendarHeatmap({
  athleteId,
  weeks = 12,
  onDayClick,
}: TrainingCalendarHeatmapProps) {
  const [logs, setLogs] = useState<TrainingLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredCell, setHoveredCell] = useState<{ date: string; load: number; x: number; y: number } | null>(null);

  useEffect(() => {
    if (!athleteId) return;
    setLoading(true);
    getTrainingLogs(athleteId, weeks * 7 + 7)
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false));
  }, [athleteId, weeks]);

  const { grid, monthLabels } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const endDate = new Date(today);
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - (weeks * 7 - 1));

    // Align start to Monday
    const startDay = startDate.getDay();
    const offset = startDay === 0 ? 6 : startDay - 1;
    startDate.setDate(startDate.getDate() - offset);

    // Align end to Sunday
    const endDay = endDate.getDay();
    const endOffset = endDay === 0 ? 0 : 7 - endDay;
    endDate.setDate(endDate.getDate() + endOffset);

    const totalDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const totalWeeks = Math.ceil(totalDays / 7);

    // Build load map
    const loadMap: Record<string, number> = {};
    for (const log of logs) {
      loadMap[log.training_date] = (loadMap[log.training_date] || 0) + (log.session_load || 0);
    }

    // Build grid: weeks x 7
    const grid: { date: string; load: number; isFuture: boolean }[][] = [];
    const monthLabels: { week: number; label: string }[] = [];
    let lastMonth = -1;

    for (let w = 0; w < totalWeeks; w++) {
      const week: { date: string; load: number; isFuture: boolean }[] = [];
      for (let d = 0; d < 7; d++) {
        const date = new Date(startDate);
        date.setDate(date.getDate() + w * 7 + d);
        const dateStr = date.toISOString().split('T')[0];
        const isFuture = date > today;
        week.push({
          date: dateStr,
          load: isFuture ? 0 : (loadMap[dateStr] || 0),
          isFuture,
        });

        if (d === 0) {
          const month = date.getMonth();
          if (month !== lastMonth) {
            monthLabels.push({ week: w, label: `${date.getMonth() + 1}月` });
            lastMonth = month;
          }
        }
      }
      grid.push(week);
    }

    return { grid, monthLabels };
  }, [logs, weeks]);

  if (loading) {
    return (
      <div className="card space-y-3">
        <div className="skeleton h-4 w-32" />
        <div className="grid grid-cols-13 gap-1">
          {Array.from({ length: weeks * 7 }).map((_, i) => (
            <div key={i} className="skeleton h-4 w-4 rounded-sm" />
          ))}
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="card">
        <h4 className="text-sm font-semibold text-slate-700 mb-3">训练热力图</h4>
        <p className="text-xs text-slate-400 text-center py-6">暂无训练数据</p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700">训练热力图 — 最近 {weeks} 周</h4>
        <div className="flex items-center gap-1">
          {LOAD_COLORS.map((level) => (
            <div key={level.label} className="flex items-center gap-0.5 text-[10px] text-slate-400">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: level.color }}
                title={level.label}
              />
              {level.label === '休息' && <span>{level.label}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Month header row */}
      <div className="flex gap-[2px]">
        <div className="w-5 shrink-0" />
        <div className="flex-1 flex gap-[2px] relative" style={{ height: 18 }}>
          {monthLabels.map((ml, i) => {
            const left = (ml.week / (grid.length || 1)) * 100;
            return (
              <span
                key={i}
                className="absolute text-[10px] text-slate-400 font-medium"
                style={{ left: `${left}%` }}
              >
                {ml.label}
              </span>
            );
          })}
        </div>
      </div>

      <div className="flex gap-[2px]">
        {/* Day labels */}
        <div className="flex flex-col gap-[2px] shrink-0">
          {DAY_LABELS.map((day) => (
            <div
              key={day}
              className="h-[13px] w-5 flex items-center justify-end pr-1 text-[9px] text-slate-400"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="flex-1 flex gap-[2px]">
          {grid.map((week, wi) => (
            <div key={wi} className="flex-1 flex flex-col gap-[2px]">
              {week.map((cell, di) => (
                <div
                  key={`${wi}-${di}`}
                  className="aspect-square rounded-[2px] cursor-pointer hover:ring-2 hover:ring-blue-400 hover:scale-125 transition-transform relative"
                  style={{
                    backgroundColor: cell.isFuture ? 'transparent' : getLoadColor(cell.load),
                    border: cell.isFuture ? '1px dashed #e5e5ea' : 'none',
                  }}
                  onClick={() => !cell.isFuture && onDayClick?.(cell.date, cell.load)}
                  onMouseEnter={(e) => {
                    if (!cell.isFuture) {
                      const rect = (e.target as HTMLElement).getBoundingClientRect();
                      setHoveredCell({ date: cell.date, load: cell.load, x: rect.left, y: rect.top });
                    }
                  }}
                  onMouseLeave={() => setHoveredCell(null)}
                  title={`${cell.date}: ${cell.load.toFixed(0)} 负荷`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div
          className="fixed z-50 px-2 py-1 rounded-lg bg-slate-800 text-white text-[11px] shadow-lg pointer-events-none"
          style={{
            left: hoveredCell.x,
            top: hoveredCell.y - 32,
          }}
        >
          {hoveredCell.date} · {hoveredCell.load.toFixed(0)} 负荷
        </div>
      )}
    </div>
  );
}
