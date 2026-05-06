import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Text, ForeignKey, Boolean, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def _UID(primary_key=False):
    return Column(String(36), primary_key=primary_key, default=lambda: str(uuid.uuid4()))

def _FKey(table_col, nullable=True, ondelete=None):
    fk = ForeignKey(table_col, **({"ondelete": ondelete} if ondelete else {}))
    return Column(String(36), fk, nullable=nullable)


class Athlete(Base):
    __tablename__ = "athletes"
    id = _UID(primary_key=True)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10))
    sport = Column(String(50), nullable=False)
    position_or_event = Column(String(100))
    athlete_type = Column(String(20), default="real")  # "real" or "test"
    training_years = Column(Float)
    injury_history = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(30))
    hand_dominance = Column(String(10))
    coach_notes = Column(Text)
    dominant_foot = Column(String(10))
    position_role = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    baselines = relationship("AthleteBaseline", back_populates="athlete", cascade="all, delete-orphan")
    training_logs = relationship("TrainingLog", back_populates="athlete", cascade="all, delete-orphan")
    performance_tests = relationship("PerformanceTest", back_populates="athlete", cascade="all, delete-orphan")
    wellness_questionnaires = relationship("WellnessQuestionnaire", back_populates="athlete", cascade="all, delete-orphan")
    computed_metrics = relationship("ComputedMetric", back_populates="athlete", cascade="all, delete-orphan")
    alert_events = relationship("AlertEvent", back_populates="athlete", cascade="all, delete-orphan")
    periodization_plans = relationship("PeriodizationPlan", back_populates="athlete", cascade="all, delete-orphan")
    daily_readiness = relationship("DailyReadiness", back_populates="athlete", cascade="all, delete-orphan")
    planned_sessions = relationship("PlannedSession", back_populates="athlete", cascade="all, delete-orphan")
    coach_comments = relationship("CoachComment", back_populates="athlete", cascade="all, delete-orphan")
    injury_records = relationship("InjuryRecord", back_populates="athlete", cascade="all, delete-orphan")
    group_memberships = relationship("TeamGroupMember", back_populates="athlete", cascade="all, delete-orphan")
    competitions = relationship("Competition", back_populates="athlete", cascade="all, delete-orphan")
    alert_configs = relationship("AlertConfig", back_populates="athlete", cascade="all, delete-orphan")
    recovery_suggestions = relationship("RecoverySuggestion", back_populates="athlete", cascade="all, delete-orphan")


class AthleteBaseline(Base):
    __tablename__ = "athlete_baselines"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    metric_name = Column(String(50), nullable=False)
    baseline_value = Column(Float, nullable=False)
    typical_error = Column(Float)
    swc = Column(Float)
    established_at = Column(Date, nullable=False)
    valid_until = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="baselines")
    __table_args__ = (UniqueConstraint("athlete_id", "metric_name", "established_at"),)


class TrainingLog(Base):
    __tablename__ = "training_logs"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    training_date = Column(Date, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    rpe = Column(Integer, nullable=False)
    training_type = Column(String(20))
    session_load = Column(Float)
    description = Column(Text)
    cycle_phase = Column(String(20))
    coach_notes = Column(Text)
    tags = Column(JSON, default=list)
    source = Column(String(30), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="training_logs")
    __table_args__ = (UniqueConstraint("athlete_id", "training_date"),)


class PerformanceTest(Base):
    __tablename__ = "performance_tests"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    test_date = Column(Date, nullable=False)
    squat_1rm_kg = Column(Float)
    bench_press_1rm_kg = Column(Float)
    deadlift_1rm_kg = Column(Float)
    cmj_height_cm = Column(Float)
    rfd_n_per_s = Column(Float)
    sprint_30m_sec = Column(Float)
    standing_long_jump_cm = Column(Float)
    med_ball_throw_m = Column(Float)
    vo2max_ml_kg_min = Column(Float)
    lactate_threshold_power_w = Column(Float)
    lactate_threshold_pace = Column(String(20))
    test_protocol = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="performance_tests")
    __table_args__ = (UniqueConstraint("athlete_id", "test_date"),)


class WellnessQuestionnaire(Base):
    __tablename__ = "wellness_questionnaires"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    record_date = Column(Date, nullable=False)
    morning_heart_rate = Column(Integer)
    hrv_lnrmssd = Column(Float)
    sleep_duration_hours = Column(Float)
    sleep_quality = Column(Integer)
    fatigue_score = Column(Integer)
    muscle_soreness = Column(Integer)
    stress_score = Column(Integer)
    mood_score = Column(Integer)
    body_weight_kg = Column(Float)
    illness_flag = Column(Boolean, default=False)
    notes = Column(Text)
    source = Column(String(30), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="wellness_questionnaires")
    __table_args__ = (UniqueConstraint("athlete_id", "record_date"),)


class ComputedMetric(Base):
    __tablename__ = "computed_metrics"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    calc_date = Column(Date, nullable=False)
    acute_load_7d = Column(Float)
    chronic_load_28d = Column(Float)
    acwr = Column(Float)
    acwr_risk_zone = Column(String(20))
    monotony = Column(Float)
    strain = Column(Float)
    strain_zscore = Column(Float)
    rssi_score = Column(Float)
    rssi_risk_level = Column(String(30))
    acwr_component = Column(Float)
    hr_component = Column(Float)
    hrv_component = Column(Float)
    fatigue_component = Column(Float)
    performance_component = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="computed_metrics")
    __table_args__ = (UniqueConstraint("athlete_id", "calc_date"),)


class AlertEvent(Base):
    __tablename__ = "alert_events"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    alert_date = Column(Date, nullable=False)
    alert_type = Column(String(30))
    severity = Column(String(10))
    alert_source = Column(String(50))
    current_value = Column(Text)
    recommended_action = Column(Text)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    coach_notes = Column(Text)
    coach_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="alert_events")


class PeriodizationPlan(Base):
    __tablename__ = "periodization_plans"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", nullable=False)
    plan_name = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    cycle_type = Column(String(20))
    weekly_template = Column(JSON, default=list)
    coach_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="periodization_plans")


class User(Base):
    __tablename__ = "users"
    id = _UID(primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20))
    athlete_id = _FKey("athletes.id")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyReadiness(Base):
    __tablename__ = "daily_readiness"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    record_date = Column(Date, nullable=False)
    sleep_quality = Column(Integer)
    muscle_soreness = Column(Integer)
    fatigue_level = Column(Integer)
    stress_motivation = Column(Integer)
    discomfort_notes = Column(Text)
    readiness_color = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="daily_readiness")
    __table_args__ = (UniqueConstraint("athlete_id", "record_date"),)


class ExerciseLibrary(Base):
    __tablename__ = "exercise_library"
    id = _UID(primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(30))
    category_l1 = Column(String(30))              # 一级分类: 力量/耐力/康复-纠正性训练
    category_l2 = Column(String(30))              # 二级分类: 肘部/腕部/膝关节/腰部
    nasm_phase = Column(String(10))               # NASM阶段: INH/LEN/ACT/INT
    target_muscles = Column(JSON, default=list)   # 目标肌群数组
    instructions = Column(Text)                   # 详细步骤
    literature_ref = Column(Text)                 # 文献依据
    description = Column(Text)
    preset_params = Column(JSON)
    coach_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    planned_exercises = relationship("PlannedExercise", back_populates="exercise")
    exercise_logs = relationship("ExerciseLog", back_populates="exercise")
    injury_links = relationship("ExerciseInjuryLink", back_populates="exercise", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("name", "coach_id"),)


class ExerciseInjuryLink(Base):
    """关联康复动作与伤病类型"""
    __tablename__ = "exercise_injury_links"
    id = _UID(primary_key=True)
    exercise_id = _FKey("exercise_library.id", ondelete="CASCADE", nullable=False)
    injury_body_part = Column(String(30), nullable=False)  # elbow/knee/shoulder/wrist/back
    risk_factor = Column(String(20))                        # preventive/rehab/both
    priority = Column(Integer, default=1)                   # 1=首选, 2=备选
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    exercise = relationship("ExerciseLibrary", back_populates="injury_links")
    __table_args__ = (UniqueConstraint("exercise_id", "injury_body_part"),)


class PlannedSession(Base):
    __tablename__ = "planned_sessions"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    plan_date = Column(Date, nullable=False)
    created_by = _FKey("users.id")
    session_name = Column(String(100))
    training_type = Column(String(20))
    notes = Column(Text)
    planned_load = Column(Float, default=0)        # 自动计算的计划负荷
    status = Column(String(20), default="scheduled")  # scheduled/completed/missed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="planned_sessions")
    planned_exercises = relationship("PlannedExercise", back_populates="planned_session", cascade="all, delete-orphan")


class PlannedExercise(Base):
    __tablename__ = "planned_exercises"
    id = _UID(primary_key=True)
    planned_session_id = _FKey("planned_sessions.id", ondelete="CASCADE", nullable=False)
    exercise_id = _FKey("exercise_library.id", nullable=True)
    order_index = Column(Integer, nullable=False)
    target_weight_kg = Column(Float)
    target_reps = Column(Integer)
    target_sets = Column(Integer)
    rest_seconds = Column(Integer)
    target_rpe = Column(Integer)
    notes = Column(Text)
    planned_session = relationship("PlannedSession", back_populates="planned_exercises")
    exercise = relationship("ExerciseLibrary", back_populates="planned_exercises")
    exercise_logs = relationship("ExerciseLog", back_populates="planned_exercise")
    __table_args__ = (UniqueConstraint("planned_session_id", "order_index"),)


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"
    id = _UID(primary_key=True)
    training_log_id = _FKey("training_logs.id", ondelete="CASCADE", nullable=False)
    exercise_id = _FKey("exercise_library.id")
    order_index = Column(Integer)
    actual_weight_kg = Column(Float)
    actual_reps = Column(Integer)
    actual_sets = Column(Integer)
    actual_rpe = Column(Integer)
    planned_exercise_id = _FKey("planned_exercises.id")
    notes = Column(Text)
    exercise = relationship("ExerciseLibrary", back_populates="exercise_logs")
    planned_exercise = relationship("PlannedExercise", back_populates="exercise_logs")


class CoachComment(Base):
    __tablename__ = "coach_comments"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    training_log_id = _FKey("training_logs.id")
    created_by = _FKey("users.id", nullable=False)
    comment_text = Column(Text, nullable=False)
    rating = Column(Integer)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    read_by_athlete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="coach_comments")


class InjuryRecord(Base):
    __tablename__ = "injury_records"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    diagnosis = Column(Text, nullable=False)
    injury_date = Column(Date, nullable=False)
    expected_recovery_weeks = Column(Float)
    actual_return_date = Column(Date)
    status = Column(String(20))
    body_part = Column(String(50))
    severity = Column(String(10))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="injury_records")
    rehab_logs = relationship("InjuryRehabLog", back_populates="injury_record", cascade="all, delete-orphan")
    restrictions = relationship("InjuryRestriction", back_populates="injury_record", cascade="all, delete-orphan")
    return_to_play_checklist = relationship("ReturnToPlayChecklist", back_populates="injury_record", cascade="all, delete-orphan")


class InjuryRehabLog(Base):
    __tablename__ = "injury_rehab_logs"
    id = _UID(primary_key=True)
    injury_record_id = _FKey("injury_records.id", ondelete="CASCADE", nullable=False)
    log_date = Column(Date, nullable=False)
    pain_score = Column(Integer)
    rehab_completion_pct = Column(Float)
    exercises_completed = Column(Text)
    notes = Column(Text)
    injury_record = relationship("InjuryRecord", back_populates="rehab_logs")


class InjuryRestriction(Base):
    __tablename__ = "injury_restrictions"
    id = _UID(primary_key=True)
    injury_record_id = _FKey("injury_records.id", ondelete="CASCADE", nullable=False)
    restriction_type = Column(String(50))
    restriction_detail = Column(Text, nullable=False)
    exercise_name_pattern = Column(String(100))
    is_active = Column(Boolean, default=True)
    injury_record = relationship("InjuryRecord", back_populates="restrictions")


class ReturnToPlayChecklist(Base):
    __tablename__ = "return_to_play_checklist"
    id = _UID(primary_key=True)
    injury_record_id = _FKey("injury_records.id", ondelete="CASCADE", nullable=False)
    check_item = Column(String(200), nullable=False)
    target_value = Column(Float)
    actual_value = Column(Float)
    unit = Column(String(20))
    is_passed = Column(Boolean, default=False)
    passed_date = Column(Date)
    notes = Column(Text)
    injury_record = relationship("InjuryRecord", back_populates="return_to_play_checklist")


class TeamGroup(Base):
    __tablename__ = "team_groups"
    id = _UID(primary_key=True)
    name = Column(String(50), nullable=False)
    coach_id = _FKey("users.id")
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("TeamGroupMember", back_populates="group", cascade="all, delete-orphan")


class TeamGroupMember(Base):
    __tablename__ = "team_group_members"
    id = _UID(primary_key=True)
    group_id = _FKey("team_groups.id", ondelete="CASCADE", nullable=False)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    group = relationship("TeamGroup", back_populates="members")
    athlete = relationship("Athlete", back_populates="group_memberships")
    __table_args__ = (UniqueConstraint("group_id", "athlete_id"),)


class PeriodizationTemplate(Base):
    __tablename__ = "periodization_templates"
    id = _UID(primary_key=True)
    name = Column(String(100), nullable=False)
    template_type = Column(String(30))
    cycle_phase = Column(String(20))
    description = Column(Text)
    weekly_structure = Column(JSON, default=list)
    coach_id = Column(String(36))
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    log_date = Column(Date, nullable=False)
    protein_sufficient = Column(String(3))
    post_training_refuel = Column(Boolean, default=False)
    water_intake_liters = Column(Float)
    appetite_score = Column(Integer)
    morning_weight_kg = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("athlete_id", "log_date"),)


class MentalLog(Base):
    __tablename__ = "mental_logs"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    log_date = Column(Date, nullable=False)
    mood_score = Column(Integer)
    focus_score = Column(Integer)
    motivation_score = Column(Integer)
    mental_fatigue_score = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("athlete_id", "log_date"),)


class ExerciseFavorite(Base):
    __tablename__ = "exercise_favorites"
    id = _UID(primary_key=True)
    user_id = Column(String(36), nullable=False)
    exercise_id = _FKey("exercise_library.id", ondelete="CASCADE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "exercise_id"),)


class TemplateFavorite(Base):
    __tablename__ = "template_favorites"
    id = _UID(primary_key=True)
    user_id = Column(String(36), nullable=False)
    template_id = _FKey("periodization_templates.id", ondelete="CASCADE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "template_id"),)


class RecentlyUsed(Base):
    __tablename__ = "recently_used"
    id = _UID(primary_key=True)
    user_id = Column(String(36), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(String(36), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)


class Competition(Base):
    """比赛日程"""
    __tablename__ = "competitions"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    name = Column(String(200), nullable=False)
    competition_date = Column(Date, nullable=False)
    location = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="competitions")


class DailyMetric(Base):
    """每日训练指标 + 身体数据 + 肩/膝风险评分"""
    __tablename__ = "daily_metrics"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    metric_date = Column(Date, nullable=False)

    # 基础训练指标
    training_load = Column(Float, default=0)       # 0-100
    injury_risk = Column(Float, default=0)         # 0-100 (综合)
    fatigue = Column(Float, default=0)             # 0-100
    sleep_quality = Column(Float, default=5.0)     # 1-7
    training_content = Column(Text)
    notes = Column(Text)

    # === 羽毛球专项身体数据 ===
    # 上肢 (肩部)
    smash_count_today = Column(Integer, default=0)        # 今日杀球次数
    smash_7d_avg = Column(Float, default=0)               # 近7天平均杀球量
    overhead_week_total = Column(Integer, default=0)      # 过顶击球周总量
    max_smash_30d = Column(Integer, default=0)            # 近30天最大杀球量
    external_rotation_ratio = Column(Float, default=0.7)  # 外旋/内旋比
    arm_pain_vas = Column(Integer, default=0)             # 肩臂疼痛 VAS (0-10)

    # 下肢 (膝部)
    total_impacts_7d = Column(Integer, default=0)         # 近7天总冲击次数
    jump_landing_quality = Column(Integer, default=7)     # 落地质量 (1-10)
    quad_hamstring_ratio = Column(Float, default=0.8)     # 股四/腘绳比
    footwork_score = Column(Integer, default=7)           # 步法评分 (1-10)
    leg_pain_vas = Column(Integer, default=0)             # 腿部疼痛 VAS (0-10)

    # 全身
    reaction_time_ms = Column(Integer, default=250)       # 反应时间 (ms)
    has_knee_pain_history = Column(Boolean, default=False)

    # === 计算的肩/膝风险值 ===
    shoulder_overuse_risk = Column(Float, default=0)      # 0-100
    shoulder_acute_risk = Column(Float, default=0)        # 0-100
    knee_overuse_risk = Column(Float, default=0)          # 0-100
    knee_acute_risk = Column(Float, default=0)            # 0-100

    # === 训练日志升级字段 ===
    rpe = Column(Integer, default=6)                      # 0-10 主观疲劳
    energy_level = Column(Integer, default=7)             # 1-10 精力水平
    muscle_soreness = Column(JSON, default=dict)          # {"shoulder":5,"quad":3,"calf":2}
    technical_notes = Column(Text)
    plan_vs_actual_diff = Column(Float)                   # 实际 vs 计划负荷偏差%
    completion_rate = Column(Float)                       # 完成率%
    media_urls = Column(JSON, default=list)               # 图片/视频URL列表

    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("athlete_id", "metric_date"),)


class AlertConfig(Base):
    """预警配置表 - 每个运动员可自定义各项指标的预警阈值"""
    __tablename__ = "alert_config"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    metric_name = Column(String(50), nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default="warning")  # "warning" / "critical"
    notify = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="alert_configs")


class RecoverySuggestion(Base):
    """每日恢复建议"""
    __tablename__ = "recovery_suggestions"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    date = Column(Date, nullable=False)
    suggestion_text = Column(Text)
    exercises = Column(JSON, default=list)  # [{name, sets, reps, duration, completed}]
    status = Column(String(20), default="pending")  # "pending" / "completed" / "skipped"
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    athlete = relationship("Athlete", back_populates="recovery_suggestions")


class TrainingTemplate(Base):
    """训练计划模板"""
    __tablename__ = "training_templates"
    id = _UID(primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), default="daily")          # "daily" / "weekly" / "periodized"
    sport = Column(String(50), default="羽毛球")
    intensity_zone = Column(String(20))                  # "低" / "中" / "高" / "极高"
    target_focus = Column(JSON, default=list)            # ["技术","步法","耐力"...]
    created_by = Column(String(36))
    is_public = Column(Boolean, default=True)
    weekly_frequency = Column(String(50))                 # "2-3次（非连续日）"
    content = Column(JSON, nullable=False)               # 模板内容 JSON
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingAssignment(Base):
    """训练计划分配"""
    __tablename__ = "training_assignments"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    template_id = _FKey("training_templates.id", ondelete="SET NULL")
    scheduled_date = Column(Date, nullable=False)
    overrides = Column(JSON, default=dict)                # 覆盖模板参数
    status = Column(String(20), default="scheduled")      # "scheduled"/"completed"/"missed"
    actual_log_id = _FKey("daily_metrics.id")              # 关联实际日志
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("athlete_id", "scheduled_date", "template_id"),)


class RehabExercise(Base):
    """康复动作库（NASM OPT 模型）"""
    __tablename__ = "rehab_exercises"
    id = _UID(primary_key=True)
    name = Column(String(100), nullable=False)
    target_body_part = Column(String(20))    # shoulder, knee, elbow, ankle, core
    nasm_phase = Column(String(20))          # inhibit, lengthen, activate, integrate
    purpose = Column(Text)
    difficulty = Column(Integer, default=2)  # 1-5
    equipment_needed = Column(JSON, default=list)
    instructions = Column(Text)
    common_mistakes = Column(Text)
    image_url = Column(String(255))
    video_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class RehabPlan(Base):
    """个性化康复计划"""
    __tablename__ = "rehab_plans"
    id = _UID(primary_key=True)
    athlete_id = _FKey("athletes.id", ondelete="CASCADE", nullable=False)
    name = Column(String(100))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")  # active, completed, expired
    created_by = Column(String(36))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class RehabPlanExercise(Base):
    """康复计划每日动作安排"""
    __tablename__ = "rehab_plan_exercises"
    id = _UID(primary_key=True)
    plan_id = _FKey("rehab_plans.id", ondelete="CASCADE", nullable=False)
    exercise_id = _FKey("rehab_exercises.id", ondelete="CASCADE", nullable=False)
    scheduled_date = Column(Date, nullable=False)
    sets = Column(Integer, default=3)
    reps = Column(String(20))                  # e.g., "10-15" or "30秒"
    rest_seconds = Column(Integer, default=60)
    order_index = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    pain_before = Column(Integer)              # VAS 0-10
    pain_after = Column(Integer)               # VAS 0-10
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = ()


