import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, ReferenceArea, Legend, BarChart, Bar
} from 'recharts';
import {
  ArrowLeft, Activity, Brain, Zap, Moon, AlertTriangle, RefreshCw
} from 'lucide-react';
import {
  getAthlete, getACWRTimeSeries, getRSSI, getTrainingRecommendation,
  getPerformanceComparison, getAthleteReport,
  Athlete, ACWRTimeSeries, RSSIDetail, TrainingRecommendationResponse
} from '../services/api';
import { RiskGauge } from '../components/RiskGauge';
import { TrainingStatus } from '../components/TrainingStatus';
import { TrainingCalendarHeatmap } from '../components/TrainingCalendarHeatmap';
import { HRVSleepTrend } from '../components/HRVSleepTrend';
import { TrainingLoadDistribution } from '../components/TrainingLoadDistribution';
import { CompetitionCalendar } from '../components/CompetitionCalendar';
import { TodayPlanCard } from '../components/TodayPlanCard';

function riskColor(zone: string): string {
  switch (zone) {
    case '安全区': return '#22c55e';
    case '谨慎区': return '#f59e0b';
    case '高风险区': return '#ef4444';
    case '功能性过度训练': return '#f59e0b';
    case '非功能性过度训练': return '#ef4444';
    case '适应性训练': return '#3b82f6';
    default: return '#22c55e';
  }
}

export function AthleteDetail() {
  const { id } = useParams<{ id: string }>();
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [acwrData, setAcwrData] = useState<ACWRTimeSeries | null>(null);
  const [rssiData, setRssiData] = useState<RSSIDetail | null>(null);
  const [recommendation, setRecommendation] = useState<TrainingRecommendationResponse | null>(null);
  const [perfCompare, setPerfCompare] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [comparisonMode, setComparisonMode] = useState(false);
  const [periodAStart, setPeriodAStart] = useState('');
  const [periodAEnd, setPeriodAEnd] = useState('');
  const [periodBStart, setPeriodBStart] = useState('');
  const [periodBEnd, setPeriodBEnd] = useState('');
  const [comparisonData, setComparisonData] = useState<any>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError('');
    Promise.all([
      getAthlete(id).catch(() => null),
      getACWRTimeSeries(id, 60).catch(() => null),
      getRSSI(id).catch(() => null),
      getTrainingRecommendation(id).catch(() => null),
      getPerformanceComparison(id).catch(() => null),
    ]).then(([ath, acwr, rssi, rec, perf]) => {
      setAthlete(ath);
      setAcwrData(acwr);
      setRssiData(rssi);
      setRecommendation(rec);
      setPerfCompare(perf);
      if (!ath) setError('运动员不存在');
    }).finally(() => setLoading(false));
  }, [id]);

  const handleCompare = async () => {
    if (!id || !periodAStart || !periodAEnd || !periodBStart || !periodBEnd) return;
    try {
      const report = await getAthleteReport(id);
      // Filter data by periods for comparison
      const filterByPeriod = (history: any[], start: string, end: string) =>
        history.filter((h: any) => h.date >= start && h.date <= end);
      const aAcwr = filterByPeriod(report.acwr_history || [], periodAStart, periodAEnd);
      const bAcwr = filterByPeriod(report.acwr_history || [], periodBStart, periodBEnd);
      const aRssi = filterByPeriod(report.rssi_history || [], periodAStart, periodAEnd);
      const bRssi = filterByPeriod(report.rssi_history || [], periodBStart, periodBEnd);
      const aTests = (report.recent_performance_tests || []).filter((t: any) =>
        t.test_date >= periodAStart && t.test_date <= periodAEnd);
      const bTests = (report.recent_performance_tests || []).filter((t: any) =>
        t.test_date >= periodBStart && t.test_date <= periodBEnd);
      setComparisonData({ aAcwr, bAcwr, aRssi, bRssi, aTests, bTests });
      setComparisonMode(true);
    } catch { setError('同期对比数据加载失败'); }
  };

  if (loading) return <div className="text-center py-16 text-slate-400">加载中...</div>;
  if (error || !athlete) return (
    <div className="text-center py-16">
      <p className="text-red-500">{error || '运动员不存在'}</p>
      <Link to="/athletes" className="text-blue-500 mt-2 inline-block">返回运动员列表</Link>
    </div>
  );

  // Chart data from real ACWR
  const chartData = acwrData ? acwrData.dates.map((d, i) => ({
    date: d,
    acwr: acwrData.acwr[i],
    acuteLoad: acwrData.acute_load[i],
    chronicLoad: acwrData.chronic_load[i],
  })) : [];

  // Performance comparisons
  const comparisons = perfCompare?.comparisons || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/athletes" className="p-2 rounded-lg hover:bg-slate-100 transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-500" />
        </Link>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-slate-900">{athlete.name}</h2>
          <p className="text-sm text-slate-500">
            {athlete.sport} · {athlete.position_or_event || '未指定位置'} · 训练年限 {athlete.training_years || '未知'}年
          </p>
        </div>
        {rssiData && <RiskGauge score={rssiData.rssi_score} size="sm" />}
      </div>

      {/* Training Status */}
      {id && <TrainingStatus athleteId={id} />}

      {/* Today's Plan Card */}
      {id && <TodayPlanCard athleteId={id} />}

      {/* ACWR Chart */}
      {acwrData && (
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4" /> ACWR 急慢性负荷比 — 最近 60 天趋势
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 'auto']} tick={{ fontSize: 11 }} />
              <ReferenceArea y1={0.8} y2={1.3} fill="#22c55e" fillOpacity={0.08} label="安全区" />
              <ReferenceArea y1={1.3} y2={1.5} fill="#f59e0b" fillOpacity={0.1} />
              <ReferenceArea y1={1.5} y2={2.5} fill="#ef4444" fillOpacity={0.1} />
              <ReferenceLine y={1.3} stroke="#f59e0b" strokeDasharray="5 5" />
              <ReferenceLine y={1.5} stroke="#ef4444" strokeDasharray="5 5" />
              <Line type="monotone" dataKey="acwr" stroke="#2563eb" strokeWidth={2.5} dot={false} name="ACWR" />
              <Tooltip />
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Training Calendar Heatmap */}
      {id && <TrainingCalendarHeatmap athleteId={id} />}

      {/* Two Column: RSSI + Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RSSI */}
        {rssiData && (
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Brain className="w-4 h-4" /> RSSI 恢复-应激状态指数
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-4xl font-bold" style={{ color: riskColor(rssiData.risk_level) }}>
                  {rssiData.rssi_score.toFixed(1)}
                </div>
                <div className="text-xs text-slate-500 mt-1">总分 / 100</div>
              </div>
              <div className="px-4 py-2 rounded-lg text-sm font-bold text-white" style={{ background: riskColor(rssiData.risk_level) }}>
                {rssiData.risk_level}
              </div>
            </div>
            {[
              { label: 'ACWR 负荷比 (25分)', val: rssiData.acwr_component, max: 25, color: 'bg-blue-500' },
              { label: '晨起心率 (25分)', val: rssiData.heart_rate_component, max: 25, color: 'bg-red-500' },
              { label: 'HRV 心率变异性 (25分)', val: rssiData.hrv_component, max: 25, color: 'bg-purple-500' },
              { label: '主观疲劳 (15分)', val: rssiData.fatigue_component, max: 15, color: 'bg-amber-500' },
              { label: '体能表现 (10分)', val: rssiData.performance_component, max: 10, color: 'bg-emerald-500' },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>{item.label}</span>
                  <span className="font-mono">{item.val.toFixed(1)}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className={`h-full ${item.color} rounded-full`} style={{ width: `${(item.val / item.max) * 100}%` }} />
                </div>
              </div>
            ))}
            {rssiData.warnings?.length > 0 && (
              <div className="p-3 rounded-lg bg-red-50 space-y-1">
                {rssiData.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-red-700 flex items-start gap-1">
                    <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" /> {w}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Training Recommendations */}
        {recommendation && (
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Zap className="w-4 h-4" /> 个性化训练建议
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed">{recommendation.summary}</p>
            {recommendation.warnings?.length > 0 && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 space-y-1">
                {recommendation.warnings.map((w, i) => (
                  <p key={i} className="text-sm text-red-700 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {w}
                  </p>
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-blue-50"><div className="text-xs text-blue-500 mb-1">负荷调整</div><p className="text-sm text-blue-800">{recommendation.load_adjustment}</p></div>
              <div className="p-3 rounded-lg bg-green-50"><div className="text-xs text-green-500 mb-1">强度</div><p className="text-sm text-green-800">{recommendation.intensity_recommendation}</p></div>
              <div className="p-3 rounded-lg bg-amber-50"><div className="text-xs text-amber-500 mb-1">容量</div><p className="text-sm text-amber-800">{recommendation.volume_recommendation}</p></div>
              <div className="p-3 rounded-lg bg-purple-50"><div className="text-xs text-purple-500 mb-1">频次</div><p className="text-sm text-purple-800">{recommendation.frequency_recommendation}</p></div>
            </div>
            {recommendation.weekly_template?.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 font-medium">周训练模板</div>
                {recommendation.weekly_template.map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50">
                    <div className="w-12 h-10 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold text-xs shrink-0">{s.day?.slice(0, 2) || i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-800">{s.session_name}</div>
                      <div className="text-xs text-slate-500">{s.training_type} · {s.duration_min}分钟 · RPE {s.rpe_target} · {s.load_pct}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Competition Calendar + Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          {id && <CompetitionCalendar athleteId={id} />}
        </div>
        <div className="lg:col-span-2 space-y-6">
          {id && <HRVSleepTrend athleteId={id} />}
          {id && <TrainingLoadDistribution athleteId={id} />}
        </div>
      </div>

      {/* Performance Comparisons */}
      {comparisons.length > 0 && (
        <div className="card space-y-4">
          <h3 className="text-sm font-semibold text-slate-700">体能测试变化</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 px-3">指标</th>
                  <th className="text-center py-2 px-3">当前</th>
                  <th className="text-center py-2 px-3">之前</th>
                  <th className="text-center py-2 px-3">基线</th>
                  <th className="text-center py-2 px-3">变化</th>
                  <th className="text-center py-2 px-3">判定</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((c: any, i: number) => (
                  <tr key={i} className="border-b border-slate-100">
                    <td className="py-2.5 px-3 font-medium">{c.metric}</td>
                    <td className="py-2.5 px-3 text-center font-bold">{c.current_value}</td>
                    <td className="py-2.5 px-3 text-center">{c.previous_value}</td>
                    <td className="py-2.5 px-3 text-center">{c.baseline_value}</td>
                    <td className={`py-2.5 px-3 text-center font-mono font-bold ${c.change_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {c.change_pct > 0 ? '+' : ''}{c.change_pct}%
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded ${c.is_significant ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                        {c.interpretation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Period Comparison */}
      <div className="card space-y-4">
        <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> 同期对比
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">A期开始</label>
            <input type="date" value={periodAStart} onChange={e => setPeriodAStart(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">A期结束</label>
            <input type="date" value={periodAEnd} onChange={e => setPeriodAEnd(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">B期开始</label>
            <input type="date" value={periodBStart} onChange={e => setPeriodBStart(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">B期结束</label>
            <input type="date" value={periodBEnd} onChange={e => setPeriodBEnd(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
        </div>
        <button onClick={handleCompare} className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600">开始对比</button>
        {comparisonMode && comparisonData && (
          <div className="space-y-4 mt-4">
            <h4 className="text-sm font-medium text-slate-600">ACWR 趋势对比</h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={[
                { name: 'A期', avgAcwr: comparisonData.aAcwr.length ? comparisonData.aAcwr.reduce((s: number, x: any) => s + x.acwr, 0) / comparisonData.aAcwr.length : 0 },
                { name: 'B期', avgAcwr: comparisonData.bAcwr.length ? comparisonData.bAcwr.reduce((s: number, x: any) => s + x.acwr, 0) / comparisonData.bAcwr.length : 0 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="avgAcwr" fill="#2563eb" name="平均 ACWR" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
