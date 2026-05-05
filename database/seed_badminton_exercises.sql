-- ============================================================================
-- AthleteIQ - 羽毛球练习库种子数据
-- 包含技战术练习和专项体能测试基准
-- ============================================================================

-- 扩展 exercise_library 分类约束，支持羽毛球技战术
DO $$
BEGIN
    ALTER TABLE exercise_library DROP CONSTRAINT IF EXISTS exercise_library_category_check;
EXCEPTION
    WHEN undefined_object THEN NULL;
END $$;
ALTER TABLE exercise_library ADD CONSTRAINT exercise_library_category_check
    CHECK (category IN ('基础力量', '爆发力', '速度', '代谢', '恢复', '柔韧', '核心', '羽毛球-技战术'));

-- 创建运动员专项测试基准常模表
CREATE TABLE IF NOT EXISTS athlete_baselines_defaults (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    typical_value NUMERIC(10,3) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sport, metric_name)
);

-- ============================================================================
-- 后场技术 (4 exercises)
-- ============================================================================
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('高远球', '羽毛球-技战术', '后场正手/反手高远球多球练习，发展后场到位能力和击球控制', '{"duration_min": 15, "target_reps": 40, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "保持正确握拍、侧身转体和鞭打发力动作"}'),
('杀球', '羽毛球-技战术', '后场正手杀球多球练习，发展进攻火力和爆发力', '{"duration_min": 15, "target_reps": 25, "target_sets": 4, "target_rpe": 7, "rest_seconds": 45, "notes": "注意收腹转体连贯发力，击球点保持在最高点前方"}'),
('吊球', '羽毛球-技战术', '后场正手/滑板吊球练习，发展变化落点和战术欺骗能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 5, "rest_seconds": 30, "notes": "保持动作一致性，隐蔽性强，注意切/劈击角度"}'),
('平高球', '羽毛球-技战术', '后场平高球多球练习，发展快速过渡和压制能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "控制弧线和速度，平高快过而不是高远"}');

-- ============================================================================
-- 中场技术 (3 exercises)
-- ============================================================================
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('正手抽球', '羽毛球-技战术', '中场正手抽球多球练习，发展平快防守和过渡球能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "保持低重心，前臂旋转发力，拍面向前"}'),
('反手抽球', '羽毛球-技战术', '中场反手抽球多球练习，发展反手位置防守和过渡能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "注意转体和手腕发力，拇指顶住拍柄宽面"}'),
('挡网', '羽毛球-技战术', '中场挡网多球练习，发展防守中转近网球的能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 5, "rest_seconds": 20, "notes": "控制拍面角度和力度，力求贴网而过"}');

-- ============================================================================
-- 前场技术 (4 exercises)
-- ============================================================================
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('搓球', '羽毛球-技战术', '网前搓球多球练习，发展网前控球和旋转能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 5, "rest_seconds": 20, "notes": "手指手腕精控发力，拍面切击产生旋转"}'),
('推球', '羽毛球-技战术', '网前推球多球练习，发展网前快速压制的进攻能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "抢占高点，手腕爆发推压，球速快而平"}'),
('勾对角', '羽毛球-技战术', '网前勾对角多球练习，发展网前变线和战术欺骗能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "保持动作一致性，最后时刻改变拍面方向"}'),
('挑球', '羽毛球-技战术', '网前挑球多球练习，发展被动情况下的高远过渡能力', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 6, "rest_seconds": 30, "notes": "低重心发力，拍面向上挑送，控制高度和落点"}');

-- ============================================================================
-- 发球技术 (2 exercises)
-- ============================================================================
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('正手发高远球', '羽毛球-技战术', '正手发高远球练习，发展发球环节的到位率和稳定性', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 5, "rest_seconds": 25, "notes": "侧身站姿，手腕鞭打发力，追求高度和落点精准"}'),
('反手发网前球', '羽毛球-技战术', '反手发网前球练习，发展双打发球质量和稳定性', '{"duration_min": 15, "target_reps": 30, "target_sets": 4, "target_rpe": 4, "rest_seconds": 20, "notes": "拇指顶拍柄，手指手腕精控，力求贴网过发球线"}');

-- ============================================================================
-- 步法训练 (2 exercises)
-- ============================================================================
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('前后场连贯步法', '羽毛球-技战术', '全场前后跑动步法练习，发展场上的快速移动和重心转换能力', '{"duration_min": 20, "target_reps": 20, "target_sets": 5, "target_rpe": 7, "rest_seconds": 45, "notes": "保持低重心，蹬转起跳连贯，回中意识"}'),
('左右摸边', '羽毛球-技战术', '底线左右摸边步法练习，发展防守覆盖范围和侧移速度', '{"duration_min": 15, "target_reps": 40, "target_sets": 4, "target_rpe": 7, "rest_seconds": 30, "notes": "并步/交叉步交替，注重启动和制动的爆发力"}');

-- ============================================================================
-- 羽毛球专项体能测试基准 - 常模数据
-- ============================================================================
INSERT INTO athlete_baselines_defaults (sport, metric_name, typical_value, description) VALUES
('羽毛球', 'shuttle_run_sec', 32.0, '专项折返跑(秒) - 模拟场上前后左右折返跑'),
('羽毛球', 'vertical_jump_cm', 55.0, '垂直纵跳高度(cm) - 反映下肢爆发力'),
('羽毛球', 'grip_strength_left_kg', 40.0, '左手握力(kg) - 反映前臂和手腕力量'),
('羽毛球', 'grip_strength_right_kg', 45.0, '右手握力(kg) - 反映前臂和手腕力量'),
('羽毛球', 'y_balance_left_cm', 90.0, 'Y平衡测试左侧(cm) - 反映下肢动态稳定性'),
('羽毛球', 'y_balance_right_cm', 92.0, 'Y平衡测试右侧(cm) - 反映下肢动态稳定性'),
('羽毛球', 'shoulder_rom_left_deg', 180.0, '左肩关节活动度(°) - 反映肩关节柔韧性'),
('羽毛球', 'shoulder_rom_right_deg', 180.0, '右肩关节活动度(°) - 反映肩关节柔韧性');
