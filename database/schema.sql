-- ============================================================================
-- AthleteIQ - 运动员数据监测系统 数据库 Schema
-- 基于 NSCA-CSCS / CPSS 标准设计
-- PostgreSQL 15+
-- ============================================================================

-- 1. 运动员档案表 (Athlete Profile)
CREATE TABLE athletes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('男', '女', '其他')),
    sport VARCHAR(50) NOT NULL,
    position_or_event VARCHAR(100),
    training_years NUMERIC(4,1) CHECK (training_years >= 0),
    injury_history TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(30),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. 运动员个人基准值表 (Individual Baseline)
-- 每个运动员的正常生理范围和测试基准
CREATE TABLE athlete_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,  -- e.g., 'heart_rate_resting', 'hrv_lnrmssd', 'squat_1rm', 'vo2max'
    baseline_value NUMERIC(10,3) NOT NULL,
    -- 典型误差 (Typical Error, TE)，用于 CV% 最小有效差异计算
    typical_error NUMERIC(10,3),
    -- 最小有效差异 (Smallest Worthwhile Change, SWC)
    swc NUMERIC(10,3),
    established_at DATE NOT NULL,
    valid_until DATE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, metric_name, established_at)
);

-- 3. 训练日志表 (Training Log)
-- CPSS 标准：Session RPE = Duration × RPE
CREATE TABLE training_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    training_date DATE NOT NULL,
    duration_minutes NUMERIC(5,1) CHECK (duration_minutes > 0),
    rpe INTEGER CHECK (rpe BETWEEN 1 AND 10),
    -- 训练类型: 力量/耐力/速度/技战术/柔韧/混合
    training_type VARCHAR(20) CHECK (training_type IN ('力量', '耐力', '速度', '技战术', '柔韧', '混合')),
    -- 自动计算的 Session RPE Load
    session_load NUMERIC(10,1) GENERATED ALWAYS AS (duration_minutes * rpe) STORED,
    -- 训练内容详情
    description TEXT,
    -- 训练周期阶段: preparation/competition/transition
    cycle_phase VARCHAR(20) CHECK (cycle_phase IN ('准备期', '比赛期', '过渡期')),
    coach_notes TEXT,
    tags JSONB DEFAULT '[]',
    source VARCHAR(30) DEFAULT 'manual',  -- 'manual', 'csv_import', 'api_garmin', 'api_polar'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, training_date)
);

-- 索引: 按日期范围查询训练负荷
CREATE INDEX idx_training_logs_date ON training_logs (athlete_id, training_date);

-- 4. 体能测试记录表 (Performance Test Record)
CREATE TABLE performance_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    test_date DATE NOT NULL,
    -- 力量指标
    squat_1rm_kg NUMERIC(7,2),
    bench_press_1rm_kg NUMERIC(7,2),
    deadlift_1rm_kg NUMERIC(7,2),
    cmj_height_cm NUMERIC(5,2),           -- 反向纵跳高度 (Countermovement Jump)
    rfd_n_per_s NUMERIC(8,2),             -- 发力率 (Rate of Force Development)
    -- 爆发力/速度指标
    sprint_30m_sec NUMERIC(5,3),
    standing_long_jump_cm NUMERIC(5,1),
    med_ball_throw_m NUMERIC(5,2),
    -- 代谢能力指标
    vo2max_ml_kg_min NUMERIC(6,2),
    lactate_threshold_power_w NUMERIC(7,1),
    lactate_threshold_pace VARCHAR(20),   -- 格式: "3:45/km"
    -- 测试环境/备注
    test_protocol VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, test_date)
);

CREATE INDEX idx_perf_tests_date ON performance_tests (athlete_id, test_date);

-- 5. 每日恢复/健康问卷表 (Daily Wellness Questionnaire)
CREATE TABLE wellness_questionnaires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    -- 晨起静息心率 (bpm)
    morning_heart_rate INTEGER CHECK (morning_heart_rate BETWEEN 30 AND 120),
    -- 心率变异性 (LnRMSSD, ms)
    hrv_lnrmssd NUMERIC(6,2),
    -- 睡眠
    sleep_duration_hours NUMERIC(4,1) CHECK (sleep_duration_hours BETWEEN 0 AND 15),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 5),
    -- 主观评分 (1-5)
    fatigue_score INTEGER CHECK (fatigue_score BETWEEN 1 AND 5),
    muscle_soreness INTEGER CHECK (muscle_soreness BETWEEN 1 AND 5),
    stress_score INTEGER CHECK (stress_score BETWEEN 1 AND 5),
    mood_score INTEGER CHECK (mood_score BETWEEN 1 AND 5),
    -- 身体质量
    body_weight_kg NUMERIC(5,1),
    -- 额外备注
    illness_flag BOOLEAN DEFAULT FALSE,
    notes TEXT,
    source VARCHAR(30) DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, record_date)
);

CREATE INDEX idx_wellness_date ON wellness_questionnaires (athlete_id, record_date);

-- 6. 计算指标汇总表 (Computed Metrics - 物化/缓存计算)
CREATE TABLE computed_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    calc_date DATE NOT NULL,
    -- ACWR 相关
    acute_load_7d NUMERIC(10,1),
    chronic_load_28d NUMERIC(10,1),
    acwr NUMERIC(6,3),
    acwr_risk_zone VARCHAR(20) CHECK (acwr_risk_zone IN ('安全区', '谨慎区', '高风险区')),
    -- 单调性与应变
    monotony NUMERIC(6,3),
    strain NUMERIC(10,1),
    strain_zscore NUMERIC(6,3),  -- 与历史基线比较的 Z-Score
    -- RSSI 综合指数
    rssi_score NUMERIC(6,2),
    rssi_risk_level VARCHAR(30) CHECK (rssi_risk_level IN ('正常', '适应性训练', '功能性过度训练', '非功能性过度训练', '需医学评估')),
    -- 子维度评分
    acwr_component NUMERIC(5,2),
    hr_component NUMERIC(5,2),
    hrv_component NUMERIC(5,2),
    fatigue_component NUMERIC(5,2),
    performance_component NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, calc_date)
);

CREATE INDEX idx_metrics_date ON computed_metrics (athlete_id, calc_date);

-- 7. 预警事件表 (Alert Events)
CREATE TABLE alert_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    alert_date DATE NOT NULL,
    alert_type VARCHAR(30) CHECK (alert_type IN ('ACWR过高', 'ACWR过低', '过度训练', 'HRV下降', '晨起心率升高',
                                                  '力量下降', '恢复不足', '负荷异常', '训练单调性过高')),
    severity VARCHAR(10) CHECK (severity IN ('低', '中', '高', '严重')),
    alert_source VARCHAR(50),    -- 触发此预警的指标详情
    current_value TEXT,           -- JSON: 具体触发值
    recommended_action TEXT,      -- 自动生成的建议措施
    is_read BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    coach_notes TEXT,
    coach_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_athlete ON alert_events (athlete_id, alert_date, is_resolved);
CREATE INDEX idx_alerts_severity ON alert_events (severity, is_resolved);

-- 8. 训练周期计划表 (Periodization Plan)
CREATE TABLE periodization_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    plan_name VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cycle_type VARCHAR(20) CHECK (cycle_type IN ('准备期', '比赛期', '过渡期')),
    -- JSON 存储每周计划模板
    -- [{"week":1, "sessions":[{"type":"力量", "load_pct":80, "rpe_target":7}, ...]}, ...]
    weekly_template JSONB DEFAULT '[]',
    coach_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK(end_date > start_date)
);

-- 9. 用户/教练表 (Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'coach', 'athlete')),
    athlete_id UUID REFERENCES athletes(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. 数据导入日志 (Data Import Log)
CREATE TABLE import_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    file_name VARCHAR(255),
    data_type VARCHAR(30),       -- 'training', 'wellness', 'performance_test'
    records_imported INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    source_format VARCHAR(30),   -- 'csv', 'excel', 'api'
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 视图: 运动员当前状态总览 (方便仪表板快速查询)
-- ============================================================================
CREATE VIEW athlete_current_status AS
SELECT
    a.id AS athlete_id,
    a.name,
    a.sport,
    cm.calc_date,
    cm.acwr,
    cm.acwr_risk_zone,
    cm.rssi_score,
    cm.rssi_risk_level,
    cm.monotony,
    cm.strain,
    wq.morning_heart_rate,
    wq.hrv_lnrmssd,
    wq.sleep_duration_hours,
    wq.fatigue_score
FROM athletes a
LEFT JOIN LATERAL (
    SELECT * FROM computed_metrics
    WHERE athlete_id = a.id
    ORDER BY calc_date DESC LIMIT 1
) cm ON TRUE
LEFT JOIN LATERAL (
    SELECT * FROM wellness_questionnaires
    WHERE athlete_id = a.id
    ORDER BY record_date DESC LIMIT 1
) wq ON TRUE;

-- ============================================================================
-- 函数: 计算给定运动员在指定日期的 ACWR
-- ============================================================================
CREATE OR REPLACE FUNCTION calculate_acwr(
    p_athlete_id UUID,
    p_date DATE,
    p_acute_window INTEGER DEFAULT 7,
    p_chronic_window INTEGER DEFAULT 28
) RETURNS TABLE (
    acute_load NUMERIC(10,1),
    chronic_load NUMERIC(10,1),
    acwr NUMERIC(6,3),
    risk_zone VARCHAR(20)
) AS $$
DECLARE
    v_acute_avg NUMERIC(10,1);
    v_chronic_avg NUMERIC(10,1);
    v_acwr NUMERIC(6,3);
    v_risk VARCHAR(20);
BEGIN
    -- 计算急性负荷 (7天滚动平均)
    SELECT COALESCE(AVG(session_load), 0) INTO v_acute_avg
    FROM training_logs
    WHERE athlete_id = p_athlete_id
      AND training_date > (p_date - p_acute_window)
      AND training_date <= p_date;

    -- 计算慢性负荷 (28天滚动平均)
    SELECT COALESCE(AVG(session_load), 0) INTO v_chronic_avg
    FROM training_logs
    WHERE athlete_id = p_athlete_id
      AND training_date > (p_date - p_chronic_window)
      AND training_date <= p_date;

    -- ACWR
    IF v_chronic_avg > 0 THEN
        v_acwr := ROUND((v_acute_avg / v_chronic_avg)::NUMERIC, 3);
    ELSE
        v_acwr := 0;
    END IF;

    -- 风险区间判定 (NSCA共识)
    IF v_acwr = 0 THEN
        v_risk := '安全区';
    ELSIF v_acwr >= 0.8 AND v_acwr <= 1.3 THEN
        v_risk := '安全区';
    ELSIF v_acwr > 1.3 AND v_acwr <= 1.5 THEN
        v_risk := '谨慎区';
    ELSE
        v_risk := '高风险区';
    END IF;

    RETURN QUERY SELECT v_acute_avg, v_chronic_avg, v_acwr, v_risk;
END;
$$ LANGUAGE plpgsql;
