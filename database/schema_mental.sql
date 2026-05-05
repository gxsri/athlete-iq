-- ============================================================================
-- AthleteIQ - 心理监测模块 Schema
-- ============================================================================

CREATE TABLE mental_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    mood_score INTEGER CHECK (mood_score BETWEEN 1 AND 5),
    focus_score INTEGER CHECK (focus_score BETWEEN 1 AND 5),
    motivation_score INTEGER CHECK (motivation_score BETWEEN 1 AND 5),
    mental_fatigue_score INTEGER CHECK (mental_fatigue_score BETWEEN 1 AND 5),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, log_date)
);

CREATE INDEX idx_mental_date ON mental_logs (athlete_id, log_date);
