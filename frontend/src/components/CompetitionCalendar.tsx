import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft, ChevronRight, Trophy, Plus, X, Calendar, Target, Zap,
  AlertTriangle, Moon, Edit3, Save, Trash2, TrendingUp, ClipboardList, PenLine,
} from 'lucide-react';
import {
  getMonthlyRisks, getCompetitions, createCompetition, deleteCompetition,
  getDailyMetrics, updateDailyMetrics, getCompetitionRecommendation,
  getCalendarAssignments,
  MonthlyRisk, Competition, DailyMetricResponse, CompetitionRecommendation, TrainingAssignment,
} from '../services/api';
import { TrainingLogForm } from './TrainingLogForm';
import { AssignmentModal } from './AssignmentModal';

interface CompetitionCalendarProps {
  athleteId: string;
}

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日'];

function riskToColor(risk: number): string {
  // 0 → green (0,255,0), 100 → red (255,0,0), linear interpolation
  const r = Math.round((risk / 100) * 255);
  const g = Math.round((1 - risk / 100) * 255);
  return `rgb(${r},${g},0)`;
}

function getRiskBg(risk: number): string {
  if (risk === 0) return 'bg-slate-50';
  if (risk < 20) return 'bg-green-100';
  if (risk < 40) return 'bg-lime-100';
  if (risk < 60) return 'bg-yellow-100';
  if (risk < 80) return 'bg-orange-100';
  return 'bg-red-100';
}

const PHASE_COLORS: Record<string, string> = {
  '基础期': 'bg-blue-50 border-blue-200 text-blue-700',
  '强化期': 'bg-orange-50 border-orange-200 text-orange-700',
  '模拟期': 'bg-purple-50 border-purple-200 text-purple-700',
  '减量期': 'bg-amber-50 border-amber-200 text-amber-700',
  '调整期': 'bg-sky-50 border-sky-200 text-sky-700',
  '比赛日': 'bg-red-50 border-red-200 text-red-700',
};

export function CompetitionCalendar({ athleteId }: CompetitionCalendarProps) {
  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth() + 1);
  const [risks, setRisks] = useState<MonthlyRisk[]>([]);
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(false);

  // Selected day
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [dayMetrics, setDayMetrics] = useState<DailyMetricResponse | null>(null);
  const [dayLoading, setDayLoading] = useState(false);

  // Edit mode for selected day
  const [editing, setEditing] = useState(false);
  const [editLoad, setEditLoad] = useState(0);
  const [editContent, setEditContent] = useState('');
  const [editNotes, setEditNotes] = useState('');

  // Add competition modal
  const [showCompModal, setShowCompModal] = useState(false);
  const [compName, setCompName] = useState('');
  const [compDate, setCompDate] = useState('');
  const [compLocation, setCompLocation] = useState('');

  // Competition recommendation
  const [selectedComp, setSelectedComp] = useState<Competition | null>(null);
  const [recommendation, setRecommendation] = useState<CompetitionRecommendation | null>(null);
  const [recLoading, setRecLoading] = useState(false);

  // Training log + assignment modals
  const [showLogForm, setShowLogForm] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [logFormDate, setLogFormDate] = useState('');

  // Assignments for plan indicators
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);

  // Fetch data
  const fetchMonthData = useCallback(async () => {
    if (!athleteId) return;
    setLoading(true);
    try {
      const monthStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}`;
      const [riskData, compData, assignData] = await Promise.all([
        getMonthlyRisks(athleteId, currentYear, currentMonth),
        getCompetitions(athleteId),
        getCalendarAssignments(athleteId, monthStr),
      ]);
      setRisks(riskData);
      setCompetitions(compData);
      setAssignments(assignData);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [athleteId, currentYear, currentMonth]);

  useEffect(() => {
    fetchMonthData();
  }, [fetchMonthData]);

  // Navigation
  const prevMonth = () => {
    if (currentMonth === 1) { setCurrentMonth(12); setCurrentYear(y => y - 1); }
    else setCurrentMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (currentMonth === 12) { setCurrentMonth(1); setCurrentYear(y => y + 1); }
    else setCurrentMonth(m => m + 1);
  };

  // Click day → fetch details
  const handleDayClick = async (dateStr: string) => {
    setSelectedDate(dateStr);
    setEditing(false);
    setDayLoading(true);
    setSelectedComp(null);
    setRecommendation(null);
    try {
      const metrics = await getDailyMetrics(athleteId, dateStr);
      setDayMetrics(metrics);
      if (metrics) {
        setEditLoad(metrics.training_load);
        setEditContent(metrics.training_content || '');
        setEditNotes(metrics.notes || '');
      }
    } catch { setDayMetrics(null); }
    finally { setDayLoading(false); }
  };

  // Save day edits
  const handleSaveDay = async () => {
    if (!selectedDate) return;
    try {
      const updated = await updateDailyMetrics(athleteId, selectedDate, {
        training_load: editLoad,
        training_content: editContent,
        notes: editNotes,
      });
      setDayMetrics(updated);
      setEditing(false);
      fetchMonthData();
    } catch { /* ignore */ }
  };

  // Add competition
  const handleAddCompetition = async () => {
    if (!compName || !compDate) return;
    try {
      await createCompetition(athleteId, {
        name: compName,
        competition_date: compDate,
        location: compLocation || undefined,
      });
      setShowCompModal(false);
      setCompName('');
      setCompDate('');
      setCompLocation('');
      fetchMonthData();
    } catch { /* ignore */ }
  };

  // Delete competition
  const handleDeleteComp = async (compId: string) => {
    try {
      await deleteCompetition(athleteId, compId);
      if (selectedComp?.id === compId) {
        setSelectedComp(null);
        setRecommendation(null);
      }
      fetchMonthData();
    } catch { /* ignore */ }
  };

  // Get recommendation for a competition
  const handleCompClick = async (comp: Competition) => {
    setSelectedComp(comp);
    setRecLoading(true);
    try {
      const rec = await getCompetitionRecommendation(athleteId, comp.id);
      setRecommendation(rec);
    } catch { setRecommendation(null); }
    finally { setRecLoading(false); }
  };

  // Calendar grid computation
  const firstDay = new Date(currentYear, currentMonth - 1, 1);
  const lastDay = new Date(currentYear, currentMonth, 0);
  const startDayOfWeek = firstDay.getDay(); // 0=Sun
  const leadingEmpty = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1; // Make Monday first
  const totalDays = lastDay.getDate();
  const totalCells = leadingEmpty + totalDays;
  const rows = Math.ceil(totalCells / 7);

  // Build risk map
  const riskMap: Record<string, MonthlyRisk> = {};
  for (const r of risks) {
    riskMap[r.date] = r;
  }

  // Competition dates set
  const compDates = new Set(competitions.map(c => c.competition_date));

  // Assignment dates set
  const assignDates = new Set(assignments.map(a => a.scheduled_date));
  const assignMap: Record<string, TrainingAssignment> = {};
  for (const a of assignments) assignMap[a.scheduled_date] = a;

  return (
    <div className="space-y-4">
      {/* Month Navigation */}
      <div className="flex items-center justify-between">
        <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
          <ChevronLeft className="w-4 h-4 text-slate-500" />
        </button>
        <h4 className="text-sm font-semibold text-slate-700">
          {currentYear}年 {currentMonth}月
        </h4>
        <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
          <ChevronRight className="w-4 h-4 text-slate-500" />
        </button>
      </div>

      {/* Calendar Grid */}
      {loading ? (
        <div className="space-y-1">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton h-10 w-full" />)}
        </div>
      ) : (
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 bg-slate-50 border-b border-slate-200">
            {WEEKDAYS.map(d => (
              <div key={d} className="text-center py-1.5 text-[11px] font-medium text-slate-400">
                {d}
              </div>
            ))}
          </div>
          {/* Day cells */}
          <div className="grid grid-cols-7">
            {Array.from({ length: rows * 7 }, (_, i) => {
              const dayNum = i - leadingEmpty + 1;
              const isValid = dayNum >= 1 && dayNum <= totalDays;
              const dateStr = isValid
                ? `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`
                : '';
              const risk = isValid ? (riskMap[dateStr]?.injury_risk || 0) : 0;
              const hasComp = isValid && compDates.has(dateStr);
              const hasPlan = isValid && assignDates.has(dateStr);
              const isToday = dateStr === today.toISOString().split('T')[0];
              const isSelected = dateStr === selectedDate;

              return (
                <div
                  key={i}
                  onClick={() => isValid && handleDayClick(dateStr)}
                  onDoubleClick={() => {
                    if (isValid) { setLogFormDate(dateStr); setShowLogForm(true); }
                  }}
                  className={`
                    relative h-11 border-b border-r border-slate-100 flex flex-col items-center justify-center
                    ${isValid ? 'cursor-pointer hover:ring-2 hover:ring-blue-400 hover:z-10 transition-all' : 'bg-slate-50/50'}
                    ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50 z-10' : ''}
                    ${isToday && !isSelected ? 'ring-1 ring-blue-300' : ''}
                  `}
                  style={isValid && risk > 0 ? { backgroundColor: riskToColor(risk) + '30' } : {}}
                >
                  {isValid && (
                    <>
                      <span className={`text-xs font-medium ${isToday ? 'text-blue-600 font-bold' : 'text-slate-700'}`}>
                        {dayNum}
                      </span>
                      <div className="flex items-center gap-0.5 absolute top-0.5 right-0.5">
                        {hasComp && <Trophy className="w-2.5 h-2.5 text-amber-500" />}
                        {hasPlan && <ClipboardList className="w-2.5 h-2.5 text-blue-500" />}
                      </div>
                      {risk > 0 && (
                        <div
                          className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                          style={{ backgroundColor: riskToColor(risk) }}
                        />
                      )}
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Color Legend */}
      <div className="flex items-center gap-3 text-[10px] text-slate-400 flex-wrap">
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-green-400" /> 低风险</div>
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-yellow-400" /> 中等</div>
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-red-400" /> 高风险</div>
        <div className="flex items-center gap-1"><Trophy className="w-3 h-3 text-amber-500" /> 比赛</div>
        <div className="flex items-center gap-1"><ClipboardList className="w-3 h-3 text-blue-500" /> 有计划</div>
      </div>

      {/* Competition List */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h5 className="text-xs font-semibold text-slate-600 flex items-center gap-1">
            <Trophy className="w-3 h-3 text-amber-500" /> 比赛日程
          </h5>
          <button
            onClick={() => setShowCompModal(true)}
            className="flex items-center gap-1 px-2 py-1 bg-blue-500 text-white rounded text-[10px] hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-3 h-3" /> 添加
          </button>
        </div>

        {competitions.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-3">暂无比赛安排</p>
        ) : (
          <div className="space-y-1.5">
            {competitions.map(comp => {
              const daysUntil = Math.ceil((new Date(comp.competition_date).getTime() - Date.now()) / 86400000);
              const isPast = daysUntil < 0;
              return (
                <div
                  key={comp.id}
                  onClick={() => handleCompClick(comp)}
                  className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-colors ${
                    selectedComp?.id === comp.id
                      ? 'border-blue-300 bg-blue-50'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-700 truncate">{comp.name}</p>
                    <p className="text-[10px] text-slate-400">
                      {comp.competition_date}
                      {!isPast && <span className="ml-1 text-blue-500">（倒计时 {daysUntil} 天）</span>}
                      {isPast && <span className="ml-1 text-slate-400">（已结束）</span>}
                    </p>
                    {comp.location && <p className="text-[10px] text-slate-400">📍 {comp.location}</p>}
                  </div>
                  <button
                    onClick={e => { e.stopPropagation(); handleDeleteComp(comp.id); }}
                    className="p-1 rounded hover:bg-red-50 text-slate-300 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Competition Recommendation Panel */}
      {selectedComp && (
        <div className="p-3 rounded-lg border border-slate-200 space-y-2 animate-fade-in">
          <h5 className="text-xs font-semibold text-slate-700">
            📋 {selectedComp.name} — 训练建议
          </h5>
          {recLoading ? (
            <div className="skeleton h-20 w-full" />
          ) : recommendation ? (
            <div className="space-y-2">
              <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${PHASE_COLORS[recommendation.phase_label] || 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                {recommendation.phase} · 负荷 {recommendation.load_range}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{recommendation.description}</p>
              <ul className="space-y-0.5">
                {recommendation.recommendations.map((r, i) => (
                  <li key={i} className="text-[11px] text-slate-500 flex items-start gap-1">
                    <span className="text-blue-400 mt-0.5">●</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-xs text-slate-400">暂无建议数据</p>
          )}
        </div>
      )}

      {/* Selected Day Detail Panel */}
      {selectedDate && (
        <div className="p-3 rounded-lg border border-blue-200 bg-blue-50/50 space-y-2 animate-fade-in">
          <div className="flex items-center justify-between">
            <h5 className="text-xs font-semibold text-slate-700 flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {selectedDate}
              {riskMap[selectedDate]?.has_competition && (
                <span className="text-amber-500 flex items-center gap-0.5">
                  <Trophy className="w-3 h-3" /> {riskMap[selectedDate]?.competition_name}
                </span>
              )}
              {assignMap[selectedDate] && (
                <span className="text-blue-500 flex items-center gap-0.5">
                  <ClipboardList className="w-3 h-3" /> {assignMap[selectedDate]?.template_name}
                </span>
              )}
            </h5>
            <div className="flex items-center gap-1">
              {editing ? (
                <>
                  <button onClick={handleSaveDay} className="p-1 rounded bg-green-500 text-white hover:bg-green-600 transition-colors">
                    <Save className="w-3 h-3" />
                  </button>
                  <button onClick={() => setEditing(false)} className="p-1 rounded hover:bg-slate-200 transition-colors">
                    <X className="w-3 h-3 text-slate-400" />
                  </button>
                </>
              ) : (
                <div className="flex items-center gap-1">
                  <button onClick={() => { setLogFormDate(selectedDate); setShowLogForm(true); }}
                    className="p-1 rounded hover:bg-slate-200 transition-colors flex items-center gap-0.5 text-[10px] text-blue-500">
                    <PenLine className="w-3 h-3" /> 日志
                  </button>
                  <button onClick={() => setShowAssignModal(true)}
                    className="p-1 rounded hover:bg-slate-200 transition-colors flex items-center gap-0.5 text-[10px] text-purple-500">
                    <ClipboardList className="w-3 h-3" /> 分配
                  </button>
                  <button onClick={() => setEditing(true)} className="p-1 rounded hover:bg-slate-200 transition-colors">
                    <Edit3 className="w-3 h-3 text-slate-400" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {dayLoading ? (
            <div className="skeleton h-16 w-full" />
          ) : editing ? (
            <div className="space-y-2">
              <div>
                <label className="text-[10px] text-slate-500">训练负荷 (0-100)</label>
                <input
                  type="range" value={editLoad} onChange={e => setEditLoad(Number(e.target.value))}
                  min={0} max={100} className="w-full"
                />
                <span className="text-xs font-mono text-blue-600">{editLoad}</span>
              </div>
              <div>
                <label className="text-[10px] text-slate-500">训练内容</label>
                <textarea
                  value={editContent}
                  onChange={e => setEditContent(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="训练安排..."
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-500">备注</label>
                <textarea
                  value={editNotes}
                  onChange={e => setEditNotes(e.target.value)}
                  rows={1}
                  className="w-full px-3 py-1.5 rounded border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="备注..."
                />
              </div>
            </div>
          ) : dayMetrics ? (
            <div className="space-y-1.5">
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-1.5 text-xs">
                  <Zap className="w-3 h-3 text-orange-500" />
                  <span className="text-slate-500">负荷:</span>
                  <span className="font-mono font-bold">{dayMetrics.training_load}</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <AlertTriangle className="w-3 h-3 text-red-500" />
                  <span className="text-slate-500">风险:</span>
                  <span className="font-mono font-bold">{dayMetrics.injury_risk}</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <Target className="w-3 h-3 text-purple-500" />
                  <span className="text-slate-500">疲劳:</span>
                  <span className="font-mono font-bold">{dayMetrics.fatigue}</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <Moon className="w-3 h-3 text-indigo-500" />
                  <span className="text-slate-500">睡眠:</span>
                  <span className="font-mono font-bold">{dayMetrics.sleep_quality}</span>
                </div>
              </div>
              {dayMetrics.training_content && (
                <p className="text-xs text-slate-600 mt-1">📝 {dayMetrics.training_content}</p>
              )}
              {dayMetrics.notes && (
                <p className="text-[11px] text-slate-400 mt-1">{dayMetrics.notes}</p>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-400">暂无数据，点击编辑添加训练安排</p>
          )}
        </div>
      )}

      {/* Training Log Form Modal */}
      {showLogForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl w-full max-w-lg shadow-xl max-h-[85vh] overflow-hidden">
            <TrainingLogForm
              athleteId={athleteId}
              date={logFormDate}
              onClose={() => setShowLogForm(false)}
              onSaved={() => { setShowLogForm(false); fetchMonthData(); }}
            />
          </div>
        </div>
      )}

      {/* Assignment Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-h-[80vh] overflow-y-auto">
            <AssignmentModal
              athleteId={athleteId}
              date={selectedDate || logFormDate}
              onClose={() => setShowAssignModal(false)}
              onAssigned={() => { setShowAssignModal(false); fetchMonthData(); }}
            />
          </div>
        </div>
      )}

      {/* Add Competition Modal */}
      {showCompModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-5 w-full max-w-sm shadow-xl animate-scale-in">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-slate-800">添加比赛</h4>
              <button onClick={() => setShowCompModal(false)} className="p-1 rounded hover:bg-slate-100">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">赛事名称 *</label>
                <input
                  type="text" value={compName} onChange={e => setCompName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="如: 全国锦标赛"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">比赛日期 *</label>
                <input
                  type="date" value={compDate} onChange={e => setCompDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">地点</label>
                <input
                  type="text" value={compLocation} onChange={e => setCompLocation(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="如: 北京国家体育场"
                />
              </div>
              <button
                onClick={handleAddCompetition}
                disabled={!compName || !compDate}
                className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                确认添加
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
