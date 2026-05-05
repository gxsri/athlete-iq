-- ============================================================================
-- AthleteIQ - 数据库 Schema 扩展
-- 添加训练计划、伤病管理、团队管理、练习库等新表
-- ============================================================================

-- 11. 每日准备度问卷表 (Daily Readiness Survey)
CREATE TABLE daily_readiness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 5),
    muscle_soreness INTEGER CHECK (muscle_soreness BETWEEN 1 AND 5),
    fatigue_level INTEGER CHECK (fatigue_level BETWEEN 1 AND 5),
    stress_motivation INTEGER CHECK (stress_motivation BETWEEN 1 AND 5),
    discomfort_notes TEXT,
    readiness_color VARCHAR(10) CHECK (readiness_color IN ('green', 'yellow', 'red')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, record_date)
);

CREATE INDEX idx_daily_readiness_date ON daily_readiness (athlete_id, record_date);

-- 12. 练习库表 (Exercise Library)
CREATE TABLE exercise_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(30) CHECK (category IN ('基础力量', '爆发力', '速度', '代谢', '恢复', '柔韧', '核心')),
    description TEXT,
    preset_params JSONB,
    coach_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, coach_id)
);

CREATE INDEX idx_exercise_library_category ON exercise_library (category);

-- 13. 计划训练课表 (Planned Sessions)
CREATE TABLE planned_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    created_by UUID REFERENCES users(id),
    session_name VARCHAR(100),
    training_type VARCHAR(20) CHECK (training_type IN ('力量', '耐力', '速度', '技战术', '柔韧', '混合')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_planned_sessions_athlete ON planned_sessions (athlete_id, plan_date);

-- 14. 计划练习表 (Planned Exercises - 属于 planned_sessions)
CREATE TABLE planned_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planned_session_id UUID NOT NULL REFERENCES planned_sessions(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercise_library(id),
    order_index INTEGER NOT NULL,
    target_weight_kg NUMERIC(7,2),
    target_reps INTEGER,
    target_sets INTEGER,
    rest_seconds INTEGER,
    target_rpe INTEGER CHECK (target_rpe BETWEEN 1 AND 10),
    notes TEXT,
    UNIQUE(planned_session_id, order_index)
);

-- 15. 练习执行日志表 (Exercise Logs - 关联训练记录与练习库)
CREATE TABLE exercise_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_log_id UUID NOT NULL REFERENCES training_logs(id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercise_library(id),
    order_index INTEGER,
    actual_weight_kg NUMERIC(7,2),
    actual_reps INTEGER,
    actual_sets INTEGER,
    actual_rpe INTEGER CHECK (actual_rpe BETWEEN 1 AND 10),
    planned_exercise_id UUID REFERENCES planned_exercises(id),
    notes TEXT
);

CREATE INDEX idx_exercise_logs_training ON exercise_logs (training_log_id);

-- 16. 教练反馈/评论表 (Coach Comments)
CREATE TABLE coach_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    training_log_id UUID REFERENCES training_logs(id),
    created_by UUID NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coach_comments_athlete ON coach_comments (athlete_id, created_at);

-- 17. 伤病记录表 (Injury Records)
CREATE TABLE injury_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    diagnosis TEXT NOT NULL,
    injury_date DATE NOT NULL,
    expected_recovery_weeks NUMERIC(4,1),
    actual_return_date DATE,
    status VARCHAR(20) CHECK (status IN ('活跃', '康复中', '已恢复')),
    body_part VARCHAR(50),
    severity VARCHAR(10) CHECK (severity IN ('轻度', '中度', '重度')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_injury_records_athlete ON injury_records (athlete_id, status);

-- 18. 伤病康复日志表 (Injury Rehab Logs)
CREATE TABLE injury_rehab_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    injury_record_id UUID NOT NULL REFERENCES injury_records(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    pain_score INTEGER CHECK (pain_score BETWEEN 0 AND 10),
    rehab_completion_pct NUMERIC(5,1),
    exercises_completed TEXT,
    notes TEXT
);

CREATE INDEX idx_injury_rehab_logs ON injury_rehab_logs (injury_record_id, log_date);

-- 19. 伤病训练限制表 (Injury Restrictions)
CREATE TABLE injury_restrictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    injury_record_id UUID NOT NULL REFERENCES injury_records(id) ON DELETE CASCADE,
    restriction_type VARCHAR(50) CHECK (restriction_type IN ('禁止动作', '负荷限制', 'RoM限制')),
    restriction_detail TEXT NOT NULL,
    exercise_name_pattern VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_injury_restrictions ON injury_restrictions (injury_record_id);

-- 20. 重返赛场清单表 (Return to Play Checklist)
CREATE TABLE return_to_play_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    injury_record_id UUID NOT NULL REFERENCES injury_records(id) ON DELETE CASCADE,
    check_item VARCHAR(200) NOT NULL,
    target_value NUMERIC(10,3),
    actual_value NUMERIC(10,3),
    unit VARCHAR(20),
    is_passed BOOLEAN DEFAULT FALSE,
    passed_date DATE,
    notes TEXT
);

CREATE INDEX idx_rtp_checklist ON return_to_play_checklist (injury_record_id);

-- 21. 团队分组表 (Team Groups)
CREATE TABLE team_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    coach_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 22. 团队分组成员表 (Team Group Members)
CREATE TABLE team_group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES team_groups(id) ON DELETE CASCADE,
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    UNIQUE(group_id, athlete_id)
);

CREATE INDEX idx_team_group_members_group ON team_group_members (group_id);
CREATE INDEX idx_team_group_members_athlete ON team_group_members (athlete_id);

-- 23. 周期化模板表 (Periodization Templates)
CREATE TABLE periodization_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    template_type VARCHAR(30) CHECK (template_type IN ('线性周期', '非线性DUP', '板块周期')),
    cycle_phase VARCHAR(20) CHECK (cycle_phase IN ('一般准备期', '专项准备期', '比赛期', '过渡期')),
    description TEXT,
    weekly_structure JSONB DEFAULT '[]',
    coach_id UUID,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_periodization_templates ON periodization_templates (template_type, cycle_phase);
