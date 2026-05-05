import type {
  Athlete, AthleteRiskStatus, DashboardOverview, DailyReadiness,
  ExerciseLibrary, PlannedSession, PlannedExercise,
  CoachComment, InjuryRecord, InjuryRestriction,
  TeamGroup, PeriodizationTemplate,
  RadarChartData, TeamHeatmapEntry, TeamHeatmapResponse
} from '../services/api';

export const mockAthletes: (Athlete & Partial<AthleteRiskStatus> & { team_group?: string })[] = [
  { id: '1', name: '张伟', date_of_birth: '2000-03-15', gender: '男', sport: '篮球', position_or_event: '前锋', training_years: 5, latest_acwr: 1.52, acwr_risk_zone: '高风险区', rssi_score: 62.5, rssi_risk_level: '功能性过度训练', active_alerts: 3, team_group: '主力组' },
  { id: '2', name: '李娜', date_of_birth: '2002-07-22', gender: '女', sport: '游泳', position_or_event: '自由泳100m', training_years: 4, latest_acwr: 1.38, acwr_risk_zone: '谨慎区', rssi_score: 42.0, rssi_risk_level: '适应性训练', active_alerts: 2, team_group: '主力组' },
  { id: '3', name: '王强', date_of_birth: '2001-11-08', gender: '男', sport: '足球', position_or_event: '中场', training_years: 6, latest_acwr: 1.05, acwr_risk_zone: '安全区', rssi_score: 18.5, rssi_risk_level: '正常', active_alerts: 0, team_group: '主力组' },
  { id: '4', name: '赵芳', date_of_birth: '2003-01-30', gender: '女', sport: '田径', position_or_event: '短跑100m', training_years: 3, latest_acwr: 1.45, acwr_risk_zone: '谨慎区', rssi_score: 51.2, rssi_risk_level: '功能性过度训练', active_alerts: 2, team_group: '主力组' },
  { id: '5', name: '刘洋', date_of_birth: '1999-09-12', gender: '男', sport: '篮球', position_or_event: '中锋', training_years: 7, latest_acwr: 1.61, acwr_risk_zone: '高风险区', rssi_score: 74.8, rssi_risk_level: '非功能性过度训练', active_alerts: 5, team_group: '主力组' },
  { id: '6', name: '陈雪', date_of_birth: '2004-05-18', gender: '女', sport: '游泳', position_or_event: '蝶泳200m', training_years: 2, latest_acwr: 0.95, acwr_risk_zone: '安全区', rssi_score: 15.2, rssi_risk_level: '正常', active_alerts: 0, team_group: '青年组' },
  { id: '7', name: '周磊', date_of_birth: '2000-12-03', gender: '男', sport: '足球', position_or_event: '后卫', training_years: 5, latest_acwr: 1.18, acwr_risk_zone: '安全区', rssi_score: 22.1, rssi_risk_level: '正常', active_alerts: 1, team_group: '主力组' },
  { id: '8', name: '吴敏', date_of_birth: '2001-08-25', gender: '女', sport: '田径', position_or_event: '跳远', training_years: 4, latest_acwr: 1.33, acwr_risk_zone: '谨慎区', rssi_score: 35.7, rssi_risk_level: '适应性训练', active_alerts: 1, team_group: '康复组' },
  { id: '9', name: '郑浩', date_of_birth: '2005-02-14', gender: '男', sport: '篮球', position_or_event: '后卫', training_years: 1, latest_acwr: 1.22, acwr_risk_zone: '安全区', rssi_score: 18.9, rssi_risk_level: '正常', active_alerts: 0, team_group: '青年组' },
  { id: '10', name: '孙悦', date_of_birth: '2003-04-20', gender: '女', sport: '游泳', position_or_event: '仰泳100m', training_years: 3, latest_acwr: 1.08, acwr_risk_zone: '安全区', rssi_score: 12.4, rssi_risk_level: '正常', active_alerts: 0, team_group: '青年组' },
];

export const mockExerciseLibrary: ExerciseLibrary[] = [
  { id: 'e1', name: '深蹲', category: '力量', description: '杠铃后蹲，主要锻炼股四头肌和臀大肌', preset_params: { weight_kg: 80, reps: 8, sets: 4, rest_seconds: 120, rpe: 7 } },
  { id: 'e2', name: '卧推', category: '力量', description: '杠铃平躺卧推，锻炼胸大肌和肱三头肌', preset_params: { weight_kg: 60, reps: 8, sets: 4, rest_seconds: 90, rpe: 7 } },
  { id: 'e3', name: '硬拉', category: '力量', description: '传统硬拉，锻炼背部链肌群', preset_params: { weight_kg: 100, reps: 5, sets: 3, rest_seconds: 150, rpe: 8 } },
  { id: 'e4', name: '引体向上', category: '力量', description: '正手引体向上，锻炼背阔肌和肱二头肌', preset_params: { weight_kg: 0, reps: 10, sets: 3, rest_seconds: 60, rpe: 7 } },
  { id: 'e5', name: '哑铃推举', category: '力量', description: '坐姿哑铃肩推', preset_params: { weight_kg: 20, reps: 10, sets: 3, rest_seconds: 60, rpe: 6 } },
  { id: 'e6', name: '杠铃划船', category: '力量', description: '俯身杠铃划船', preset_params: { weight_kg: 60, reps: 8, sets: 4, rest_seconds: 90, rpe: 7 } },
  { id: 'e7', name: '保加利亚分腿蹲', category: '力量', description: '单腿分腿蹲，改善下肢不平衡', preset_params: { weight_kg: 20, reps: 10, sets: 3, rest_seconds: 60, rpe: 7 } },
  { id: 'e8', name: '俯卧撑', category: '力量', description: '标准俯卧撑', preset_params: { weight_kg: 0, reps: 20, sets: 3, rest_seconds: 45, rpe: 5 } },
  { id: 'e9', name: '400m间歇跑', category: '耐力', description: '400米间歇训练，提升最大摄氧量', preset_params: { weight_kg: 0, reps: 8, sets: 8, rest_seconds: 90, rpe: 8 } },
  { id: 'e10', name: '5000m匀速跑', category: '耐力', description: '5公里有氧基础训练', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 5 } },
  { id: 'e11', name: '游泳2000m', category: '耐力', description: '中等强度自由泳巡航', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 6 } },
  { id: 'e12', name: '自行车40km', category: '耐力', description: '公路自行车有氧巡航', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 5 } },
  { id: 'e13', name: '划船机2000m', category: '耐力', description: 'Concept2划船机计时训练', preset_params: { weight_kg: 0, reps: 3, sets: 3, rest_seconds: 180, rpe: 7 } },
  { id: 'e14', name: '30m冲刺', category: '速度', description: '30米直线加速跑', preset_params: { weight_kg: 0, reps: 6, sets: 2, rest_seconds: 120, rpe: 9 } },
  { id: 'e15', name: 'T型灵敏测试', category: '速度', description: '多方向灵敏性训练', preset_params: { weight_kg: 0, reps: 4, sets: 3, rest_seconds: 60, rpe: 7 } },
  { id: 'e16', name: '跳箱', category: '速度', description: '爆发力跳箱训练', preset_params: { weight_kg: 0, reps: 6, sets: 4, rest_seconds: 90, rpe: 7 } },
  { id: 'e17', name: '折返跑', category: '速度', description: '20m折返，提升转向速度', preset_params: { weight_kg: 0, reps: 5, sets: 3, rest_seconds: 90, rpe: 8 } },
  { id: 'e18', name: '投篮训练', category: '技战术', description: '定点跳投 + 移动接球投篮', preset_params: { weight_kg: 0, reps: 50, sets: 3, rest_seconds: 30, rpe: 6 } },
  { id: 'e19', name: '传接球训练', category: '技战术', description: '双人传接球配合训练', preset_params: { weight_kg: 0, reps: 20, sets: 3, rest_seconds: 30, rpe: 5 } },
  { id: 'e20', name: '战术跑位', category: '技战术', description: '半场5v5战术演练', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 7 } },
  { id: 'e21', name: '出发与转身', category: '技战术', description: '跳发+转身技术练习', preset_params: { weight_kg: 0, reps: 15, sets: 2, rest_seconds: 45, rpe: 6 } },
  { id: 'e22', name: '静态拉伸', category: '柔韧', description: '全身主要肌群静态拉伸', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 2 } },
  { id: 'e23', name: '泡沫轴放松', category: '柔韧', description: '自筋膜松解', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 2 } },
  { id: 'e24', name: '瑜伽', category: '柔韧', description: '运动瑜伽恢复序列', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 3 } },
  { id: 'e25', name: '高翻', category: '力量', description: '奥林匹克举重高翻', preset_params: { weight_kg: 60, reps: 3, sets: 5, rest_seconds: 120, rpe: 8 } },
  { id: 'e26', name: '抓举', category: '力量', description: '宽握抓举', preset_params: { weight_kg: 45, reps: 3, sets: 5, rest_seconds: 120, rpe: 8 } },
  { id: 'e27', name: '药球砸地', category: '力量', description: '爆发力药球过顶砸地', preset_params: { weight_kg: 8, reps: 10, sets: 3, rest_seconds: 45, rpe: 7 } },
  { id: 'e28', name: '战绳', category: '耐力', description: '战绳波浪训练', preset_params: { weight_kg: 0, reps: 1, sets: 4, rest_seconds: 60, rpe: 8 } },
  { id: 'e29', name: '敏捷梯', category: '速度', description: '敏捷梯步伐训练', preset_params: { weight_kg: 0, reps: 4, sets: 3, rest_seconds: 45, rpe: 5 } },
  { id: 'e30', name: '实战对抗', category: '技战术', description: '全场比赛', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 9 } },
  { id: 'e31', name: '水中康复', category: '混合', description: '浅水区康复训练', preset_params: { weight_kg: 0, reps: 1, sets: 1, rest_seconds: 0, rpe: 3 } },
  { id: 'e32', name: '核心训练', category: '混合', description: '平板支撑+卷腹+俄罗斯转体组合', preset_params: { weight_kg: 0, reps: 15, sets: 3, rest_seconds: 30, rpe: 6 } },
  // 羽毛球-技战术
  { id: 'b1', name: '高远球', category: '羽毛球-技战术', description: '正手高远球技术练习', preset_params: { duration_min: 15, target_rpe: 5, reps: 1, sets: 1, rest_seconds: 0 } },
  { id: 'b2', name: '杀球', category: '羽毛球-技战术', description: '正手杀球技术练习', preset_params: { target_reps: 30, target_rpe: 7, rest_seconds: 30, reps: 30, sets: 1 } },
  { id: 'b3', name: '吊球', category: '羽毛球-技战术', description: '正手吊球技术练习', preset_params: { target_reps: 30, target_rpe: 5, rest_seconds: 0, reps: 30, sets: 1 } },
  { id: 'b4', name: '平高球', category: '羽毛球-技战术', description: '平高压迫球技术练习', preset_params: { target_reps: 30, target_rpe: 6, rest_seconds: 0, reps: 30, sets: 1 } },
  { id: 'b5', name: '正手抽球', category: '羽毛球-技战术', description: '正手抽球技术练习', preset_params: { target_reps: 25, target_rpe: 6, rest_seconds: 0, reps: 25, sets: 1 } },
  { id: 'b6', name: '反手抽球', category: '羽毛球-技战术', description: '反手抽球技术练习', preset_params: { target_reps: 25, target_rpe: 6, rest_seconds: 0, reps: 25, sets: 1 } },
  { id: 'b7', name: '挡网', category: '羽毛球-技战术', description: '网前挡网技术练习', preset_params: { target_reps: 20, target_rpe: 4, rest_seconds: 0, reps: 20, sets: 1 } },
  { id: 'b8', name: '搓球', category: '羽毛球-技战术', description: '网前搓球技术练习', preset_params: { target_reps: 25, target_rpe: 4, rest_seconds: 0, reps: 25, sets: 1 } },
  { id: 'b9', name: '推球', category: '羽毛球-技战术', description: '网前推球技术练习', preset_params: { target_reps: 25, target_rpe: 5, rest_seconds: 0, reps: 25, sets: 1 } },
  { id: 'b10', name: '勾对角', category: '羽毛球-技战术', description: '网前勾对角技术练习', preset_params: { target_reps: 20, target_rpe: 5, rest_seconds: 0, reps: 20, sets: 1 } },
  { id: 'b11', name: '挑球', category: '羽毛球-技战术', description: '网前挑球技术练习', preset_params: { target_reps: 25, target_rpe: 5, rest_seconds: 0, reps: 25, sets: 1 } },
  { id: 'b12', name: '正手发高远球', category: '羽毛球-技战术', description: '正手发高远球技术练习', preset_params: { target_reps: 20, target_rpe: 3, rest_seconds: 0, reps: 20, sets: 1 } },
  { id: 'b13', name: '反手发网前球', category: '羽毛球-技战术', description: '反手发网前球技术练习', preset_params: { target_reps: 20, target_rpe: 3, rest_seconds: 0, reps: 20, sets: 1 } },
  { id: 'b14', name: '前后场连贯步法', category: '羽毛球-技战术', description: '前后场连贯步法训练', preset_params: { duration_min: 15, target_rpe: 7, reps: 1, sets: 1, rest_seconds: 0 } },
  { id: 'b15', name: '左右摸边', category: '羽毛球-技战术', description: '左右摸边移动训练', preset_params: { duration_min: 10, target_rpe: 6, reps: 1, sets: 1, rest_seconds: 0 } },
];

export const badmintonTests = [
  '羽毛球专项折返跑', '垂直纵跳', '握力_左', '握力_右',
  'Y平衡_左', 'Y平衡_右', '肩关节活动度_左', '肩关节活动度_右',
];

export const mockTeamGroups: TeamGroup[] = [
  { id: 'g1', name: '主力组', member_count: 6 },
  { id: 'g2', name: '康复组', member_count: 2 },
  { id: 'g3', name: '青年组', member_count: 3 },
];

function genDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().split('T')[0];
}

function genToday(): string {
  return new Date().toISOString().split('T')[0];
}

export const mockDailyReadiness: DailyReadiness[] = [];
// Generate 7 days for athletes 1, 2, 5
for (const aid of ['1', '2', '5']) {
  for (let d = 0; d < 7; d++) {
    const date = genDate(d);
    const athlete = mockAthletes.find(a => a.id === aid);
    const isHighRisk = athlete?.rssi_risk_level === '非功能性过度训练';
    const sleep = isHighRisk ? Math.floor(Math.random() * 2) + 2 : Math.floor(Math.random() * 3) + 3;
    const soreness = isHighRisk ? Math.floor(Math.random() * 2) + 3 : Math.floor(Math.random() * 3) + 1;
    const fatigue = isHighRisk ? Math.floor(Math.random() * 2) + 4 : Math.floor(Math.random() * 3) + 1;
    const stress = isHighRisk ? Math.floor(Math.random() * 2) + 3 : Math.floor(Math.random() * 3) + 2;
    const avg = (sleep + (6 - soreness) + (6 - fatigue) + (6 - stress)) / 16;
    mockDailyReadiness.push({
      id: `r-${aid}-${d}`,
      athlete_id: aid,
      record_date: date,
      sleep_quality: sleep,
      muscle_soreness: soreness,
      fatigue_level: fatigue,
      stress_motivation: stress,
      readiness_color: avg > 0.65 ? 'green' : avg > 0.4 ? 'yellow' : 'red',
    });
  }
}

export const mockPlannedSessions: PlannedSession[] = [
  {
    id: 'ps1', athlete_id: '1', plan_date: genToday(), session_name: '下肢力量 + 耐力', training_type: '力量',
    exercises: [
      { id: 'pe1', exercise: mockExerciseLibrary[0], target_weight_kg: 90, target_reps: 6, target_sets: 4, rest_seconds: 120, target_rpe: 8 },
      { id: 'pe2', exercise: mockExerciseLibrary[6], target_weight_kg: 25, target_reps: 8, target_sets: 3, rest_seconds: 60, target_rpe: 7 },
      { id: 'pe3', exercise: mockExerciseLibrary[13], target_weight_kg: 0, target_reps: 3, target_sets: 3, rest_seconds: 180, target_rpe: 7 },
    ],
  },
  {
    id: 'ps2', athlete_id: '5', plan_date: genToday(), session_name: '上肢力量 + 技战术', training_type: '混合',
    exercises: [
      { id: 'pe4', exercise: mockExerciseLibrary[1], target_weight_kg: 70, target_reps: 8, target_sets: 4, rest_seconds: 90, target_rpe: 7 },
      { id: 'pe5', exercise: mockExerciseLibrary[3], target_weight_kg: 0, target_reps: 12, target_sets: 3, rest_seconds: 60, target_rpe: 7 },
      { id: 'pe6', exercise: mockExerciseLibrary[17], target_weight_kg: 0, target_reps: 60, target_sets: 3, rest_seconds: 30, target_rpe: 6 },
    ],
  },
  {
    id: 'ps3', athlete_id: '3', plan_date: genDate(1), session_name: '有氧耐力日', training_type: '耐力',
    exercises: [
      { id: 'pe7', exercise: mockExerciseLibrary[9], target_weight_kg: 0, target_reps: 1, target_sets: 1, rest_seconds: 0, target_rpe: 5 },
      { id: 'pe8', exercise: mockExerciseLibrary[21], target_weight_kg: 0, target_reps: 1, target_sets: 1, rest_seconds: 0, target_rpe: 2 },
    ],
  },
  {
    id: 'ps4', athlete_id: '4', plan_date: genDate(1), session_name: '速度+爆发日', training_type: '速度',
    exercises: [
      { id: 'pe9', exercise: mockExerciseLibrary[13], target_weight_kg: 0, target_reps: 8, target_sets: 2, rest_seconds: 120, target_rpe: 9 },
      { id: 'pe10', exercise: mockExerciseLibrary[15], target_weight_kg: 0, target_reps: 6, target_sets: 4, rest_seconds: 90, target_rpe: 7 },
      { id: 'pe11', exercise: mockExerciseLibrary[28], target_weight_kg: 0, target_reps: 4, target_sets: 3, rest_seconds: 45, target_rpe: 5 },
    ],
  },
  {
    id: 'ps5', athlete_id: '8', plan_date: genToday(), session_name: '康复训练日', training_type: '柔韧',
    exercises: [
      { id: 'pe12', exercise: mockExerciseLibrary[30], target_weight_kg: 0, target_reps: 1, target_sets: 1, rest_seconds: 0, target_rpe: 3 },
      { id: 'pe13', exercise: mockExerciseLibrary[21], target_weight_kg: 0, target_reps: 1, target_sets: 1, rest_seconds: 0, target_rpe: 2 },
      { id: 'pe14', exercise: mockExerciseLibrary[22], target_weight_kg: 0, target_reps: 1, target_sets: 1, rest_seconds: 0, target_rpe: 2 },
    ],
  },
];

export const mockInjuryRecords: InjuryRecord[] = [
  {
    id: 'inj1', diagnosis: '左踝关节扭伤 (Grade 2)', injury_date: genDate(30), expected_recovery_weeks: 6,
    status: '康复中', body_part: '左踝', severity: '中度',
    restrictions: [
      { id: 'ir1', restriction_type: '禁止跳跃', restriction_detail: '禁止所有跳跃类训练（跳箱、跳跃冲刺等）', exercise_name_pattern: '跳箱' },
      { id: 'ir2', restriction_type: '负荷限制', restriction_detail: '左下肢负重不超过体重的50%', exercise_name_pattern: '深蹲|分腿蹲' },
    ],
  },
  {
    id: 'inj2', diagnosis: '右肩盂唇撕裂', injury_date: genDate(60), expected_recovery_weeks: 12,
    status: '术后康复', body_part: '右肩', severity: '严重',
    restrictions: [
      { id: 'ir3', restriction_type: '禁止上肢推举', restriction_detail: '禁止卧推、推举等上肢推类动作', exercise_name_pattern: '卧推|推举|抓举|高翻' },
      { id: 'ir4', restriction_type: '限制活动范围', restriction_detail: '右肩屈曲不超过90°', exercise_name_pattern: '引体向上' },
    ],
  },
  {
    id: 'inj3', diagnosis: '腰椎间盘突出 (L4-L5)', injury_date: genDate(90), expected_recovery_weeks: 8,
    status: '康复中', body_part: '腰椎', severity: '中度',
    restrictions: [
      { id: 'ir5', restriction_type: '禁止脊柱屈曲负荷', restriction_detail: '禁止硬拉、划船等脊柱屈曲负荷动作', exercise_name_pattern: '硬拉|划船|高翻|抓举' },
    ],
  },
];

export const mockCoachComments: CoachComment[] = [
  { id: 'c1', athlete_id: '1', comment_text: '下肢力量提升明显，深蹲动作模式有改善。注意膝内扣问题，下周增加臀中肌激活训练。', rating: 8, created_by_name: '王教练', created_at: genDate(3) },
  { id: 'c2', athlete_id: '1', comment_text: 'RSSI偏高，本周训练表现不及预期，需要增加恢复时间。', rating: 5, created_by_name: '李体能师', created_at: genDate(1) },
  { id: 'c3', athlete_id: '5', comment_text: '过度训练风险极高！连续3天晨脉升高。强制减量周——本周只允许低强度游泳和拉伸。', rating: 3, created_by_name: '王教练', created_at: genDate(2) },
  { id: 'c4', athlete_id: '2', comment_text: '自由泳划频稳定，转身技术改进后成绩明显提升。继续按当前计划执行。', rating: 9, created_by_name: '陈教练', created_at: genDate(5) },
];

export const mockTemplates: PeriodizationTemplate[] = [
  { id: 't1', name: '篮球季前力量期', template_type: '力量', cycle_phase: '准备期', description: '针对篮球运动员的力量基础建立阶段，包含深蹲、卧推、硬拉等核心力量训练' },
  { id: 't2', name: '游泳赛前减量模板', template_type: '混合', cycle_phase: '比赛期', description: '赛前7天减量方案，强度维持、容量递减，确保运动员以最佳状态参赛' },
  { id: 't3', name: '足球间歇耐力模板', template_type: '耐力', cycle_phase: '准备期', description: '模拟足球比赛强度的高强度间歇训练，提升最大摄氧量和恢复能力' },
  // 羽毛球专项周期化模板
  { id: 't4', name: '羽毛球休赛期基础训练', template_type: '混合', cycle_phase: '休赛期', description: '4周基础力量+技术动作固化：深蹲、核心训练、高远球、正反手抽球、前后场步法' },
  { id: 't5', name: '羽毛球备赛期专项强化', template_type: '技战术', cycle_phase: '备赛期', description: '6周专项强度提升：杀球、吊球、平高球+速度耐力训练，强化比赛节奏' },
  { id: 't6', name: '羽毛球比赛期维持减量', template_type: '混合', cycle_phase: '比赛期', description: '2周维持+减量：轻技术练习+低强度有氧，确保最佳竞技状态' },
  { id: 't7', name: '羽毛球过渡期恢复', template_type: '柔韧', cycle_phase: '过渡期', description: '2周恢复+交叉训练：拉伸、游泳、瑜伽，消除疲劳避免过度训练' },
];

export const mockRadarData: Record<string, RadarChartData> = {
  '1': {
    labels: ['最大力量', '爆发力', '速度', '敏捷性', '有氧耐力', '柔韧性', '体成分', '心理韧性'],
    current: [75, 62, 58, 70, 55, 40, 65, 72],
    best: [85, 72, 68, 78, 65, 50, 70, 80],
    normLow: [40, 35, 30, 35, 30, 25, 40, 35],
    normHigh: [90, 85, 80, 85, 80, 75, 85, 90],
    weaknesses: ['有氧耐力', '柔韧性'],
  },
  '5': {
    labels: ['最大力量', '爆发力', '速度', '敏捷性', '有氧耐力', '柔韧性', '体成分', '心理韧性'],
    current: [82, 75, 60, 55, 40, 35, 70, 60],
    best: [90, 80, 65, 60, 50, 45, 75, 70],
    normLow: [40, 35, 30, 35, 30, 25, 40, 35],
    normHigh: [90, 85, 80, 85, 80, 75, 85, 90],
    weaknesses: ['有氧耐力', '柔韧性', '敏捷性'],
  },
};

export const mockTeamHeatmap: Record<string, TeamHeatmapResponse> = {
  'g1': {
    group_name: '主力组',
    avg_acwr: 1.31,
    at_risk_pct: 33.3,
    entries: mockAthletes.filter(a => a.team_group === '主力组').map(a => ({
      athlete_name: a.name,
      acwr: a.latest_acwr || 1.0,
      acwr_color: (a.latest_acwr || 1.0) > 1.5 ? 'red' : (a.latest_acwr || 1.0) > 1.3 ? 'yellow' : 'green',
      rssi_score: a.rssi_score || 0,
      rssi_level: a.rssi_risk_level || '正常',
      recent_load: [550, 620, 580, 610, 590, 640, 600][parseInt(a.id) % 7],
      perf_trend: (a.latest_acwr || 1.0) > 1.3 ? '下降' : '稳定',
      active_injuries: a.active_alerts || 0,
      athlete_id: a.id,
    })),
  },
  'g2': {
    group_name: '康复组',
    avg_acwr: 0.88,
    at_risk_pct: 50.0,
    entries: mockAthletes.filter(a => a.team_group === '康复组').map(a => ({
      athlete_name: a.name,
      acwr: a.latest_acwr || 1.0,
      acwr_color: (a.latest_acwr || 1.0) > 1.5 ? 'red' : (a.latest_acwr || 1.0) > 1.3 ? 'yellow' : 'green',
      rssi_score: a.rssi_score || 0,
      rssi_level: a.rssi_risk_level || '正常',
      recent_load: [200, 180, 220, 190, 210, 195, 205][parseInt(a.id) % 7],
      perf_trend: '恢复中',
      active_injuries: a.active_alerts || 0,
      athlete_id: a.id,
    })),
  },
  'g3': {
    group_name: '青年组',
    avg_acwr: 1.08,
    at_risk_pct: 0,
    entries: mockAthletes.filter(a => a.team_group === '青年组').map(a => ({
      athlete_name: a.name,
      acwr: a.latest_acwr || 1.0,
      acwr_color: (a.latest_acwr || 1.0) > 1.5 ? 'red' : (a.latest_acwr || 1.0) > 1.3 ? 'yellow' : 'green',
      rssi_score: a.rssi_score || 0,
      rssi_level: a.rssi_risk_level || '正常',
      recent_load: [350, 370, 360, 380, 355, 365, 375][parseInt(a.id) % 7],
      perf_trend: '上升',
      active_injuries: a.active_alerts || 0,
      athlete_id: a.id,
    })),
  },
};
