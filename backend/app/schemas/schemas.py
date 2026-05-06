from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

VALID_SPORTS = ["篮球","足球","游泳","田径","羽毛球","排球","网球","乒乓球","拳击","举重","体操","击剑","柔道","跆拳道","通用","其他"]
VALID_TYPES = ["力量","耐力","速度","技战术","柔韧","混合"]

def _opt_date(f): return Field(None) if f == date else None

def _sport_validator(v):
    if v is not None and v not in VALID_SPORTS:
        raise ValueError(f"运动项目必须是以下之一: {VALID_SPORTS}")
    return v

def _type_validator(v):
    if v is not None and v not in VALID_TYPES:
        raise ValueError(f"训练类型必须是以下之一: {VALID_TYPES}")
    return v


# ============ Athlete Schemas ============

class AthleteCreate(BaseModel):
    name: str = Field(..., max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(男|女|其他)$")
    sport: str = Field(..., max_length=50)
    position_or_event: Optional[str] = None
    athlete_type: Optional[str] = "real"
    training_years: Optional[float] = Field(None, ge=0)
    injury_history: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    hand_dominance: Optional[str] = None
    coach_notes: Optional[str] = None
    dominant_foot: Optional[str] = None
    position_role: Optional[str] = None

    _v_sport = validator("sport", allow_reuse=True)(_sport_validator)


class AthleteResponse(BaseModel):
    id: UUID
    name: str
    date_of_birth: date
    gender: str
    sport: str
    position_or_event: Optional[str]
    athlete_type: Optional[str] = "real"
    training_years: Optional[float]
    injury_history: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    hand_dominance: Optional[str]
    coach_notes: Optional[str]
    dominant_foot: Optional[str]
    position_role: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AthleteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    sport: Optional[str] = None
    position_or_event: Optional[str] = None
    training_years: Optional[float] = Field(None, ge=0)
    injury_history: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    hand_dominance: Optional[str] = None
    coach_notes: Optional[str] = None
    dominant_foot: Optional[str] = None
    position_role: Optional[str] = None

    _v_sport = validator("sport", allow_reuse=True)(_sport_validator)


class AthleteBaselineCreate(BaseModel):
    athlete_id: UUID
    metric_name: str
    baseline_value: float
    typical_error: Optional[float] = None
    swc: Optional[float] = None
    established_at: date
    valid_until: Optional[date] = None
    notes: Optional[str] = None


# ============ Training Log Schemas ============

class TrainingLogCreate(BaseModel):
    athlete_id: UUID
    training_date: date
    duration_minutes: float = Field(..., gt=0)
    rpe: int = Field(..., ge=1, le=10)
    training_type: str
    cycle_phase: Optional[str] = None
    description: Optional[str] = None
    coach_notes: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    source: str = "manual"

    _v_type = validator("training_type", allow_reuse=True)(_type_validator)


class TrainingLogResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    training_date: date
    duration_minutes: float
    rpe: int
    training_type: str
    session_load: Optional[float] = None
    cycle_phase: Optional[str]
    description: Optional[str]
    coach_notes: Optional[str]
    tags: Optional[List[str]]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingLogBatch(BaseModel):
    """批量导入训练日志"""
    logs: List[TrainingLogCreate] = Field(..., min_items=1, max_items=500)


# ============ Performance Test Schemas ============

class PerformanceTestCreate(BaseModel):
    athlete_id: UUID
    test_date: date
    squat_1rm_kg: Optional[float] = Field(None, ge=0)
    bench_press_1rm_kg: Optional[float] = Field(None, ge=0)
    deadlift_1rm_kg: Optional[float] = Field(None, ge=0)
    cmj_height_cm: Optional[float] = Field(None, ge=0)
    rfd_n_per_s: Optional[float] = Field(None, ge=0)
    sprint_30m_sec: Optional[float] = Field(None, ge=0)
    standing_long_jump_cm: Optional[float] = Field(None, ge=0)
    med_ball_throw_m: Optional[float] = Field(None, ge=0)
    vo2max_ml_kg_min: Optional[float] = Field(None, ge=0)
    lactate_threshold_power_w: Optional[float] = Field(None, ge=0)
    lactate_threshold_pace: Optional[str] = None
    test_protocol: Optional[str] = None
    notes: Optional[str] = None


# ============ Wellness Schemas ============

class WellnessCreate(BaseModel):
    athlete_id: UUID
    record_date: date
    morning_heart_rate: Optional[int] = Field(None, ge=30, le=120)
    hrv_lnrmssd: Optional[float] = Field(None, ge=0)
    sleep_duration_hours: Optional[float] = Field(None, ge=0, le=15)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    fatigue_score: Optional[int] = Field(None, ge=1, le=5)
    muscle_soreness: Optional[int] = Field(None, ge=1, le=5)
    stress_score: Optional[int] = Field(None, ge=1, le=5)
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    body_weight_kg: Optional[float] = Field(None, ge=0)
    illness_flag: bool = False
    notes: Optional[str] = None
    source: str = Field(default="manual")


# ============ Dashboard / Analytics Schemas ============

class AthleteRiskStatus(BaseModel):
    athlete_id: UUID
    athlete_name: str
    sport: str
    latest_acwr: float
    acwr_risk_zone: str
    rssi_score: float
    rssi_risk_level: str
    trend_direction: str = "稳定"
    active_alerts: int = 0
    last_updated: date

class DashboardOverview(BaseModel):
    total_athletes: int
    athletes_at_risk: int
    active_alerts: int
    avg_team_acwr: float
    alerts_by_severity: Dict[str, int]
    athlete_statuses: List[AthleteRiskStatus]

class ACWRTimeSeries(BaseModel):
    dates: List[str]
    acute_load: List[float]
    chronic_load: List[float]
    acwr: List[float]
    risk_zone_thresholds: Dict[str, float]

class RSSIDetail(BaseModel):
    date: date
    rssi_score: float
    risk_level: str
    acwr_component: float
    heart_rate_component: float
    hrv_component: float
    fatigue_component: float
    performance_component: float
    recommendations: List[str]
    warnings: List[str]

class PerformanceComparison(BaseModel):
    metric: str
    current_value: float
    previous_value: float
    baseline_value: float
    change_pct: float
    sport_avg: Optional[float]
    is_significant: bool
    interpretation: str


# ============ Alert Schemas ============

class AlertResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    alert_date: date
    alert_type: str
    severity: str
    alert_source: Optional[str]
    current_value: Optional[str]
    recommended_action: Optional[str]
    is_read: bool
    is_resolved: bool
    coach_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_resolved: Optional[bool] = None
    coach_notes: Optional[str] = None


# ============ Training Recommendation Schema ============

class TrainingRecommendationResponse(BaseModel):
    summary: str
    load_adjustment: str
    intensity_recommendation: str
    volume_recommendation: str
    frequency_recommendation: str
    priority_areas: List[str]
    recovery_strategies: List[str]
    weekly_template: List[Dict]
    warnings: List[str]


# ============ CSV Import Schemas ============

class ImportRequest(BaseModel):
    """数据导入请求"""
    data_type: str = Field(..., description="training/wellness/performance_test")
    file_content: str  # Base64 encoded CSV/Excel content
    format: str = "csv"


class ImportResponse(BaseModel):
    records_imported: int
    records_skipped: int
    errors: List[Dict]
    message: str


# ============ Daily Readiness Schemas ============

class DailyReadinessCreate(BaseModel):
    athlete_id: UUID
    record_date: date
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    muscle_soreness: Optional[int] = Field(None, ge=1, le=5)
    fatigue_level: Optional[int] = Field(None, ge=1, le=5)
    stress_motivation: Optional[int] = Field(None, ge=1, le=5)
    discomfort_notes: Optional[str] = None
    readiness_color: Optional[str] = Field(None, pattern="^(green|yellow|red)$")


class DailyReadinessResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    record_date: date
    sleep_quality: Optional[int]
    muscle_soreness: Optional[int]
    fatigue_level: Optional[int]
    stress_motivation: Optional[int]
    discomfort_notes: Optional[str]
    readiness_color: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Exercise Library Schemas ============

class ExerciseLibraryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = None
    category_l1: Optional[str] = None
    category_l2: Optional[str] = None
    nasm_phase: Optional[str] = None
    target_muscles: Optional[List[str]] = Field(default_factory=list)
    instructions: Optional[str] = None
    literature_ref: Optional[str] = None
    description: Optional[str] = None
    preset_params: Optional[Dict] = None
    coach_id: Optional[UUID] = None


class ExerciseLibraryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    category_l1: Optional[str] = None
    category_l2: Optional[str] = None
    nasm_phase: Optional[str] = None
    target_muscles: Optional[List[str]] = None
    instructions: Optional[str] = None
    literature_ref: Optional[str] = None
    description: Optional[str] = None
    preset_params: Optional[Dict] = None


class ExerciseLibraryResponse(BaseModel):
    id: UUID
    name: str
    category: Optional[str]
    category_l1: Optional[str]
    category_l2: Optional[str]
    nasm_phase: Optional[str]
    target_muscles: Optional[list] = None
    instructions: Optional[str]
    literature_ref: Optional[str]
    description: Optional[str]
    preset_params: Optional[Dict]
    coach_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class ExerciseLibraryListResponse(BaseModel):
    exercises: List[ExerciseLibraryResponse]
    total: int


# ============ Planned Exercise / Session Schemas ============

class PlannedExerciseCreate(BaseModel):
    exercise_id: Optional[UUID] = None
    order_index: int = Field(..., ge=0)
    target_weight_kg: Optional[float] = Field(None, ge=0)
    target_reps: Optional[int] = Field(None, ge=0)
    target_sets: Optional[int] = Field(None, ge=0)
    rest_seconds: Optional[int] = Field(None, ge=0)
    target_rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class PlannedExerciseResponse(BaseModel):
    id: UUID
    planned_session_id: UUID
    exercise_id: Optional[UUID] = None
    order_index: int
    target_weight_kg: Optional[float]
    target_reps: Optional[int]
    target_sets: Optional[int]
    rest_seconds: Optional[int]
    target_rpe: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class PlannedSessionCreate(BaseModel):
    athlete_id: UUID
    plan_date: date
    session_name: Optional[str] = Field(None, max_length=100)
    training_type: Optional[str] = Field(None, description="力量/耐力/速度/技战术/柔韧/混合")
    notes: Optional[str] = None
    exercises: List[PlannedExerciseCreate] = Field(default_factory=list)


class PlannedSessionResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    plan_date: date
    created_by: Optional[UUID]
    session_name: Optional[str]
    training_type: Optional[str]
    notes: Optional[str]
    planned_load: Optional[float] = 0
    status: Optional[str] = "scheduled"
    created_at: datetime
    updated_at: datetime
    exercises: List[PlannedExerciseResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AssignSessionRequest(BaseModel):
    athlete_ids: List[UUID] = Field(..., min_items=1)


# ============ Exercise Log Schemas ============

class ExerciseLogCreate(BaseModel):
    training_log_id: UUID
    exercise_id: UUID
    order_index: Optional[int] = Field(None, ge=0)
    actual_weight_kg: Optional[float] = Field(None, ge=0)
    actual_reps: Optional[int] = Field(None, ge=0)
    actual_sets: Optional[int] = Field(None, ge=0)
    actual_rpe: Optional[int] = Field(None, ge=1, le=10)
    planned_exercise_id: Optional[UUID] = None
    notes: Optional[str] = None


class ExerciseLogResponse(BaseModel):
    id: UUID
    training_log_id: UUID
    exercise_id: UUID
    order_index: Optional[int]
    actual_weight_kg: Optional[float]
    actual_reps: Optional[int]
    actual_sets: Optional[int]
    actual_rpe: Optional[int]
    planned_exercise_id: Optional[UUID]
    notes: Optional[str]

    class Config:
        from_attributes = True


class SessionDeviationResponse(BaseModel):
    plan_load: float
    actual_load: float
    deviation_pct: float
    is_over_threshold: bool


# ============ Coach Comment Schemas ============

class CoachCommentCreate(BaseModel):
    athlete_id: UUID
    training_log_id: Optional[UUID] = None
    created_by: UUID
    comment_text: str
    rating: int = Field(..., ge=1, le=10)


class CoachCommentUpdate(BaseModel):
    comment_text: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=10)


class CoachCommentResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    training_log_id: Optional[UUID]
    created_by: UUID
    comment_text: str
    rating: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Injury Schemas ============

class InjuryRestrictionCreate(BaseModel):
    restriction_type: str = Field(..., pattern="^(禁止动作|负荷限制|RoM限制)$")
    restriction_detail: str
    exercise_name_pattern: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class InjuryRestrictionResponse(BaseModel):
    id: UUID
    injury_record_id: UUID
    restriction_type: str
    restriction_detail: str
    exercise_name_pattern: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ReturnToPlayChecklistCreate(BaseModel):
    check_item: str = Field(..., max_length=200)
    target_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class ReturnToPlayChecklistUpdate(BaseModel):
    actual_value: Optional[float] = None
    is_passed: Optional[bool] = None
    notes: Optional[str] = None


class ReturnToPlayChecklistResponse(BaseModel):
    id: UUID
    injury_record_id: UUID
    check_item: str
    target_value: Optional[float]
    actual_value: Optional[float]
    unit: Optional[str]
    is_passed: bool
    passed_date: Optional[date]
    notes: Optional[str]

    class Config:
        from_attributes = True


class InjuryRehabLogCreate(BaseModel):
    log_date: date
    pain_score: Optional[int] = Field(None, ge=0, le=10)
    rehab_completion_pct: Optional[float] = Field(None, ge=0, le=100)
    exercises_completed: Optional[str] = None
    notes: Optional[str] = None


class InjuryRehabLogResponse(BaseModel):
    id: UUID
    injury_record_id: UUID
    log_date: date
    pain_score: Optional[int]
    rehab_completion_pct: Optional[float]
    exercises_completed: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class InjuryRecordCreate(BaseModel):
    athlete_id: UUID
    diagnosis: str
    injury_date: date
    expected_recovery_weeks: Optional[float] = Field(None, ge=0)
    body_part: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = Field(None, pattern="^(轻度|中度|重度)$")
    status: str = Field(default="活跃", pattern="^(活跃|康复中|已恢复)$")
    notes: Optional[str] = None
    restrictions: List[InjuryRestrictionCreate] = Field(default_factory=list)
    checklist_items: List[ReturnToPlayChecklistCreate] = Field(default_factory=list)


class InjuryRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    expected_recovery_weeks: Optional[float] = Field(None, ge=0)
    actual_return_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(活跃|康复中|已恢复)$")
    body_part: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = Field(None, pattern="^(轻度|中度|重度)$")
    notes: Optional[str] = None


class InjuryRecordResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    diagnosis: str
    injury_date: date
    expected_recovery_weeks: Optional[float]
    actual_return_date: Optional[date]
    status: str
    body_part: Optional[str]
    severity: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    restrictions: List[InjuryRestrictionResponse] = Field(default_factory=list)
    checklist_items: List[ReturnToPlayChecklistResponse] = Field(default_factory=list)
    rehab_logs: List[InjuryRehabLogResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============ Team Group Schemas ============

class TeamGroupCreate(BaseModel):
    name: str = Field(..., max_length=50)
    coach_id: Optional[UUID] = None


class TeamGroupMemberResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    athlete_name: Optional[str] = None

    class Config:
        from_attributes = True


class TeamGroupResponse(BaseModel):
    id: UUID
    name: str
    coach_id: Optional[UUID]
    created_at: datetime
    members: List[TeamGroupMemberResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TeamHeatmapEntry(BaseModel):
    athlete_name: str
    acwr: float
    acwr_color: str
    rssi_score: float
    rssi_level: str
    recent_load: Optional[float] = None
    perf_trend: Optional[str] = None
    active_injuries: int = 0


class TeamHeatmapResponse(BaseModel):
    group_name: str
    entries: List[TeamHeatmapEntry]
    avg_acwr: float
    at_risk_pct: float


class AddMemberRequest(BaseModel):
    athlete_id: UUID


# ============ Periodization Template Schemas ============

class PeriodizationTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    template_type: str = Field(..., pattern="^(线性周期|非线性DUP|板块周期)$")
    cycle_phase: str = Field(..., pattern="^(一般准备期|专项准备期|比赛期|过渡期)$")
    description: Optional[str] = None
    weekly_structure: Optional[List[Dict]] = Field(default_factory=list)
    coach_id: Optional[UUID] = None
    is_system: bool = False


class PeriodizationTemplateResponse(BaseModel):
    id: UUID
    name: str
    template_type: str
    cycle_phase: str
    description: Optional[str]
    weekly_structure: Any = None
    coach_id: Optional[UUID]
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApplyTemplateRequest(BaseModel):
    athlete_ids: List[UUID] = Field(..., min_items=1)
    start_date: date


# ============ Composite Schemas ============

class AthleteProfileComplete(BaseModel):
    athlete: AthleteResponse
    current_acwr: Optional[float] = None
    acwr_risk_zone: Optional[str] = None
    rssi_score: Optional[float] = None
    rssi_level: Optional[str] = None
    latest_test_date: Optional[date] = None
    active_injuries: int = 0
    active_injury_details: List[InjuryRecordResponse] = Field(default_factory=list)


class RadarChartData(BaseModel):
    metric_names: List[str] = Field(default_factory=list)
    current_values: List[float] = Field(default_factory=list)
    best_values: List[float] = Field(default_factory=list)
    norm_low: List[float] = Field(default_factory=list)
    norm_high: List[float] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


# ============ Nutrition Schemas ============

class NutritionLogCreate(BaseModel):
    athlete_id: UUID
    log_date: date
    protein_sufficient: Optional[str] = Field(None, pattern="^(是|否|约量)$")
    post_training_refuel: bool = False
    water_intake_liters: Optional[float] = Field(None, ge=0, le=20)
    appetite_score: Optional[int] = Field(None, ge=1, le=5)
    morning_weight_kg: Optional[float] = Field(None, ge=0, le=300)
    notes: Optional[str] = None


class NutritionLogResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    log_date: date
    protein_sufficient: Optional[str]
    post_training_refuel: bool
    water_intake_liters: Optional[float]
    appetite_score: Optional[int]
    morning_weight_kg: Optional[float]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NutritionRiskStatus(BaseModel):
    has_risk: bool
    reason: str
    consecutive_days: int


# ============ Mental Schemas ============

class MentalLogCreate(BaseModel):
    athlete_id: UUID
    log_date: date
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    focus_score: Optional[int] = Field(None, ge=1, le=5)
    motivation_score: Optional[int] = Field(None, ge=1, le=5)
    mental_fatigue_score: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class MentalLogResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    log_date: date
    mood_score: Optional[int]
    focus_score: Optional[int]
    motivation_score: Optional[int]
    mental_fatigue_score: Optional[int]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MentalWeeklyReport(BaseModel):
    week_start: date
    avg_mood: float
    avg_focus: float
    avg_motivation: float
    avg_fatigue: float
    trend: str
    has_alert: bool


# ============ Composite Risk Score Schema ============

class CompositeRiskScore(BaseModel):
    athlete_id: UUID
    athlete_name: str
    risk_score: float  # 0-100 (higher = more risk)
    risk_level: str    # "低风险" / "中等风险" / "高风险"
    acwr_contribution: float
    rssi_contribution: float
    fatigue_contribution: float
    mental_contribution: float
    nutrition_contribution: float
    recommendations: List[str]


# ============ Period Comparison Schema ============

class PeriodInfo(BaseModel):
    start: date
    end: date
    total_sessions: int
    avg_daily_load: float
    avg_rpe: float

class MetricComparison(BaseModel):
    metric: str
    period_a_value: float
    period_b_value: float
    change_pct: float
    direction: str  # "上升"/"下降"/"持平"

class PeriodComparisonResponse(BaseModel):
    athlete_id: UUID
    athlete_name: str
    period_a: PeriodInfo
    period_b: PeriodInfo
    training_load_comparison: List[MetricComparison] = Field(default_factory=list)
    test_comparison: List[MetricComparison] = Field(default_factory=list)
    subjective_comparison: List[MetricComparison] = Field(default_factory=list)


# ============ Competition Schemas ============

class CompetitionCreate(BaseModel):
    name: str = Field(..., max_length=200)
    competition_date: date
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class CompetitionResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    name: str
    competition_date: date
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Daily Metric Schemas ============

class DailyMetricResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    metric_date: date
    training_load: float
    injury_risk: float
    fatigue: float
    sleep_quality: float
    training_content: Optional[str]
    notes: Optional[str]
    # 身体数据
    smash_count_today: Optional[int] = 0
    smash_7d_avg: Optional[float] = 0
    overhead_week_total: Optional[int] = 0
    max_smash_30d: Optional[int] = 0
    external_rotation_ratio: Optional[float] = 0.7
    arm_pain_vas: Optional[int] = 0
    total_impacts_7d: Optional[int] = 0
    jump_landing_quality: Optional[int] = 7
    quad_hamstring_ratio: Optional[float] = 0.8
    footwork_score: Optional[int] = 7
    leg_pain_vas: Optional[int] = 0
    reaction_time_ms: Optional[int] = 250
    has_knee_pain_history: Optional[bool] = False
    # 风险值
    shoulder_overuse_risk: Optional[float] = 0
    shoulder_acute_risk: Optional[float] = 0
    knee_overuse_risk: Optional[float] = 0
    knee_acute_risk: Optional[float] = 0
    # 训练日志升级
    rpe: Optional[int] = None
    energy_level: Optional[int] = None
    muscle_soreness: Optional[dict] = None
    technical_notes: Optional[str] = None
    plan_vs_actual_diff: Optional[float] = None
    completion_rate: Optional[float] = None
    media_urls: Optional[list] = None

    class Config:
        from_attributes = True


class DailyMetricUpdate(BaseModel):
    metric_date: Optional[date] = None
    training_load: Optional[float] = Field(None, ge=0, le=100)
    injury_risk: Optional[float] = Field(None, ge=0, le=100)
    fatigue: Optional[float] = Field(None, ge=0, le=100)
    sleep_quality: Optional[float] = Field(None, ge=1, le=7)
    training_content: Optional[str] = None
    notes: Optional[str] = None
    # 身体数据
    smash_count_today: Optional[int] = Field(None, ge=0)
    smash_7d_avg: Optional[float] = Field(None, ge=0)
    overhead_week_total: Optional[int] = Field(None, ge=0)
    max_smash_30d: Optional[int] = Field(None, ge=0)
    external_rotation_ratio: Optional[float] = Field(None, ge=0)
    arm_pain_vas: Optional[int] = Field(None, ge=0, le=10)
    total_impacts_7d: Optional[int] = Field(None, ge=0)
    jump_landing_quality: Optional[int] = Field(None, ge=1, le=10)
    quad_hamstring_ratio: Optional[float] = Field(None, ge=0)
    footwork_score: Optional[int] = Field(None, ge=1, le=10)
    leg_pain_vas: Optional[int] = Field(None, ge=0, le=10)
    reaction_time_ms: Optional[int] = Field(None, ge=50)
    has_knee_pain_history: Optional[bool] = None
    # Training log v2 fields
    rpe: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    muscle_soreness: Optional[dict] = None
    technical_notes: Optional[str] = None
    plan_vs_actual_diff: Optional[float] = None
    completion_rate: Optional[float] = None
    media_urls: Optional[list] = None


class DailyMetricBodyUpdate(BaseModel):
    """仅更新身体数据字段（教练每日录入）"""
    smash_count_today: Optional[int] = Field(None, ge=0)
    smash_7d_avg: Optional[float] = Field(None, ge=0)
    overhead_week_total: Optional[int] = Field(None, ge=0)
    max_smash_30d: Optional[int] = Field(None, ge=0)
    external_rotation_ratio: Optional[float] = Field(None, ge=0)
    arm_pain_vas: Optional[int] = Field(None, ge=0, le=10)
    total_impacts_7d: Optional[int] = Field(None, ge=0)
    jump_landing_quality: Optional[int] = Field(None, ge=1, le=10)
    quad_hamstring_ratio: Optional[float] = Field(None, ge=0)
    footwork_score: Optional[int] = Field(None, ge=1, le=10)
    leg_pain_vas: Optional[int] = Field(None, ge=0, le=10)
    reaction_time_ms: Optional[int] = Field(None, ge=50)
    has_knee_pain_history: Optional[bool] = None


# ============ Alert Config Schemas ============

class AlertConfigCreate(BaseModel):
    athlete_id: UUID
    metric_name: str
    threshold: float
    severity: str = Field(default="warning", pattern="^(warning|critical)$")
    notify: bool = True


class AlertConfigResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    metric_name: str
    threshold: float
    severity: str
    notify: bool

    class Config:
        from_attributes = True


class AlertConfigUpdate(BaseModel):
    threshold: Optional[float] = None
    severity: Optional[str] = Field(None, pattern="^(warning|critical)$")
    notify: Optional[bool] = None


# ============ Recovery Suggestion Schemas ============

class RecoveryExerciseItem(BaseModel):
    name: str
    sets: Optional[int] = 1
    reps: Optional[int] = 1
    duration_min: Optional[int] = 15
    notes: Optional[str] = None
    category: Optional[str] = "recovery"
    completed: bool = False


class RecoverySuggestionResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    date: date
    suggestion_text: Optional[str]
    exercises: Optional[List[dict]] = Field(default_factory=list)
    status: str
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecoverySuggestionCreate(BaseModel):
    athlete_id: UUID
    date: date


class MonthlyRiskResponse(BaseModel):
    date: str
    injury_risk: float
    training_load: float
    has_competition: bool = False
    competition_name: Optional[str] = None


class TrainingRecommendationResponse2(BaseModel):
    competition_date: date
    days_until: int
    phase: str
    phase_label: str
    load_range: str
    description: str
    recommendations: List[str]


# ============ Training Template Schemas ============

class TrainingTemplateCreate(BaseModel):
    name: str = Field(..., max_length=200)
    type: str = Field(default="daily", pattern="^(daily|weekly|periodized)$")
    sport: str = Field(default="羽毛球", max_length=50)
    intensity_zone: Optional[str] = None
    target_focus: Optional[List[str]] = Field(default_factory=list)
    weekly_frequency: Optional[str] = None
    is_public: bool = True
    content: dict
    description: Optional[str] = None


class TrainingTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = Field(None, pattern="^(daily|weekly|periodized)$")
    intensity_zone: Optional[str] = None
    target_focus: Optional[List[str]] = None
    weekly_frequency: Optional[str] = None
    is_public: Optional[bool] = None
    content: Optional[dict] = None
    description: Optional[str] = None


class TrainingTemplateResponse(BaseModel):
    id: UUID
    name: str
    type: str
    sport: Optional[str]
    intensity_zone: Optional[str]
    target_focus: Optional[List[str]]
    weekly_frequency: Optional[str] = None
    is_public: bool
    content: dict
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingAssignmentCreate(BaseModel):
    athlete_id: UUID
    template_id: UUID
    scheduled_date: date
    overrides: Optional[dict] = Field(default_factory=dict)
    notes: Optional[str] = None


class TrainingAssignmentResponse(BaseModel):
    id: UUID
    athlete_id: UUID
    template_id: Optional[UUID]
    scheduled_date: date
    overrides: Optional[dict]
    status: str
    actual_log_id: Optional[UUID]
    notes: Optional[str]
    template_name: Optional[str] = None
    template_content: Optional[dict] = None

    class Config:
        from_attributes = True


class PlanVsActualResponse(BaseModel):
    scheduled_date: date
    planned_load: float
    actual_load: float
    diff_pct: float
    completion_rate: float
    status: str


# ============ Plan vs Actual Detail Schemas ============

class ExercisePlanVsActual(BaseModel):
    exercise_id: Optional[UUID] = None
    exercise_name: str = ""
    planned_sets: Optional[int] = None
    planned_reps: Optional[int] = None
    planned_rpe: Optional[int] = None
    planned_weight: Optional[float] = None
    actual_sets: Optional[int] = None
    actual_reps: Optional[int] = None
    actual_rpe: Optional[int] = None
    actual_weight: Optional[float] = None
    planned_load: float = 0
    actual_load: float = 0
    completion_pct: float = 0


class SessionPlanVsActualResponse(BaseModel):
    session_id: UUID
    session_name: Optional[str] = None
    plan_date: date
    planned_load: float = 0
    actual_load: float = 0
    deviation_pct: float = 0
    completion_rate: float = 0
    exercises: List[ExercisePlanVsActual] = Field(default_factory=list)


# ============ Batch Create Schemas ============

class BatchSessionCreate(BaseModel):
    athlete_id: UUID
    start_date: date
    end_date: date
    weekdays: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6], description="0=Mon, 6=Sun")
    session_name: Optional[str] = None
    training_type: Optional[str] = "混合"
    exercises: List[PlannedExerciseCreate] = Field(default_factory=list)
    notes: Optional[str] = None


# ============ Auto Adjust Schemas ============

class AutoAdjustRequest(BaseModel):
    adjustment_factor: float = Field(default=-20.0, description="调整百分比，负数表示降低负荷")
    reason: Optional[str] = None

    @validator("adjustment_factor", pre=True)
    def coerce_float(cls, v):
        return float(v)


class AdjustedSession(BaseModel):
    session_id: UUID
    plan_date: date
    original_load: float
    adjusted_load: float
    change_pct: float


class AutoAdjustResponse(BaseModel):
    athlete_id: UUID
    adjustment_factor: float
    sessions_adjusted: int
    details: List[AdjustedSession] = Field(default_factory=list)
    summary: str = ""


# ============ Exercise Log with Plan Link Schema ============

class PlanLinkedLogCreate(BaseModel):
    athlete_id: UUID
    session_exercise_id: UUID
    actual_sets_completed: Optional[int] = Field(None, ge=0)
    actual_reps_completed: Optional[int] = Field(None, ge=0)
    actual_rpe: Optional[int] = Field(None, ge=1, le=10)
    actual_duration_min: Optional[int] = Field(None, ge=0)
    actual_weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class WeekPlanResponse(BaseModel):
    week_start: date
    week_end: date
    days: List[dict] = Field(default_factory=list)  # [{date, day_name, sessions: [...]}]
