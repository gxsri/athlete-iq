import React, { useState, useMemo, useEffect } from 'react';
import { Search, X, Plus, Star, Clock } from 'lucide-react';
import type { ExerciseLibrary } from '../services/api';
import { getExercises, getFavorites, getRecents, addFavorite, removeFavorite, createExercise } from '../services/api';

interface QuickAddExerciseProps {
  onAdd: (exercise: ExerciseLibrary) => void;
}

const categories = ['全部', '力量', '耐力', '速度', '技战术', '混合', '康复/纠正性训练'];
const rehabL2 = ['肘部', '腕部', '膝关节', '腰部'];

export function QuickAddExercise({ onAdd }: QuickAddExerciseProps) {
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('全部');
  const [selected, setSelected] = useState<ExerciseLibrary | null>(null);
  const [allExercises, setAllExercises] = useState<ExerciseLibrary[]>([]);
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [recents, setRecents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('力量');
  const [newDesc, setNewDesc] = useState('');
  const [newWeight, setNewWeight] = useState('80');
  const [newReps, setNewReps] = useState('8');
  const [newSets, setNewSets] = useState('3');
  const [newRest, setNewRest] = useState('60');
  const [newRpe, setNewRpe] = useState('7');
  const [newMsg, setNewMsg] = useState('');
  const [showFavs, setShowFavs] = useState(false);
  const [showRecents, setShowRecents] = useState(true);

  useEffect(() => {
    Promise.all([
      getExercises({}).then((data: any) => data.exercises || data || []).catch(() => []),
      getFavorites('exercise').catch(() => []),
      getRecents('exercise').catch(() => []),
    ]).then(([ex, favs, rec]) => {
      setAllExercises(Array.isArray(ex) ? ex : []);
      setFavoriteIds(new Set(favs.map((f: any) => f.item_id)));
      setRecents(rec);
      setLoading(false);
    });
  }, []);

  const toggleFavorite = async (e: React.MouseEvent, exerciseId: string) => {
    e.stopPropagation();
    if (favoriteIds.has(exerciseId)) {
      await removeFavorite('exercise', exerciseId).catch(() => {});
      setFavoriteIds(prev => { const next = new Set(prev); next.delete(exerciseId); return next; });
    } else {
      await addFavorite('exercise', exerciseId).catch(() => {});
      setFavoriteIds(prev => new Set(prev).add(exerciseId));
    }
  };

  const filtered = useMemo(() => {
    let list = showFavs ? allExercises.filter(e => favoriteIds.has(e.id)) : allExercises;
    if (!showFavs && !showRecents) list = allExercises;
    if (activeCategory !== '全部') list = list.filter(e => e.category === activeCategory);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(e => e.name.toLowerCase().includes(q) || e.description?.toLowerCase().includes(q));
    }
    return list;
  }, [search, activeCategory, allExercises, favoriteIds, showFavs]);

  const recentExercises = useMemo(() => {
    if (!showRecents || search.trim()) return [];
    return recents
      .map((r: any) => allExercises.find(e => e.id === r.item_id))
      .filter(Boolean) as ExerciseLibrary[];
  }, [recents, allExercises, showRecents, search]);

  const handleCreateExercise = async () => {
    if (!newName.trim()) { setNewMsg('请输入动作名称'); return; }
    try {
      const created = await createExercise({
        name: newName.trim(),
        category: newCategory,
        description: newDesc.trim() || undefined,
        preset_params: {
          weight_kg: Number(newWeight),
          reps: Number(newReps),
          sets: Number(newSets),
          rest_seconds: Number(newRest),
          rpe: Number(newRpe),
        },
      });
      setAllExercises(prev => [...prev, created]);
      setNewName(''); setNewMsg('创建成功！');
      setTimeout(() => { setShowNewForm(false); setNewMsg(''); }, 1000);
    } catch (err: any) {
      setNewMsg(err.message || '创建失败');
    }
  };

  return (
    <div className="space-y-3">
      {/* Search */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="搜索训练动作..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Quick filters */}
      <div className="flex items-center gap-1">
        <button onClick={() => { setShowFavs(!showFavs); setShowRecents(false); }}
          className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${showFavs ? 'bg-yellow-400 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
          <Star className="w-3 h-3 inline mr-0.5" />我的收藏
        </button>
        <button onClick={() => { setShowRecents(!showRecents); setShowFavs(false); }}
          className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${showRecents && !showFavs ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
          <Clock className="w-3 h-3 inline mr-0.5" />最近使用
        </button>
        <button onClick={() => setShowNewForm(!showNewForm)}
          className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors">
          <Plus className="w-3 h-3 inline mr-0.5" />新建
        </button>
      </div>

      {/* New Exercise Form */}
      {showNewForm && (
        <div className="p-3 rounded-lg bg-green-50 border border-green-200 space-y-2">
          <input type="text" placeholder="动作名称" value={newName} onChange={e => setNewName(e.target.value)}
            className="w-full px-3 py-1.5 rounded border border-slate-200 text-sm" />
          <div className="grid grid-cols-2 gap-2">
            <select value={newCategory} onChange={e => setNewCategory(e.target.value)}
              className="px-2 py-1.5 rounded border border-slate-200 text-xs bg-white">
              {categories.filter(c => c !== '全部').map(c => <option key={c}>{c}</option>)}
            </select>
            <input type="text" placeholder="描述" value={newDesc} onChange={e => setNewDesc(e.target.value)}
              className="px-2 py-1.5 rounded border border-slate-200 text-xs" />
          </div>
          <div className="grid grid-cols-5 gap-1">
            <input type="number" placeholder="重量" value={newWeight} onChange={e => setNewWeight(e.target.value)} className="px-1 py-1 rounded border border-slate-200 text-xs" />
            <input type="number" placeholder="次" value={newReps} onChange={e => setNewReps(e.target.value)} className="px-1 py-1 rounded border border-slate-200 text-xs" />
            <input type="number" placeholder="组" value={newSets} onChange={e => setNewSets(e.target.value)} className="px-1 py-1 rounded border border-slate-200 text-xs" />
            <input type="number" placeholder="间歇" value={newRest} onChange={e => setNewRest(e.target.value)} className="px-1 py-1 rounded border border-slate-200 text-xs" />
            <input type="number" placeholder="RPE" value={newRpe} onChange={e => setNewRpe(e.target.value)} className="px-1 py-1 rounded border border-slate-200 text-xs" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreateExercise} className="px-3 py-1.5 bg-green-500 text-white rounded text-xs hover:bg-green-600">创建</button>
            <button onClick={() => setShowNewForm(false)} className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded text-xs hover:bg-slate-200">取消</button>
          </div>
          {newMsg && <p className={`text-xs ${newMsg.includes('成功') ? 'text-green-600' : 'text-red-500'}`}>{newMsg}</p>}
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-1">
        {categories.map(cat => (
          <button key={cat} onClick={() => setActiveCategory(cat)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${activeCategory === cat ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            {cat}
          </button>
        ))}
      </div>

      {/* Recent Exercises */}
      {recentExercises.length > 0 && showRecents && !search.trim() && !showFavs && (
        <div>
          <div className="text-xs text-slate-400 mb-1">最近使用</div>
          <div className="max-h-32 overflow-y-auto space-y-1">
            {recentExercises.slice(0, 5).map(ex => (
              <div key={ex.id} onClick={() => setSelected(ex)}
                className={`p-2 rounded-lg border cursor-pointer transition-colors text-sm ${selected?.id === ex.id ? 'border-blue-300 bg-blue-50' : 'border-slate-100 hover:bg-slate-50'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-700">{ex.name}</span>
                  <button onClick={e => toggleFavorite(e, ex.id)}
                    className={favoriteIds.has(ex.id) ? 'text-yellow-500' : 'text-slate-300 hover:text-yellow-400'}>
                    <Star className="w-3.5 h-3.5" fill={favoriteIds.has(ex.id) ? 'currentColor' : 'none'} />
                  </button>
                </div>
                <div className="text-xs text-slate-400">{ex.category}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exercise List */}
      {loading ? (
        <p className="text-xs text-slate-400 text-center py-4">加载中...</p>
      ) : (
        <div className="max-h-48 overflow-y-auto space-y-1">
          {filtered.map(ex => (
            <div key={ex.id} onClick={() => setSelected(ex)}
              className={`p-2 rounded-lg border cursor-pointer transition-colors text-sm ${selected?.id === ex.id ? 'border-blue-300 bg-blue-50' : 'border-slate-100 hover:bg-slate-50'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-700">{ex.name}</div>
                  <div className="text-xs text-slate-400">{ex.category}</div>
                </div>
                <button onClick={e => toggleFavorite(e, ex.id)}
                  className={favoriteIds.has(ex.id) ? 'text-yellow-500' : 'text-slate-300 hover:text-yellow-400'}>
                  <Star className="w-3.5 h-3.5" fill={favoriteIds.has(ex.id) ? 'currentColor' : 'none'} />
                </button>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-xs text-slate-400 text-center py-4">无匹配训练动作</p>
          )}
        </div>
      )}

      {/* Confirm Add */}
      {selected && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-700">{selected.name}</span>
            <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">{selected.category}</span>
          </div>
          {selected.description && <p className="text-xs text-slate-600">{selected.description}</p>}
          {selected.preset_params && (
            <div className="grid grid-cols-5 gap-2 text-xs text-slate-500">
              <span>重量: {selected.preset_params.weight_kg}kg</span>
              <span>次: {selected.preset_params.reps}</span>
              <span>组: {selected.preset_params.sets}</span>
              <span>间歇: {selected.preset_params.rest_seconds}s</span>
              <span>RPE: {selected.preset_params.rpe}</span>
            </div>
          )}
          <div className="flex gap-2">
            <button onClick={() => { onAdd(selected); setSelected(null); }}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-medium hover:bg-blue-600 transition-colors">
              <Plus className="w-3 h-3" /> 添加到计划
            </button>
            <button onClick={() => setSelected(null)}
              className="flex items-center gap-1 px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-200 transition-colors">
              <X className="w-3 h-3" /> 取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
