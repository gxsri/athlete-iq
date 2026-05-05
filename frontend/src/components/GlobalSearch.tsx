import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, User, Dumbbell, FileText, X } from 'lucide-react';
import { getAthletes, getExercises, getTemplates, Athlete, ExerciseLibrary } from '../services/api';

interface GlobalSearchProps {
  open?: boolean;
  onClose?: () => void;
}

export function GlobalSearch({ open: externalOpen, onClose }: GlobalSearchProps = {}) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen !== undefined ? externalOpen : internalOpen;
  const close = () => { setInternalOpen(false); onClose?.(); };
  const [query, setQuery] = useState('');
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [exercises, setExercises] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setInternalOpen(true);
      }
      if (e.key === 'Escape') close();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      if (athletes.length === 0) getAthletes().then(setAthletes).catch(() => {});
      if (templates.length === 0) getTemplates().then(setTemplates).catch(() => {});
    }
  }, [open]);

  useEffect(() => {
    if (!query.trim()) {
      setExercises([]);
      return;
    }
    setLoading(true);
    const timer = setTimeout(() => {
      getExercises({}).then((data) => {
        const q = query.toLowerCase();
        const list = data.exercises || (Array.isArray(data) ? data : []);
        const filtered = list.filter((e: any) =>
          e.name.toLowerCase().includes(q) || e.description?.toLowerCase().includes(q)
        );
        setExercises(filtered);
      }).catch(() => setExercises([])).finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  const filteredAthletes = query.trim()
    ? athletes.filter(a => a.name.toLowerCase().includes(query.toLowerCase())).slice(0, 5)
    : [];

  const filteredTemplates = query.trim()
    ? templates.filter((t: any) => t.name.toLowerCase().includes(query.toLowerCase())).slice(0, 3)
    : [];

  const hasResults = filteredAthletes.length > 0 || exercises.length > 0 || filteredTemplates.length > 0;

  const navigateTo = (path: string) => {
    close();
    setQuery('');
    navigate(path);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-[15vh]" onClick={close}>
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 p-4 border-b border-slate-200">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="搜索运动员、动作、模板..."
            className="flex-1 text-lg outline-none text-slate-800 placeholder-slate-300"
          />
          <button
            onClick={close}
            className="p-1 rounded hover:bg-slate-100"
            title="关闭 (Esc)"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2">
          {loading && <p className="text-sm text-slate-400 text-center py-4">搜索中...</p>}

          {!loading && !hasResults && query.trim() && (
            <p className="text-sm text-slate-400 text-center py-8">未找到匹配结果</p>
          )}

          {!loading && !query.trim() && (
            <p className="text-sm text-slate-400 text-center py-8">输入关键词开始搜索...</p>
          )}

          {/* Athletes */}
          {filteredAthletes.length > 0 && (
            <div className="mb-2">
              <div className="text-xs text-slate-400 px-3 py-1 font-medium">运动员</div>
              {filteredAthletes.map(a => (
                <button
                  key={a.id}
                  onClick={() => navigateTo(`/athletes/${a.id}`)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 text-left transition-colors"
                >
                  <User className="w-4 h-4 text-blue-500" />
                  <div>
                    <div className="text-sm font-medium text-slate-700">{a.name}</div>
                    <div className="text-xs text-slate-400">{a.sport} · {a.position_or_event || ''}</div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Exercises */}
          {exercises.length > 0 && (
            <div className="mb-2">
              <div className="text-xs text-slate-400 px-3 py-1 font-medium">训练动作</div>
              {exercises.slice(0, 5).map((e: any) => (
                <button
                  key={e.id}
                  onClick={() => navigateTo('/planner')}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 text-left transition-colors"
                >
                  <Dumbbell className="w-4 h-4 text-green-500" />
                  <div>
                    <div className="text-sm font-medium text-slate-700">{e.name}</div>
                    <div className="text-xs text-slate-400">{e.category} · {e.description || ''}</div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Templates */}
          {filteredTemplates.length > 0 && (
            <div className="mb-2">
              <div className="text-xs text-slate-400 px-3 py-1 font-medium">训练模板</div>
              {filteredTemplates.map((t: any) => (
                <button
                  key={t.id}
                  onClick={() => navigateTo('/planner')}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 text-left transition-colors"
                >
                  <FileText className="w-4 h-4 text-purple-500" />
                  <div>
                    <div className="text-sm font-medium text-slate-700">{t.name}</div>
                    <div className="text-xs text-slate-400">{t.template_type} · {t.cycle_phase}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="px-4 py-2 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between">
          <span>使用 ↑↓ 键选择，Enter 打开</span>
          <span>Ctrl+K 打开搜索</span>
        </div>
      </div>
    </div>
  );
}
