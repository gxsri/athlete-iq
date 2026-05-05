import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, X, Search, Database, Heart, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import { getExercises, getCategories, createExercise, updateExercise, deleteExercise, seedPresetExercises, seedRehabExercises, ExerciseLibrary, CategoriesResponse } from '../services/api';

const l1Categories = ['全部', '力量', '耐力', '速度', '技战术', '混合', '恢复', '柔韧', '康复/纠正性训练'];
const l2Categories = ['全部', '肘部', '腕部', '膝关节', '腰部'];
const nasmPhases = ['全部', 'INH', 'LEN', 'ACT', 'INT'];

export function ExercisesPage() {
  const [exercises, setExercises] = useState<ExerciseLibrary[]>([]);
  const [categories, setCategories] = useState<CategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [l1Filter, setL1Filter] = useState('全部');
  const [l2Filter, setL2Filter] = useState('全部');
  const [nasmFilter, setNasmFilter] = useState('全部');
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Form state
  const [formName, setFormName] = useState('');
  const [formCategoryL1, setFormCategoryL1] = useState('力量');
  const [formCategoryL2, setFormCategoryL2] = useState('');
  const [formNasmPhase, setFormNasmPhase] = useState('');
  const [formTargetMuscles, setFormTargetMuscles] = useState('');
  const [formInstructions, setFormInstructions] = useState('');
  const [formLiteratureRef, setFormLiteratureRef] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formWeight, setFormWeight] = useState('0');
  const [formReps, setFormReps] = useState('8');
  const [formSets, setFormSets] = useState('3');
  const [formRpe, setFormRpe] = useState('6');
  const [formRest, setFormRest] = useState('60');

  const loadExercises = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (l1Filter !== '全部') params.category_l1 = l1Filter;
      if (l2Filter !== '全部') params.category_l2 = l2Filter;
      if (nasmFilter !== '全部') params.nasm_phase = nasmFilter;
      if (search) params.search = search;
      const result = await getExercises(params);
      setExercises(result.exercises || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadExercises(); }, [l1Filter, l2Filter, nasmFilter]);
  useEffect(() => { getCategories().then(setCategories).catch(() => {}); }, []);

  const handleSearch = () => loadExercises();

  const resetForm = () => {
    setFormName(''); setFormCategoryL1('力量'); setFormCategoryL2('');
    setFormNasmPhase(''); setFormTargetMuscles(''); setFormInstructions('');
    setFormLiteratureRef(''); setFormDesc('');
    setFormWeight('0'); setFormReps('8'); setFormSets('3');
    setFormRpe('6'); setFormRest('60');
  };

  const buildFormData = () => ({
    name: formName,
    category: formCategoryL1,
    category_l1: formCategoryL1 || undefined,
    category_l2: formCategoryL2 || undefined,
    nasm_phase: formNasmPhase || undefined,
    target_muscles: formTargetMuscles ? formTargetMuscles.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : [],
    instructions: formInstructions || undefined,
    literature_ref: formLiteratureRef || undefined,
    description: formDesc || undefined,
    preset_params: {
      weight_kg: Number(formWeight) || 0,
      reps: Number(formReps) || 8,
      sets: Number(formSets) || 3,
      rpe: Number(formRpe) || 6,
      rest_seconds: Number(formRest) || 60,
    },
  });

  const handleAdd = async () => {
    if (!formName) { setError('请输入动作名称'); return; }
    setError('');
    try {
      await createExercise(buildFormData());
      setMessage(`已添加: ${formName}`);
      resetForm(); setShowAdd(false);
      loadExercises();
    } catch (err: any) { setError(err.message); }
  };

  const handleUpdate = async (id: string) => {
    if (!formName) { setError('请输入动作名称'); return; }
    setError('');
    try {
      await updateExercise(id, buildFormData());
      setMessage('已更新');
      setEditingId(null); resetForm(); setShowAdd(false);
      loadExercises();
    } catch (err: any) { setError(err.message); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此动作？')) return;
    try { await deleteExercise(id); setMessage('已删除'); loadExercises(); }
    catch (err: any) { setError(err.message); }
  };

  const handleSeedPreset = async () => {
    try { const r = await seedPresetExercises(); setMessage(r.status === 'seeded' ? `已导入 ${r.count || 10} 个基础动作` : '操作完成'); loadExercises(); }
    catch (err: any) { setError(err.message); }
  };

  const handleSeedRehab = async () => {
    try {
      const r = await seedRehabExercises();
      if (r.status === 'seeded') setMessage(`已导入 ${r.rehab_count} 个康复动作 + ${r.injury_links} 个伤病关联`);
      else setMessage(r.status || '操作完成');
      loadExercises();
      getCategories().then(setCategories).catch(() => {});
    } catch (err: any) { setError(err.message); }
  };

  const startEdit = (ex: ExerciseLibrary) => {
    setEditingId(ex.id);
    setFormName(ex.name);
    setFormCategoryL1(ex.category_l1 || ex.category || '力量');
    setFormCategoryL2(ex.category_l2 || '');
    setFormNasmPhase(ex.nasm_phase || '');
    setFormTargetMuscles((ex.target_muscles || []).join(', '));
    setFormInstructions(ex.instructions || '');
    setFormLiteratureRef(ex.literature_ref || '');
    setFormDesc(ex.description || '');
    setFormWeight(String(ex.preset_params?.weight_kg || 0));
    setFormReps(String(ex.preset_params?.reps || 8));
    setFormSets(String(ex.preset_params?.sets || 3));
    setFormRpe(String(ex.preset_params?.rpe || 6));
    setFormRest(String(ex.preset_params?.rest_seconds || 60));
    setShowAdd(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">训练动作库</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            力量 · 技战术 · 康复/纠正性训练 · {categories ? categories.categories_l2.length : 0} 个康复分类
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleSeedPreset}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-500 text-white rounded-lg text-xs font-medium hover:bg-slate-600 transition-colors">
            <Database className="w-4 h-4" /> 导入基础动作
          </button>
          <button onClick={handleSeedRehab}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 text-white rounded-lg text-xs font-medium hover:bg-emerald-600 transition-colors">
            <Heart className="w-4 h-4" /> 导入康复动作
          </button>
          <button onClick={() => { resetForm(); setShowAdd(!showAdd); setEditingId(null); }}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors">
            <Plus className="w-4 h-4" /> 添加动作
          </button>
        </div>
      </div>

      {message && <div className="p-3 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-sm rounded-lg">{message}</div>}
      {error && <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg">{error}</div>}

      {/* Add/Edit Form */}
      {showAdd && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {editingId ? '编辑动作' : '添加新动作'}
            </h4>
            <button onClick={() => { setShowAdd(false); setEditingId(null); }} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-500 mb-1">动作名称 *</label>
              <input type="text" value={formName} onChange={e => setFormName(e.target.value)}
                placeholder="如: 北欧腘绳肌离心训练"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">一级分类</label>
              <select value={formCategoryL1} onChange={e => setFormCategoryL1(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm">
                {l1Categories.filter(c => c !== '全部').map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            {formCategoryL1 === '康复/纠正性训练' && (
              <>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">二级分类</label>
                  <select value={formCategoryL2} onChange={e => setFormCategoryL2(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm">
                    <option value="">无</option>
                    {l2Categories.filter(c => c !== '全部').map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">NASM 阶段</label>
                  <select value={formNasmPhase} onChange={e => setFormNasmPhase(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm">
                    <option value="">无</option>
                    {nasmPhases.filter(p => p !== '全部').map(p => <option key={p} value={p}>{p} {p==='INH'?'抑制':p==='LEN'?'拉长':p==='ACT'?'激活':'整合'}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">目标肌群 (逗号分隔)</label>
                  <input type="text" value={formTargetMuscles} onChange={e => setFormTargetMuscles(e.target.value)}
                    placeholder="如: 腘绳肌, 半腱肌"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs text-slate-500 mb-1">详细步骤</label>
                  <textarea value={formInstructions} onChange={e => setFormInstructions(e.target.value)}
                    rows={3} placeholder="1. ...\n2. ..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm resize-none" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">文献依据</label>
                  <input type="text" value={formLiteratureRef} onChange={e => setFormLiteratureRef(e.target.value)}
                    placeholder="如: NASM CET"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
                </div>
              </>
            )}
            <div>
              <label className="block text-xs text-slate-500 mb-1">预设负重 (kg)</label>
              <input type="number" value={formWeight} onChange={e => setFormWeight(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">预设组数</label>
              <input type="number" value={formSets} onChange={e => setFormSets(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">预设次数</label>
              <input type="number" value={formReps} onChange={e => setFormReps(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">预设 RPE (3-10)</label>
              <input type="number" min="3" max="10" value={formRpe} onChange={e => setFormRpe(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">组间休息 (秒)</label>
              <input type="number" value={formRest} onChange={e => setFormRest(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs text-slate-500 mb-1">描述</label>
              <input type="text" value={formDesc} onChange={e => setFormDesc(e.target.value)}
                placeholder="简短描述..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm" />
            </div>
          </div>
          <button onClick={() => editingId ? handleUpdate(editingId) : handleAdd()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors">
            <Save className="w-4 h-4" /> {editingId ? '更新' : '保存'}
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="space-y-3">
        {/* Search */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="搜索动作..."
              value={search} onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <button onClick={handleSearch}
            className="px-3 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-lg text-sm hover:bg-slate-200 dark:hover:bg-slate-700">
            搜索
          </button>
        </div>

        {/* L1 Filter */}
        <div className="flex gap-1 flex-wrap">
          {l1Categories.map(cat => (
            <button key={cat} onClick={() => { setL1Filter(cat); setL2Filter('全部'); setNasmFilter('全部'); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                l1Filter === cat ? 'bg-cyan-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}>{cat}</button>
          ))}
        </div>

        {/* L2 Filter (rehab specific) */}
        {l1Filter === '康复/纠正性训练' && (
          <div className="flex gap-1 flex-wrap items-center">
            <span className="text-xs text-slate-400 mr-1">部位:</span>
            {l2Categories.map(cat => (
              <button key={cat} onClick={() => setL2Filter(cat)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  l2Filter === cat ? 'bg-emerald-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}>{cat}</button>
            ))}
            <span className="text-xs text-slate-400 mx-2">|</span>
            <span className="text-xs text-slate-400 mr-1">NASM:</span>
            {nasmPhases.map(p => (
              <button key={p} onClick={() => setNasmFilter(p)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  nasmFilter === p ? 'bg-purple-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}>
                {p === '全部' ? '全部' : `${p} ${p==='INH'?'抑制':p==='LEN'?'拉长':p==='ACT'?'激活':'整合'}`}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Exercise List */}
      {loading ? (
        <div className="space-y-3">{[1,2,3,4,5].map(i => <div key={i} className="skeleton h-16 rounded-lg" />)}</div>
      ) : exercises.length === 0 ? (
        <div className="text-center py-12 text-slate-400 dark:text-slate-500">
          <p className="text-sm">暂无训练动作</p>
          <p className="text-xs mt-1">点击"导入康复动作"或"添加动作"开始</p>
        </div>
      ) : (
        <div className="space-y-2">
          {exercises.map(ex => {
            const isRehab = ex.category_l1 === '康复/纠正性训练';
            const isExpanded = expandedId === ex.id;
            return (
              <div key={ex.id} className="card py-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpandedId(isExpanded ? null : ex.id)}>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{ex.name}</span>
                      {ex.nasm_phase && (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          ex.nasm_phase === 'INH' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' :
                          ex.nasm_phase === 'LEN' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' :
                          ex.nasm_phase === 'ACT' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400' :
                          'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                        }`}>{ex.nasm_phase}</span>
                      )}
                      {ex.category_l2 && (
                        <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                          {ex.category_l2}
                        </span>
                      )}
                      {!isRehab && (
                        <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400">
                          {ex.category || ex.category_l1}
                        </span>
                      )}
                    </div>
                    {ex.description && (
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 truncate">{ex.description}</p>
                    )}
                    {ex.preset_params && (
                      <div className="flex gap-2 mt-1 text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                        {ex.preset_params.weight_kg > 0 && <span>{ex.preset_params.weight_kg}kg</span>}
                        <span>{ex.preset_params.sets}组×{ex.preset_params.reps}次</span>
                        <span>RPE {ex.preset_params.rpe}</span>
                        {ex.preset_params.rest_seconds > 0 && <span>休{ex.preset_params.rest_seconds}s</span>}
                        {ex.preset_params.duration_min > 0 && <span>{ex.preset_params.duration_min}min</span>}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-1 ml-3 shrink-0">
                    {isRehab && (
                      <button onClick={() => setExpandedId(isExpanded ? null : ex.id)}
                        className="p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    )}
                    <button onClick={() => startEdit(ex)}
                      className="px-2 py-1 text-xs text-cyan-500 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 rounded transition-colors">编辑</button>
                    <button onClick={() => handleDelete(ex.id)}
                      className="p-1 text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Expanded rehab details */}
                {isExpanded && isRehab && (
                  <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2 text-xs">
                    {ex.target_muscles && ex.target_muscles.length > 0 && (
                      <div className="flex items-start gap-2">
                        <span className="text-slate-400 shrink-0">目标肌群:</span>
                        <div className="flex gap-1 flex-wrap">
                          {ex.target_muscles.map((m: string, i: number) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px]">{m}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {ex.instructions && (
                      <div>
                        <span className="text-slate-400">详细步骤:</span>
                        <pre className="mt-1 text-slate-600 dark:text-slate-400 whitespace-pre-wrap font-sans leading-relaxed bg-slate-50 dark:bg-slate-800/50 p-2 rounded">{ex.instructions}</pre>
                      </div>
                    )}
                    {ex.literature_ref && (
                      <div className="flex items-start gap-2">
                        <BookOpen className="w-3 h-3 text-slate-400 mt-0.5 shrink-0" />
                        <span className="text-slate-500 dark:text-slate-500 italic">{ex.literature_ref}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
