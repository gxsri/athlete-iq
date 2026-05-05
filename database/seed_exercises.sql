-- ============================================================================
-- AthleteIQ - 练习库种子数据
-- 涵盖所有训练类别的基础练习
-- ============================================================================

-- 基础力量 (8 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('深蹲', '基础力量', '杠铃后深蹲，主要发展下肢力量和核心稳定性', '{"default_weight_pct_1rm": 80, "default_reps": 5, "default_sets": 4, "default_rpe": 7}'),
('卧推', '基础力量', '杠铃平板卧推，主要发展上肢推力和胸部力量', '{"default_weight_pct_1rm": 80, "default_reps": 5, "default_sets": 4, "default_rpe": 7}'),
('硬拉', '基础力量', '传统硬拉，发展后链肌群（臀肌、腘绳肌、背部）', '{"default_weight_pct_1rm": 85, "default_reps": 3, "default_sets": 4, "default_rpe": 8}'),
('引体向上', '基础力量', '自重或负重引体向上，发展背部肌群和上肢拉力', '{"default_weight_pct_1rm": 0, "default_reps": 8, "default_sets": 4, "default_rpe": 7}'),
('俯卧撑', '基础力量', '自重俯卧撑，发展上肢推力和核心稳定性', '{"default_weight_pct_1rm": 0, "default_reps": 15, "default_sets": 3, "default_rpe": 5}'),
('杠铃划船', '基础力量', '俯身杠铃划船，发展背部厚度和上肢拉力', '{"default_weight_pct_1rm": 75, "default_reps": 6, "default_sets": 4, "default_rpe": 7}'),
('腿举', '基础力量', '器械腿举，孤立发展股四头肌和臀部力量', '{"default_weight_pct_1rm": 85, "default_reps": 8, "default_sets": 3, "default_rpe": 7}'),
('肩推', '基础力量', '杠铃或哑铃站姿/坐姿肩推，发展肩部力量', '{"default_weight_pct_1rm": 75, "default_reps": 6, "default_sets": 4, "default_rpe": 7}');

-- 爆发力 (6 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('高翻', '爆发力', '杠铃高翻，发展全身爆发力和三重伸展能力', '{"default_weight_pct_1rm": 70, "default_reps": 3, "default_sets": 5, "default_rpe": 7}'),
('抓举', '爆发力', '杠铃抓举，发展全身爆发力和速度力量', '{"default_weight_pct_1rm": 65, "default_reps": 3, "default_sets": 5, "default_rpe": 7}'),
('药球抛砸', '爆发力', '药球过顶抛砸，发展上肢和核心爆发力', '{"default_weight_pct_1rm": 0, "default_reps": 6, "default_sets": 4, "default_rpe": 8, "default_ball_weight_kg": 5}'),
('跳箱', '爆发力', '跳箱训练，发展下肢爆发力和发力率', '{"default_weight_pct_1rm": 0, "default_reps": 5, "default_sets": 4, "default_rpe": 7, "default_box_height_cm": 60}'),
('壶铃摆荡', '爆发力', '壶铃摆荡，发展后链爆发力和髋关节爆发力', '{"default_weight_pct_1rm": 0, "default_reps": 12, "default_sets": 4, "default_rpe": 7, "default_kb_weight_kg": 24}'),
('反向纵跳', '爆发力', 'CMJ 反向纵跳，发展垂直爆发力和发力率', '{"default_weight_pct_1rm": 0, "default_reps": 5, "default_sets": 4, "default_rpe": 8}');

-- 速度 (5 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('30m冲刺', '速度', '站立起跑 30 米冲刺，发展加速度', '{"default_weight_pct_1rm": 0, "default_reps": 4, "default_sets": 3, "default_rpe": 9, "default_rest_sec": 180}'),
('60m冲刺', '速度', '蹲踞式或站立式 60 米冲刺，发展加速和最大速度', '{"default_weight_pct_1rm": 0, "default_reps": 3, "default_sets": 2, "default_rpe": 9, "default_rest_sec": 240}'),
('敏捷梯', '速度', '敏捷梯步伐训练，发展脚步速度和协调性', '{"default_weight_pct_1rm": 0, "default_reps": 8, "default_sets": 3, "default_rpe": 6}'),
('折返跑', '速度', '20 米折返跑/Pro-Agility 测试，发展变向速度', '{"default_weight_pct_1rm": 0, "default_reps": 4, "default_sets": 3, "default_rpe": 8, "default_rest_sec": 120}'),
('反应起跑', '速度', '声音/信号触发起跑，发展反应速度和起跑技术', '{"default_weight_pct_1rm": 0, "default_reps": 6, "default_sets": 3, "default_rpe": 7, "default_rest_sec": 90}');

-- 代谢 (4 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('400m间歇', '代谢', '400 米间歇跑，发展乳酸阈能力和速度耐力', '{"default_weight_pct_1rm": 0, "default_reps": 6, "default_sets": 2, "default_rpe": 8, "default_rest_sec": 120}'),
('800m节奏跑', '代谢', '800 米节奏跑，发展有氧能力和跑步经济性', '{"default_weight_pct_1rm": 0, "default_reps": 4, "default_sets": 2, "default_rpe": 7, "default_rest_sec": 180}'),
('划船机间歇', '代谢', '划船机高强度间歇，发展全身有氧/无氧能力', '{"default_weight_pct_1rm": 0, "default_reps": 8, "default_sets": 3, "default_rpe": 8, "default_rest_sec": 60}'),
('自行车冲刺', '代谢', '功率自行车最大冲刺，发展下肢无氧功率', '{"default_weight_pct_1rm": 0, "default_reps": 5, "default_sets": 3, "default_rpe": 10, "default_rest_sec": 180}');

-- 恢复 (4 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('泡沫轴放松', '恢复', '全身泡沫轴自我肌筋膜放松，促进恢复', '{"default_weight_pct_1rm": 0, "default_reps": 1, "default_sets": 1, "default_rpe": 2, "default_duration_min": 20}'),
('静态拉伸', '恢复', '全身主要肌群静态拉伸，改善柔韧性和恢复', '{"default_weight_pct_1rm": 0, "default_reps": 1, "default_sets": 1, "default_rpe": 2, "default_duration_min": 15}'),
('冷水浸泡', '恢复', '10-15°C 冷水浸泡，减轻炎症和肌肉酸痛', '{"default_weight_pct_1rm": 0, "default_reps": 1, "default_sets": 1, "default_rpe": 1, "default_duration_min": 12}'),
('瑜伽', '恢复', '恢复性瑜伽，改善柔韧性、呼吸和身心放松', '{"default_weight_pct_1rm": 0, "default_reps": 1, "default_sets": 1, "default_rpe": 3, "default_duration_min": 30}');

-- 核心 (4 exercises)
INSERT INTO exercise_library (name, category, description, preset_params) VALUES
('平板支撑', '核心', '前平板支撑，发展核心耐力和稳定性', '{"default_weight_pct_1rm": 0, "default_reps": 1, "default_sets": 3, "default_rpe": 6, "default_duration_sec": 60}'),
('俄罗斯转体', '核心', '俄罗斯转体，发展腹斜肌和旋转核心力量', '{"default_weight_pct_1rm": 0, "default_reps": 15, "default_sets": 3, "default_rpe": 6}'),
('鸟狗式', '核心', '鸟狗式（Bird Dog），发展核心稳定性和对侧协调', '{"default_weight_pct_1rm": 0, "default_reps": 10, "default_sets": 3, "default_rpe": 4}'),
('死虫式', '核心', '死虫式（Dead Bug），发展深层核心和抗伸展控制', '{"default_weight_pct_1rm": 0, "default_reps": 12, "default_sets": 3, "default_rpe": 4}');
