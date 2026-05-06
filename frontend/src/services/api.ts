// AthleteIQ - API Service Layer
const API_BASE = '/api';

export interface Athlete {
  id: string;
  name: string;
  date_of_birth: string;
  gender: string;
  sport: string;
  position_or_event?: string;
  training_years?: number;
}

export interface TrainingLog {
  id: string;
  athlete_id: string;
  training_date: string;
  duration_minutes: number;
  rpe: number;
  training_type: string;
  session_load: number;
  cycle_phase?: string;
  description?: string;
  coach_notes?: string;
  tags?: string[];
  source?: string;
}

export interface DashboardOverview {
  total_athletes: number;
  athletes_at_risk: number;
  active_alerts: number;
  avg_team_acwr: number;
  alerts_by_severity: Record<string, number>;
  athlete_statuses: AthleteRiskStatus[];
}

export interface AthleteRiskStatus {
  athlete_id: string;
  athlete_name: string;
  sport: string;
  latest_acwr: number;
  acwr_risk_zone: string;
  rssi_score: number;
  rssi_risk_level: string;
  active_alerts: number;
}

export interface ACWRTimeSeries {
  dates: string[];
  acute_load: number[];
  chronic_load: number[];
  acwr: number[];
  risk_zone_thresholds: Record<string, number>;
}

export interface RSSIDetail {
  date: string;
  rssi_score: number;
  risk_level: string;
  acwr_component: number;
  heart_rate_component: number;
  hrv_component: number;
  fatigue_component: number;
  performance_component: number;
  recommendations: string[];
  warnings: string[];
}

export interface TrainingRecommendationResponse {
  summary: string;
  load_adjustment: string;
  intensity_recommendation: string;
  volume_recommendation: string;
  frequency_recommendation: string;
  priority_areas: string[];
  recovery_strategies: string[];
  weekly_template: WeeklySession[];
  warnings: string[];
}

export interface WeeklySession {
  day: string;
  session_name: string;
  training_type: string;
  duration_min: number;
  rpe_target: number;
  load_pct: string;
  focus_notes?: string;
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Dashboard
export const getDashboardOverview = () =>
  fetchJSON<DashboardOverview>('/dashboard/overview');

// Athletes
export const getAthletes = (sport?: string) =>
  fetchJSON<Athlete[]>(`/athletes/${sport ? `?sport=${sport}` : ''}`);

export const getAthlete = (id: string) =>
  fetchJSON<Athlete>(`/athletes/${id}`);

// Training
export const getACWRTimeSeries = (athleteId: string, days = 90) =>
  fetchJSON<ACWRTimeSeries>(`/training/log/${athleteId}/acwr?days=${days}`);

export const createTrainingLog = (data: any) =>
  fetchJSON('/training/log', { method: 'POST', body: JSON.stringify(data) });

// RSSI
export const getRSSI = (athleteId: string) =>
  fetchJSON<RSSIDetail>(`/dashboard/athlete/${athleteId}/rssi`);

// Recommendations
export const getTrainingRecommendation = (athleteId: string) =>
  fetchJSON<TrainingRecommendationResponse>(`/dashboard/athlete/${athleteId}/recommendation`);

// Performance
export const getPerformanceComparison = (athleteId: string) =>
  fetchJSON<any>(`/dashboard/athlete/${athleteId}/performance-comparison`);

// Alerts
export const getAlerts = (params?: { is_resolved?: boolean; severity?: string }) => {
  const qs = new URLSearchParams();
  if (params?.is_resolved !== undefined) qs.set('is_resolved', String(params.is_resolved));
  if (params?.severity) qs.set('severity', params.severity);
  return fetchJSON<any[]>(`/alerts?${qs.toString()}`);
};

export const getUnreadAlertCount = () =>
  fetchJSON<{ unread_count: number }>('/alerts/unread-count');

// ============================================================
// New interfaces for expanded system
// ============================================================

export interface DailyReadiness {
  id: string;
  athlete_id: string;
  record_date: string;
  sleep_quality: number;
  muscle_soreness: number;
  fatigue_level: number;
  stress_motivation: number;
  discomfort_notes?: string;
  readiness_color: string;
}

export interface ExerciseLibrary {
  id: string;
  name: string;
  category: string;
  category_l1?: string;
  category_l2?: string;
  nasm_phase?: string;
  target_muscles?: string[];
  instructions?: string;
  literature_ref?: string;
  description?: string;
  preset_params: any;
}

export interface ExerciseLibraryListResponse {
  exercises: ExerciseLibrary[];
  total: number;
}

export interface PlannedSession {
  id: string;
  athlete_id: string;
  plan_date: string;
  session_name: string;
  training_type: string;
  exercises: PlannedExercise[];
}

export interface PlannedExercise {
  id: string;
  exercise: ExerciseLibrary;
  target_weight_kg: number;
  target_reps: number;
  target_sets: number;
  rest_seconds: number;
  target_rpe: number;
}

export interface CoachComment {
  id: string;
  athlete_id: string;
  comment_text: string;
  rating: number;
  created_by_name?: string;
  created_at: string;
}

export interface InjuryRecord {
  id: string;
  diagnosis: string;
  injury_date: string;
  expected_recovery_weeks: number;
  status: string;
  body_part: string;
  severity: string;
  restrictions: InjuryRestriction[];
}

export interface InjuryRestriction {
  id: string;
  restriction_type: string;
  restriction_detail: string;
  exercise_name_pattern: string;
}

export interface TeamGroup {
  id: string;
  name: string;
  member_count: number;
}

export interface PeriodizationTemplate {
  id: string;
  name: string;
  template_type: string;
  cycle_phase: string;
  description: string;
}

export interface RadarChartData {
  labels: string[];
  current: number[];
  best: number[];
  normLow: number[];
  normHigh: number[];
  weaknesses: string[];
}

export interface TeamHeatmapEntry {
  athlete_name: string;
  acwr: number;
  acwr_color: string;
  rssi_score: number;
  rssi_level: string;
  recent_load: number;
  perf_trend: string;
  active_injuries: number;
  athlete_id: string;
}

export interface TeamHeatmapResponse {
  group_name: string;
  entries: TeamHeatmapEntry[];
  avg_acwr: number;
  at_risk_pct: number;
}

export interface SessionDeviation {
  plan_load: number;
  actual_load: number;
  deviation_pct: number;
  is_over_threshold: boolean;
}

// ============================================================
// New API functions
// ============================================================

export const submitDailyReadiness = (data: any) =>
  fetchJSON('/readiness/', { method: 'POST', body: JSON.stringify(data) });

export const getExercises = (params?: {
  category?: string;
  category_l1?: string;
  category_l2?: string;
  nasm_phase?: string;
  search?: string;
}) => {
  const qs = new URLSearchParams();
  if (params?.category) qs.set('category', params.category);
  if (params?.category_l1) qs.set('category_l1', params.category_l1);
  if (params?.category_l2) qs.set('category_l2', params.category_l2);
  if (params?.nasm_phase) qs.set('nasm_phase', params.nasm_phase);
  if (params?.search) qs.set('search', params.search);
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return fetchJSON<ExerciseLibraryListResponse>(`/exercises/${suffix}`);
};

export const createPlannedSession = (data: any) =>
  fetchJSON('/planner/sessions', { method: 'POST', body: JSON.stringify(data) });

export const getPlannedSessions = (athleteId: string, start?: string, end?: string) =>
  fetchJSON<PlannedSession[]>(`/planner/sessions?athlete_id=${athleteId}${start ? `&start=${start}` : ''}${end ? `&end=${end}` : ''}`);

export const getTodayPlan = (athleteId: string) =>
  fetchJSON<PlannedSession>(`/planner/athlete/${athleteId}/today`);

export const getCoachComments = (athleteId: string) =>
  fetchJSON<CoachComment[]>(`/coach/comments?athlete_id=${athleteId}`);

export const addCoachComment = (data: any) =>
  fetchJSON('/coach/comments', { method: 'POST', body: JSON.stringify(data) });

export const getInjuryRecords = (athleteId: string) =>
  fetchJSON<InjuryRecord[]>(`/injury/records?athlete_id=${athleteId}`);

export const getTeamGroups = () =>
  fetchJSON<TeamGroup[]>('/groups');

export const getTeamHeatmap = (groupId?: string) =>
  fetchJSON<TeamHeatmapResponse>(`/groups/${groupId || 'all'}/heatmap`);

export const getTemplates = (type?: string) =>
  fetchJSON<PeriodizationTemplate[]>(`/templates${type ? `?template_type=${type}` : ''}`);

export const getRadarData = (athleteId: string) =>
  fetchJSON<RadarChartData>(`/dashboard/athlete/${athleteId}/radar`);

export const getSessionDeviation = (sessionId: string) =>
  fetchJSON<SessionDeviation>(`/planner/sessions/${sessionId}/deviation`);

// ============================================================
// Plan vs Actual (增强版)
// ============================================================

export interface ExercisePlanVsActualItem {
  exercise_id: string;
  exercise_name: string;
  planned_sets: number | null;
  planned_reps: number | null;
  planned_rpe: number | null;
  planned_weight: number | null;
  actual_sets: number | null;
  actual_reps: number | null;
  actual_rpe: number | null;
  actual_weight: number | null;
  planned_load: number;
  actual_load: number;
  completion_pct: number;
}

export interface SessionPlanVsActualFull {
  session_id: string;
  session_name: string;
  plan_date: string;
  planned_load: number;
  actual_load: number;
  deviation_pct: number;
  completion_rate: number;
  exercises: ExercisePlanVsActualItem[];
}

export const getPlanVsActual = (sessionId: string) =>
  fetchJSON<SessionPlanVsActualFull>(`/planner/sessions/${sessionId}/plan-vs-actual`);

export const logExerciseForPlan = (sessionId: string, data: {
  planned_exercise_id: string;
  actual_sets_completed?: number;
  actual_reps_completed?: number;
  actual_rpe?: number;
  actual_duration_min?: number;
  actual_weight_kg?: number;
  notes?: string;
}) =>
  fetchJSON<{ status: string; exercise_log_id: string; training_log_id: string }>(
    `/planner/sessions/${sessionId}/log-exercise`,
    { method: 'POST', body: JSON.stringify(data) }
  );

// ============================================================
// Week Plan
// ============================================================

export interface WeekPlanDay {
  date: string;
  day_name: string;
  is_today: boolean;
  sessions: {
    id: string;
    session_name: string;
    training_type: string;
    planned_load: number;
    status: string;
  }[];
}

export interface WeekPlan {
  week_start: string;
  week_end: string;
  days: WeekPlanDay[];
}

export const getWeekPlan = (athleteId: string, weekStart?: string) =>
  fetchJSON<WeekPlan>(`/planner/sessions/week?athlete_id=${athleteId}${weekStart ? `&week_start=${weekStart}` : ''}`);

export interface PlanVsActualTrendDay {
  date: string;
  planned_load: number;
  actual_load: number;
  completion_rate: number;
}

export interface PlanVsActualTrend {
  athlete_id: string;
  days: number;
  trend: PlanVsActualTrendDay[];
}

export const getPlanVsActualTrend = (athleteId: string, days = 30) =>
  fetchJSON<PlanVsActualTrend>(`/planner/athlete/${athleteId}/plan-vs-actual-trend?days=${days}`);

// ============================================================
// Batch Create Sessions
// ============================================================

export const batchCreateSessions = (data: {
  athlete_id: string;
  start_date: string;
  end_date: string;
  weekdays?: number[];
  session_name?: string;
  training_type?: string;
  exercises: any[];
  notes?: string;
}) =>
  fetchJSON<{ sessions_created: number; session_ids: string[] }>(
    '/planner/sessions/batch-create',
    { method: 'POST', body: JSON.stringify(data) }
  );

// ============================================================
// Auto Adjust
// ============================================================

export interface ACWRStatus {
  athlete_id: string;
  athlete_name: string;
  current_acwr: number;
  acute_load_7d: number;
  chronic_load_28d: number;
  risk_zone: string;
  needs_adjustment: boolean;
  suggestion: string;
  recommended_adjustment_pct: number;
  future_sessions_count: number;
  future_total_planned_load: number;
}

export interface AdjustedSession {
  session_id: string;
  plan_date: string;
  original_load: number;
  adjusted_load: number;
  change_pct: number;
}

export interface AutoAdjustResult {
  athlete_id: string;
  adjustment_factor: number;
  sessions_adjusted: number;
  details: AdjustedSession[];
  summary: string;
}

export const getACWRStatus = (athleteId: string) =>
  fetchJSON<ACWRStatus>(`/auto-adjust/acwr/${athleteId}`);

export const autoAdjustPlan = (athleteId: string, adjustmentFactor: number, reason?: string) =>
  fetchJSON<AutoAdjustResult>(`/auto-adjust/plan/${athleteId}`, {
    method: 'POST',
    body: JSON.stringify({ athlete_id: athleteId, adjustment_factor: adjustmentFactor, reason }),
  });

// ============================================================
// Extended API functions
// ============================================================

export const createAthlete = (data: any) =>
  fetchJSON('/athletes/', { method: 'POST', body: JSON.stringify(data) });

export const updateAthlete = (id: string, data: any) =>
  fetchJSON(`/athletes/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const submitNutritionLog = (data: any) =>
  fetchJSON('/nutrition/', { method: 'POST', body: JSON.stringify(data) });

export const getNutritionHistory = (athleteId: string) =>
  fetchJSON(`/nutrition/${athleteId}`);

export const getNutritionRisk = (athleteId: string) =>
  fetchJSON(`/nutrition/${athleteId}/risk`);

export const submitMentalLog = (data: any) =>
  fetchJSON('/mental/', { method: 'POST', body: JSON.stringify(data) });

export const getMentalHistory = (athleteId: string) =>
  fetchJSON(`/mental/${athleteId}`);

export const getMentalWeeklyReport = (athleteId: string) =>
  fetchJSON(`/mental/${athleteId}/weekly-report`);

export const getAthleteReport = (athleteId: string) =>
  fetchJSON<any>(`/dashboard/athlete/${athleteId}/report`);

export const getTrainingLogs = (athleteId: string, limit = 10) =>
  fetchJSON<TrainingLog[]>(`/training/log/${athleteId}?limit=${limit}`);

export const getRiskScore = (athleteId: string) =>
  fetchJSON<any>(`/dashboard/athlete/${athleteId}/risk-score`);

export const getPeriodComparison = (athleteId: string, params: {
  period_a_start: string; period_a_end: string;
  period_b_start: string; period_b_end: string;
}) => {
  const qs = new URLSearchParams(params as any).toString();
  return fetchJSON<any>(`/dashboard/athlete/${athleteId}/period-comparison?${qs}`);
};

export const assignSessionToAthletes = (sessionId: string, athleteIds: string[]) =>
  fetchJSON(`/planner/sessions/${sessionId}/assign`, {
    method: 'POST',
    body: JSON.stringify({ athlete_ids: athleteIds }),
  });

export const createExercise = (data: any) =>
  fetchJSON<ExerciseLibrary>('/exercises/', { method: 'POST', body: JSON.stringify(data) });

export const updateExercise = (id: string, data: any) =>
  fetchJSON(`/exercises/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteExercise = (id: string) =>
  fetchJSON(`/exercises/${id}`, { method: 'DELETE' });

export const seedPresetExercises = () =>
  fetchJSON<{ status: string; count?: number }>('/exercises/seed-presets', { method: 'POST' });

export const seedRehabExercises = () =>
  fetchJSON<{ status: string; rehab_count: number; injury_links: number }>('/exercises/seed-rehab', { method: 'POST' });

export interface CategoriesResponse {
  categories_l1: { category_l1: string; count: number }[];
  categories_l2: { category_l2: string; count: number }[];
  categories_legacy: { category: string; count: number }[];
}

export const getCategories = () =>
  fetchJSON<CategoriesResponse>('/exercises/categories');

export interface InjuryLinkedExercise {
  exercise_id: string;
  name: string;
  category_l2: string;
  nasm_phase: string;
  risk_factor: string;
  priority: number;
  instructions: string;
  target_muscles: string[];
  literature_ref: string;
  preset_params: any;
}

export const getInjuryLinks = (bodyPart: string) =>
  fetchJSON<{ body_part: string; exercises: InjuryLinkedExercise[] }>(`/exercises/injury-links/${bodyPart}`);

export const addFavorite = (itemType: string, itemId: string) =>
  fetchJSON('/favorites/', { method: 'POST', body: JSON.stringify({ item_type: itemType, item_id: itemId }) });

export const removeFavorite = (itemType: string, itemId: string) =>
  fetchJSON(`/favorites/${itemType}/${itemId}`, { method: 'DELETE' });

export const getFavorites = (itemType: string) =>
  fetchJSON<any[]>(`/favorites?item_type=${itemType}`);

export const getRecents = (itemType: string) =>
  fetchJSON<any[]>(`/recents?item_type=${itemType}`);

export const markCommentRead = (commentId: string) =>
  fetchJSON(`/coach/comments/${commentId}/mark-read`, { method: 'POST' });

export const getUnreadCommentCount = (athleteId: string) =>
  fetchJSON<{ athlete_id: string; unread_count: number }>(`/coach/comments/unread-count/${athleteId}`);

export const getSportStandards = (sport: string = '篮球') =>
  fetchJSON<any>(`/dashboard/standards?sport=${sport}`);

export const getAthleteLevel = (athleteId: string) =>
  fetchJSON<any>(`/dashboard/athlete/${athleteId}/level`);

// ============================================================
// Wellness & HRV Trends
// ============================================================

export interface WellnessTrend {
  date: string;
  morning_heart_rate?: number | null;
  hrv_lnrmssd?: number | null;
  sleep_duration_hours?: number | null;
  sleep_quality?: number | null;
  fatigue_score?: number | null;
}

export const getWellnessTrends = (athleteId: string, days = 30) =>
  fetchJSON<{ athlete_id: string; days: number; trends: WellnessTrend[] }>(
    `/wellness/${athleteId}/trends?days=${days}`
  );

// ============================================================
// Training Distribution
// ============================================================

export interface TrainingDistribution {
  athlete_id: string;
  days: number;
  total_load: number;
  distribution: { type: string; total_load: number; percentage: number }[];
}

export const getTrainingDistribution = (athleteId: string, days = 90) =>
  fetchJSON<TrainingDistribution>(`/training/log/${athleteId}/distribution?days=${days}`);

// ============================================================
// Training Status
// ============================================================

export interface TrainingStatusResponse {
  athlete_id: string;
  status: string;
  color: string;
  description: string;
  recommendation: string;
  supporting_metrics: {
    acwr: number;
    rssi_score: number;
    acute_load: number;
    chronic_load: number;
    monotony: number;
  };
}

export const getTrainingStatus = (athleteId: string) =>
  fetchJSON<TrainingStatusResponse>(`/dashboard/athlete/${athleteId}/training-status`);

// ============================================================
// Load Summary (weekly volume)
// ============================================================

export interface WeeklyLoadSummary {
  athlete_id: string;
  period: string;
  total_weeks: number;
  weekly_data: {
    week_start: string;
    total_load: number;
    sessions: number;
    avg_session_load: number;
    week_over_week_change_pct: number;
  }[];
}

export const getLoadSummary = (athleteId: string, weeks = 12) =>
  fetchJSON<WeeklyLoadSummary>(`/training/log/${athleteId}/load-summary?weeks=${weeks}`);

// ============================================================
// Team Aggregate Endpoints
// ============================================================

export interface TeamWeeklySummary {
  weeks: number;
  weekly_data: { week_start: string; total_load: number }[];
}

export const getTeamWeeklySummary = (weeks = 12) =>
  fetchJSON<TeamWeeklySummary>(`/dashboard/team/weekly-summary?weeks=${weeks}`);

export interface TeamDistribution {
  days: number;
  total_load: number;
  distribution: { type: string; total_load: number; percentage: number }[];
}

export const getTeamDistribution = (days = 30) =>
  fetchJSON<TeamDistribution>(`/dashboard/team/distribution?days=${days}`);

// ============================================================
// Readiness History
// ============================================================

export const getReadinessHistory = (athleteId: string, limit = 30) =>
  fetchJSON<DailyReadiness[]>(`/readiness/${athleteId}?limit=${limit}`);

// ============================================================
// Competition Calendar
// ============================================================

export interface Competition {
  id: string;
  athlete_id: string;
  name: string;
  competition_date: string;
  location?: string;
  notes?: string;
}

export interface MonthlyRisk {
  date: string;
  injury_risk: number;
  training_load: number;
  has_competition: boolean;
  competition_name?: string;
}

export interface DailyMetricResponse {
  id: string;
  athlete_id: string;
  metric_date: string;
  training_load: number;
  injury_risk: number;
  fatigue: number;
  sleep_quality: number;
  training_content?: string;
  notes?: string;
}

export interface CompetitionRecommendation {
  competition_date: string;
  days_until: number;
  phase: string;
  phase_label: string;
  load_range: string;
  description: string;
  recommendations: string[];
}

export const getMonthlyRisks = (athleteId: string, year: number, month: number) =>
  fetchJSON<MonthlyRisk[]>(`/athletes/${athleteId}/monthly-risks?year=${year}&month=${month}`);

export const getCompetitions = (athleteId: string) =>
  fetchJSON<Competition[]>(`/athletes/${athleteId}/competitions`);

export const createCompetition = (athleteId: string, data: { name: string; competition_date: string; location?: string; notes?: string }) =>
  fetchJSON<Competition>(`/athletes/${athleteId}/competitions`, { method: 'POST', body: JSON.stringify(data) });

export const deleteCompetition = (athleteId: string, competitionId: string) =>
  fetchJSON<{ status: string }>(`/athletes/${athleteId}/competitions/${competitionId}`, { method: 'DELETE' });

export const getDailyMetrics = (athleteId: string, metricDate: string) =>
  fetchJSON<DailyMetricResponse | null>(`/athletes/${athleteId}/daily-metrics?metric_date=${metricDate}`);

export const updateDailyMetrics = (athleteId: string, metricDate: string, data: any) =>
  fetchJSON<DailyMetricResponse>(`/athletes/${athleteId}/daily-metrics?metric_date=${metricDate}`, { method: 'PUT', body: JSON.stringify(data) });

export const getCompetitionRecommendation = (athleteId: string, competitionId: string) =>
  fetchJSON<CompetitionRecommendation>(`/athletes/${athleteId}/competitions/${competitionId}/recommendation`);

export const generateTestData = (daysBefore = 45, daysAfter = 45, athletesOnly = true) =>
  fetchJSON<any>(`/data-generator/generate?days_before=${daysBefore}&days_after=${daysAfter}&athletes_only=${athletesOnly}`, { method: 'POST' });

// ============================================================
// Alerts Enhanced
// ============================================================

export interface AlertOverview {
  risk_athlete_count: number;
  active_alerts_count: number;
  alerts: RiskAlert[];
  historical_alerts: HistoricalAlert[];
}

export interface RiskAlert {
  athlete_id: string;
  athlete_name: string;
  sport: string;
  metric_name: string;
  current_value: number;
  threshold: number;
  severity: string;
  date: string;
  recommendation: string;
}

export interface HistoricalAlert {
  id: string;
  athlete_id: string;
  alert_date: string;
  alert_type: string;
  severity: string;
  current_value: string;
  recommended_action: string;
  is_read: boolean;
  is_resolved: boolean;
}

export interface AthleteAlertDetail {
  athlete_id: string;
  alerts: HistoricalAlert[];
  risk_trend_7d: RiskTrendDay[];
}

export interface RiskTrendDay {
  date: string;
  shoulder_overuse_risk: number;
  shoulder_acute_risk: number;
  knee_overuse_risk: number;
  knee_acute_risk: number;
  training_load: number;
  fatigue: number;
}

export interface AlertConfigItem {
  id: string;
  athlete_id: string;
  metric_name: string;
  threshold: number;
  severity: string;
  notify: boolean;
}

export const getAlertsOverview = (severity?: string) =>
  fetchJSON<AlertOverview>(`/alerts/overview${severity ? `?severity=${severity}` : ''}`);

export const getAthleteAlertsDetail = (athleteId: string) =>
  fetchJSON<AthleteAlertDetail>(`/alerts/athlete/${athleteId}`);

export const getAlertConfigs = (athleteId: string) =>
  fetchJSON<AlertConfigItem[]>(`/alerts/config/${athleteId}`);

export const upsertAlertConfig = (data: any) =>
  fetchJSON<AlertConfigItem>('/alerts/config', { method: 'PUT', body: JSON.stringify(data) });

export const acknowledgeAlert = (alertId: string) =>
  fetchJSON<{ status: string }>(`/alerts/acknowledge/${alertId}`, { method: 'POST' });

// ============================================================
// Recovery
// ============================================================

export interface RecoverySuggestionResponse {
  id: string;
  athlete_id: string;
  date: string;
  suggestion_text: string;
  exercises: RecoveryExercise[];
  status: string;
  completed_at?: string;
}

export interface RecoveryExercise {
  name: string;
  sets?: number;
  reps?: number;
  duration_min?: number;
  notes?: string;
  category?: string;
  completed?: boolean;
}

export const getTodayRecovery = (athleteId: string) =>
  fetchJSON<RecoverySuggestionResponse>(`/recovery/today/${athleteId}`);

export const completeSuggestion = (suggestionId: string) =>
  fetchJSON<{ status: string }>(`/recovery/complete/${suggestionId}`, { method: 'POST' });

export const getRecoveryHistory = (athleteId: string, limit = 14) =>
  fetchJSON<RecoverySuggestionResponse[]>(`/recovery/history/${athleteId}?limit=${limit}`);

// ============================================================
// Dashboard Summary
// ============================================================

export interface DashboardSummary {
  high_risk_count: number;
  avg_fatigue: number;
  unresolved_alerts: number;
  risk_trend_7d: {
    date: string;
    avg_shoulder_risk: number;
    avg_knee_risk: number;
    avg_fatigue: number;
  }[];
  top10_risks: {
    athlete_id: string;
    athlete_name: string;
    max_risk: number;
  }[];
}

export const getDashboardSummary = () =>
  fetchJSON<DashboardSummary>('/dashboard/summary');

// ============================================================
// Training Logs v2 (Enhanced)
// ============================================================

export interface DailyMetricFull extends DailyMetricResponse {
  rpe?: number;
  energy_level?: number;
  muscle_soreness?: Record<string, number>;
  technical_notes?: string;
  plan_vs_actual_diff?: number;
  completion_rate?: number;
  media_urls?: string[];
}

export interface PlanVsActual {
  scheduled_date: string;
  planned_load: number;
  actual_load: number;
  diff_pct: number;
  completion_rate: number;
  status: string;
}

export const getTrainingLogsV2 = (athleteId: string, start?: string, end?: string, limit = 90) => {
  const params = new URLSearchParams();
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  params.set('limit', String(limit));
  return fetchJSON<DailyMetricFull[]>(`/training-logs/${athleteId}?${params.toString()}`);
};

export const createOrUpdateLog = (athleteId: string, data: any) =>
  fetchJSON<DailyMetricFull>(`/training-logs/${athleteId}`, { method: 'POST', body: JSON.stringify(data) });

export const comparePlanVsActual = (athleteId: string, compareDate: string) =>
  fetchJSON<PlanVsActual>(`/training-logs/${athleteId}/compare?compare_date=${compareDate}`);

// ============================================================
// Training Templates & Assignments
// ============================================================

export interface TrainingTemplate {
  id: string;
  name: string;
  type: string;
  sport?: string;
  intensity_zone?: string;
  target_focus?: string[];
  weekly_frequency?: string;
  is_public: boolean;
  content: any;
  description?: string;
  created_at: string;
}

export interface TrainingAssignment {
  id: string;
  athlete_id: string;
  template_id?: string;
  scheduled_date: string;
  overrides?: any;
  status: string;
  actual_log_id?: string;
  notes?: string;
  template_name?: string;
  template_content?: any;
}

export const getTrainingTemplates = (type?: string, focus?: string) => {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  if (focus) params.set('focus', focus);
  return fetchJSON<TrainingTemplate[]>(`/templates?${params.toString()}`);
};

export const createTrainingTemplate = (data: any) =>
  fetchJSON<TrainingTemplate>('/templates', { method: 'POST', body: JSON.stringify(data) });

export const updateTrainingTemplate = (id: string, data: any) =>
  fetchJSON<TrainingTemplate>(`/templates/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteTrainingTemplate = (id: string) =>
  fetchJSON<{ status: string }>(`/templates/${id}`, { method: 'DELETE' });

export const createAssignment = (data: { athlete_id: string; template_id: string; scheduled_date: string; overrides?: any; notes?: string }) =>
  fetchJSON<TrainingAssignment>('/assignments', { method: 'POST', body: JSON.stringify(data) });

export const getCalendarAssignments = (athleteId: string, month?: string) => {
  const params = new URLSearchParams({ athlete_id: athleteId });
  if (month) params.set('month', month);
  return fetchJSON<TrainingAssignment[]>(`/assignments/calendar?${params.toString()}`);
};

export const completeAssignment = (assignmentId: string, actualLogId?: string) => {
  const params = new URLSearchParams();
  if (actualLogId) params.set('actual_log_id', actualLogId);
  return fetchJSON<{ status: string }>(`/assignments/${assignmentId}/complete?${params.toString()}`, { method: 'POST' });
};

// ============================================================
// Rehab Center
// ============================================================

export interface RehabExercise {
  id: string;
  name: string;
  target_body_part: string;
  nasm_phase: string;
  purpose: string;
  difficulty: number;
  equipment_needed: string[];
  instructions: string;
  common_mistakes: string;
  image_url?: string;
  video_url?: string;
}

export interface RehabPlanSummary {
  id: string;
  athlete_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  notes?: string;
  completion_pct: number;
  exercises_count: number;
  completed_count: number;
}

export interface RehabScheduleItem {
  id: string;
  plan_id: string;
  exercise_id: string;
  exercise_name: string;
  target_body_part: string;
  scheduled_date: string;
  sets: number;
  reps: string;
  rest_seconds: number;
  completed: boolean;
  completed_at?: string;
  instructions: string;
  common_mistakes: string;
  pain_before?: number;
  pain_after?: number;
}

export interface RehabProgress {
  progress_pct: number;
  total_exercises: number;
  completed_count: number;
  pain_trend: { date: string; avg_pain_before: number; avg_pain_after: number }[];
}

export const getRehabExercises = (bodyPart?: string, phase?: string) => {
  const params = new URLSearchParams();
  if (bodyPart) params.set('body_part', bodyPart);
  if (phase) params.set('phase', phase);
  return fetchJSON<RehabExercise[]>(`/rehab/exercises?${params.toString()}`);
};

export const getRehabExercise = (id: string) =>
  fetchJSON<RehabExercise>(`/rehab/exercises/${id}`);

export const getAthleteRehabPlans = (athleteId: string) =>
  fetchJSON<RehabPlanSummary[]>(`/rehab/plans/athlete/${athleteId}`);

export const createRehabPlan = (athleteId: string, name: string, startDate: string, endDate: string) =>
  fetchJSON<any>(`/rehab/plans?athlete_id=${athleteId}&name=${encodeURIComponent(name)}&start_date=${startDate}&end_date=${endDate}`, { method: 'POST' });

export const deleteRehabPlan = (planId: string) =>
  fetchJSON<{ status: string }>(`/rehab/plans/${planId}`, { method: 'DELETE' });

export const getRehabSchedule = (athleteId: string, startDate?: string, endDate?: string) => {
  const params = new URLSearchParams({ athlete_id: athleteId });
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  return fetchJSON<RehabScheduleItem[]>(`/rehab/schedule?${params.toString()}`);
};

export const completeRehabExercise = (peId: string, painBefore: number, painAfter: number) =>
  fetchJSON<{ status: string }>(`/rehab/plan-exercises/${peId}/complete?pain_before=${painBefore}&pain_after=${painAfter}`, { method: 'PUT' });

export const autoGenerateRehabPlan = (athleteId: string, targetBodyPart?: string) => {
  const params = new URLSearchParams({ athlete_id: athleteId });
  if (targetBodyPart) params.set('target_body_part', targetBodyPart);
  return fetchJSON<any>(`/rehab/generate-plan?${params.toString()}`, { method: 'POST' });
};

export const getRehabProgress = (athleteId: string, days = 30) =>
  fetchJSON<RehabProgress>(`/rehab/progress/${athleteId}?days=${days}`);

// ============================================================
// Body Data Input
// ============================================================

export const updateDailyBodyData = (athleteId: string, metricDate: string, data: any) =>
  fetchJSON<DailyMetricResponse>(`/athletes/${athleteId}/daily-metrics?metric_date=${metricDate}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

// ============================================================
// CSV Export
// ============================================================

export const exportCSV = (data: any[], filename: string) => {
  if (data.length === 0) return;
  const headers = Object.keys(data[0]);
  const rows = data.map(row => headers.map(h => JSON.stringify(row[h] ?? '')).join(','));
  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  a.click(); URL.revokeObjectURL(url);
};
