-- ============================================================================
-- AthleteIQ - 营养监测模块 Schema
-- ============================================================================

CREATE TABLE nutrition_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    protein_sufficient VARCHAR(3) CHECK (protein_sufficient IN ('是','否','约量')),
    post_training_refuel BOOLEAN DEFAULT FALSE,  -- 训练后30分钟补充
    water_intake_liters NUMERIC(3,1) CHECK (water_intake_liters >= 0),
    appetite_score INTEGER CHECK (appetite_score BETWEEN 1 AND 5),
    morning_weight_kg NUMERIC(5,1),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(athlete_id, log_date)
);

CREATE INDEX idx_nutrition_date ON nutrition_logs (athlete_id, log_date);
