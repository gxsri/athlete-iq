import React, { useState } from 'react';
import { Droplets, UtensilsCrossed, Scale, Activity, AlertTriangle } from 'lucide-react';

interface NutritionData {
  protein?: number;
  refuel?: number;
  water?: number;
  appetite?: number;
  weight?: number;
  phase?: string;
  notes?: string;
}

interface NutritionCardProps {
  nutritionData: NutritionData;
  athleteName: string;
  onSubmit: (data: NutritionData) => void | Promise<void>;
}

const nutritionAdvice: Record<string, string[]> = {
  '备赛期': [
    '蛋白质摄入: 1.6–2.2 g/kg 体重/天',
    '碳水化合物: 5–7 g/kg 体重/天',
    '训练前 2–3 小时进食全餐',
    '训练中每 15–20 分钟补水 150–300ml',
    '训练后 30 分钟内补充蛋白质 + 碳水',
  ],
  '比赛期': [
    '赛前 3–4 小时进食高碳水低脂餐',
    '赛前 1 小时可补充易消化碳水（香蕉、能量棒）',
    '赛中每 15–20 分钟补水 150–200ml',
    '赛后即刻补充碳水 + 蛋白质（3:1 比例）',
    '全天饮水量 ≥ 35ml/kg 体重',
  ],
  '休赛期': [
    '蛋白质摄入: 1.4–1.8 g/kg 体重/天（维持量）',
    '碳水化合物: 3–5 g/kg 体重/天',
    '注意体重管理，避免体脂率过度升高',
    '补充微量营养素: 铁、钙、维生素D',
    '可适当增加抗炎食物摄入（Omega-3、姜黄等）',
  ],
  '过渡期': [
    '蛋白质摄入: 1.2–1.6 g/kg 体重/天',
    '碳水化合物: 3–4 g/kg 体重/天',
    '重点补充恢复性营养素，支持组织修复',
    '保持每日充足饮水 2–2.5L',
    '如有减脂需求，控制热量缺口在300-500kcal/天',
  ],
};

export function NutritionCard({ nutritionData, athleteName, onSubmit }: NutritionCardProps) {
  const [phase, setPhase] = useState(nutritionData.phase || '备赛期');
  const [protein, setProtein] = useState(nutritionData.protein ?? 3);
  const [refuel, setRefuel] = useState(nutritionData.refuel ?? 3);
  const [water, setWater] = useState(nutritionData.water ?? 3);
  const [appetite, setAppetite] = useState(nutritionData.appetite ?? 3);
  const [weight, setWeight] = useState(nutritionData.weight ?? '');
  const [notes, setNotes] = useState(nutritionData.notes ?? '');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const waterSufficient = water >= 4;
  const waterColor = water <= 2 ? 'text-red-500' : water >= 4 ? 'text-green-500' : 'text-yellow-500';
  const waterBg = water <= 2 ? 'bg-red-50' : water >= 4 ? 'bg-green-50' : 'bg-yellow-50';

  const riskTriggered = protein <= 2 || refuel <= 2 || water <= 2 || appetite <= 2;

  const handleSubmit = async () => {
    setMessage('');
    setError('');
    try {
      await onSubmit({
        phase,
        protein,
        refuel,
        water,
        appetite,
        weight: weight ? Number(weight) : undefined,
        notes: notes || undefined,
      });
      setMessage('营养记录已提交');
    } catch (err: any) {
      setError(err.message || '提交失败');
    }
  };

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <UtensilsCrossed className="w-4 h-4" /> 营养监测 - {athleteName}
        </h4>
      </div>

      {/* Risk Warning */}
      {riskTriggered && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-700">营养风险预警</p>
            <p className="text-xs text-red-600 mt-0.5">
              {protein <= 2 && '蛋白质摄入不足；'}
              {refuel <= 2 && '补能不足；'}
              {water <= 2 && '饮水不足；'}
              {appetite <= 2 && '食欲下降；'}
              请及时干预。
            </p>
          </div>
        </div>
      )}

      <div>
        <label className="block text-xs text-slate-500 mb-1">训练阶段</label>
        <select
          value={phase}
          onChange={e => setPhase(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="备赛期">备赛期</option>
          <option value="比赛期">比赛期</option>
          <option value="休赛期">休赛期</option>
          <option value="过渡期">过渡期</option>
        </select>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500 flex items-center gap-1">
              <Activity className="w-3 h-3" />蛋白质摄入 ({protein}/5)
            </span>
            <span className={`font-mono ${protein <= 2 ? 'text-red-500' : 'text-slate-600'}`}>{protein}</span>
          </div>
          <input type="range" value={protein} onChange={e => setProtein(Number(e.target.value))} min={1} max={5} className="w-full" />
          <div className="flex justify-between text-xs text-slate-400">
            <span>1 严重不足</span><span>5 充足</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500 flex items-center gap-1">
              <UtensilsCrossed className="w-3 h-3" />训练后补能 ({refuel}/5)
            </span>
            <span className={`font-mono ${refuel <= 2 ? 'text-red-500' : 'text-slate-600'}`}>{refuel}</span>
          </div>
          <input type="range" value={refuel} onChange={e => setRefuel(Number(e.target.value))} min={1} max={5} className="w-full" />
          <div className="flex justify-between text-xs text-slate-400">
            <span>1 无补能</span><span>5 及时补能</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500 flex items-center gap-1">
              <Droplets className="w-3 h-3" />饮水摄入 ({water}/5)
            </span>
            <span className={`font-mono ${waterColor}`}>{water}</span>
          </div>
          <input type="range" value={water} onChange={e => setWater(Number(e.target.value))} min={1} max={5} className="w-full" />
          <div className="flex justify-between text-xs text-slate-400">
            <span>1 严重缺水</span><span>5 充足饮水</span>
          </div>
          <div className={`mt-1 px-2 py-0.5 rounded text-xs font-medium inline-flex items-center gap-1 ${waterBg} ${waterColor}`}>
            <Droplets className="w-3 h-3" />
            {waterSufficient ? '饮水充足' : water <= 2 ? '饮水不足' : '饮水一般'}
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-500 flex items-center gap-1">
              <Scale className="w-3 h-3" />食欲 ({appetite}/5)
            </span>
            <span className={`font-mono ${appetite <= 2 ? 'text-red-500' : 'text-slate-600'}`}>{appetite}</span>
          </div>
          <input type="range" value={appetite} onChange={e => setAppetite(Number(e.target.value))} min={1} max={5} className="w-full" />
          <div className="flex justify-between text-xs text-slate-400">
            <span>1 无食欲</span><span>5 食欲极好</span>
          </div>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">体重 (kg)</label>
          <input
            type="number"
            value={weight}
            onChange={e => setWeight(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="如: 75"
            min={30}
            max={200}
            step={0.1}
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">备注</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="饮食补充说明..."
          />
        </div>
      </div>

      {/* Nutrition Advice Template */}
      <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
        <p className="text-xs font-medium text-blue-700 mb-2">{phase}营养建议:</p>
        <ul className="space-y-1">
          {(nutritionAdvice[phase] || nutritionAdvice['备赛期']).map((tip, i) => (
            <li key={i} className="text-xs text-blue-600 flex items-start gap-1">
              <span className="text-blue-400 mt-0.5">●</span> {tip}
            </li>
          ))}
        </ul>
      </div>

      <button
        onClick={handleSubmit}
        className="w-full py-2.5 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
      >
        提交营养记录
      </button>

      {message && <p className="text-xs text-green-600 bg-green-50 p-2 rounded">{message}</p>}
      {error && <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{error}</p>}
    </div>
  );
}
