-- ============================================================================
-- AthleteIQ - 周期化模板种子数据
-- 基于 NSCA 周期化训练模型
-- ============================================================================

-- 1. 线性周期 - 一般准备期 (4周递增)
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('线性周期 - 一般准备期 (基础建设)', '线性周期', '一般准备期',
 '经典线性周期模型：每周逐渐增加强度 (负荷%) 同时逐步降低容量 (组数×次数)。适合建立力量和有氧基础。',
 '[
  {"week": 1, "focus": "适应周", "volume_multiplier": 1.0, "intensity_pct": 65,
   "sessions": [
     {"day": "周一", "type": "力量 (下肢)", "description": "深蹲 4x8@65%, 硬拉 4x8@65%, 腿举 3x10"},
     {"day": "周二", "type": "有氧耐力", "description": "40分钟稳态有氧 (HR 130-150 bpm)"},
     {"day": "周三", "type": "力量 (上肢)", "description": "卧推 4x8@65%, 肩推 3x8@65%, 杠铃划船 4x8@65%"},
     {"day": "周四", "type": "速度/灵敏", "description": "敏捷梯 3x8 动作, 30m冲刺 4x"},
     {"day": "周五", "type": "力量 (全身)", "description": "高翻 5x3@65%, 深蹲 3x6@70%, 核心 3组"},
     {"day": "周六", "type": "专项技术", "description": "项目专项技术训练 60分钟"},
     {"day": "周日", "type": "恢复", "description": "主动恢复日 (拉伸/泡沫轴)"}
   ]
  },
  {"week": 2, "focus": "渐进周", "volume_multiplier": 0.95, "intensity_pct": 70,
   "sessions": [
     {"day": "周一", "type": "力量 (下肢)", "description": "深蹲 4x7@70%, 硬拉 4x7@70%, 腿举 3x10"},
     {"day": "周二", "type": "有氧耐力", "description": "40分钟稳态有氧"},
     {"day": "周三", "type": "力量 (上肢)", "description": "卧推 4x7@70%, 肩推 3x7@70%, 杠铃划船 4x7@70%"},
     {"day": "周四", "type": "速度/灵敏", "description": "敏捷梯 4x, 折返跑 4x"},
     {"day": "周五", "type": "力量 (全身)", "description": "高翻 5x3@70%, 深蹲 3x5@75%, 核心"},
     {"day": "周六", "type": "专项技术", "description": "项目专项技术训练"},
     {"day": "周日", "type": "恢复", "description": "主动恢复日"}
   ]
  },
  {"week": 3, "focus": "强度周", "volume_multiplier": 0.88, "intensity_pct": 77,
   "sessions": [
     {"day": "周一", "type": "力量 (下肢)", "description": "深蹲 4x5@77%, 硬拉 4x5@77%, 腿举 3x8"},
     {"day": "周二", "type": "有氧耐力", "description": "35分钟稳态有氧 + 10分钟间歇"},
     {"day": "周三", "type": "力量 (上肢)", "description": "卧推 4x5@77%, 肩推 3x5@77%, 杠铃划船 4x5@77%"},
     {"day": "周四", "type": "爆发力", "description": "高翻 5x3@75%, 跳箱 4x5"},
     {"day": "周五", "type": "力量 (全身)", "description": "深蹲 3x4@80%, 卧推 3x4@80%, 核心"},
     {"day": "周六", "type": "专项技术", "description": "项目专项技术训练"},
     {"day": "周日", "type": "恢复", "description": "主动恢复日"}
   ]
  },
  {"week": 4, "focus": "减载周", "volume_multiplier": 0.6, "intensity_pct": 75,
   "sessions": [
     {"day": "周一", "type": "轻力量维持", "description": "深蹲 2x5@75%, 卧推 2x5@75%, 硬拉 2x4@75%"},
     {"day": "周二", "type": "有氧恢复", "description": "30分钟轻松有氧"},
     {"day": "周三", "type": "轻力量维持", "description": "腿举 2x8, 划船 2x6, 肩推 2x6"},
     {"day": "周四", "type": "恢复", "description": "全面恢复: 拉伸 + 泡沫轴 + 冷水浸泡"},
     {"day": "周五", "type": "专项技术", "description": "低强度技术训练"},
     {"day": "周六", "type": "交叉训练", "description": "娱乐性运动 (游泳/自行车)"},
     {"day": "周日", "type": "完全休息", "description": "休息日"}
   ]
  }
 ]'::jsonb, TRUE);

-- 2. 非线性 DUP - 专项准备期 (日波动)
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('非线性DUP - 专项准备期 (Daily Undulating)', '非线性DUP', '专项准备期',
 '每日波动周期化 (Daily Undulating Periodization)：周一肌肥大、周三最大力量、周五爆发力，在同一个训练周内交替训练目标。',
 '[
  {"week": 1, "focus": "DUP 基础周", "sessions": [
    {"day": "周一", "type": "肌肥大 (Hypertrophy)", "rpe_target": 7, "description": "深蹲 4x10@65%, 卧推 4x10@65%, 杠铃划船 4x10, 肩推 3x10, 腿举 3x12"},
    {"day": "周二", "type": "有氧耐力 + 核心", "rpe_target": 5, "description": "35分钟稳态有氧 + 平板支撑 3x60s + 俄罗斯转体 3x15"},
    {"day": "周三", "type": "最大力量 (Max Strength)", "rpe_target": 8, "description": "深蹲 5x4@85%, 卧推 5x4@85%, 硬拉 4x3@87%, 引体向上 4x6"},
    {"day": "周四", "type": "速度/灵敏", "rpe_target": 6, "description": "30m冲刺 6x, 敏捷梯 4x, 反应起跑 5x"},
    {"day": "周五", "type": "爆发力 (Power)", "rpe_target": 7, "description": "高翻 6x3@70%, 抓举 5x2@65%, 跳箱 4x5, 药球抛砸 4x6"},
    {"day": "周六", "type": "专项技术/实战", "rpe_target": 7, "description": "项目专项技术训练或模拟比赛"},
    {"day": "周日", "type": "恢复", "rpe_target": 2, "description": "主动恢复 (泡沫轴、拉伸、冷水浸泡)"}
  ]},
  {"week": 2, "focus": "DUP 渐进周", "sessions": [
    {"day": "周一", "type": "肌肥大", "rpe_target": 7, "description": "深蹲 4x10@67%, 卧推 4x10@67%, 杠铃划船 4x10, 肩推 3x10, 腿举 3x12"},
    {"day": "周二", "type": "有氧耐力 + 核心", "rpe_target": 5, "description": "35分钟稳态有氧 + 核心训练"},
    {"day": "周三", "type": "最大力量", "rpe_target": 8, "description": "深蹲 5x3@87%, 卧推 5x3@87%, 硬拉 4x3@89%, 引体向上 4x5"},
    {"day": "周四", "type": "速度/灵敏", "rpe_target": 6, "description": "60m冲刺 4x, 折返跑 4x, 敏捷梯"},
    {"day": "周五", "type": "爆发力", "rpe_target": 7, "description": "高翻 5x3@72%, 抓举 5x2@67%, 跳箱 5x5, 壶铃摆荡 4x12"},
    {"day": "周六", "type": "专项技术", "rpe_target": 7, "description": "项目专项技术训练"},
    {"day": "周日", "type": "恢复", "rpe_target": 2, "description": "主动恢复"}
  ]},
  {"week": 3, "focus": "DUP 强度峰值周", "sessions": [
    {"day": "周一", "type": "肌肥大", "rpe_target": 7, "description": "深蹲 4x8@70%, 卧推 4x8@70%, 杠铃划船 4x8, 肩推 3x8, 腿举 3x10"},
    {"day": "周二", "type": "有氧耐力 + 核心", "rpe_target": 5, "description": "30分钟稳态有氧 + 间歇冲刺 4x200m"},
    {"day": "周三", "type": "最大力量", "rpe_target": 9, "description": "深蹲 4x2@90%, 卧推 4x2@90%, 硬拉 3x2@92%, 引体向上 4x4（负重）"},
    {"day": "周四", "type": "速度/灵敏", "rpe_target": 6, "description": "30m冲刺 6x (计时), 反应起跑 6x"},
    {"day": "周五", "type": "爆发力", "rpe_target": 8, "description": "高翻 4x2@78%, 抓举 4x2@72%, 跳箱 5x5（最高箱）"},
    {"day": "周六", "type": "专项技术", "rpe_target": 7, "description": "项目专项技术训练"},
    {"day": "周日", "type": "恢复", "rpe_target": 2, "description": "主动恢复"}
  ]},
  {"week": 4, "focus": "DUP 减载周", "sessions": [
    {"day": "周一", "type": "轻量维持", "rpe_target": 5, "description": "深蹲 2x5@75%, 卧推 2x5@75%"},
    {"day": "周二", "type": "恢复有氧", "rpe_target": 3, "description": "25分钟轻松骑行"},
    {"day": "周三", "type": "轻量力量", "rpe_target": 5, "description": "硬拉 2x4@80%, 肩推 2x5@75%"},
    {"day": "周四", "type": "恢复", "rpe_target": 2, "description": "全面恢复日"},
    {"day": "周五", "type": "爆发维持", "rpe_target": 5, "description": "高翻 3x2@70%, 跳箱 3x3"},
    {"day": "周六", "type": "交叉训练", "rpe_target": 4, "description": "娱乐性运动"},
    {"day": "周日", "type": "完全休息", "rpe_target": 1, "description": "休息日"}
  ]}
 ]'::jsonb, TRUE);

-- 3. 板块周期 - 比赛期 (2周集中+1周恢复)
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('板块周期 - 比赛期 (集中负荷+恢复)', '板块周期', '比赛期',
 '板块周期模型：2周集中专项训练 + 1周恢复减量。在比赛期内维持竞技状态的同时进行阶段性负荷刺激。',
 '[
  {"week": 1, "focus": "板块1: 集中力量", "volume_multiplier": 1.0, "sessions": [
    {"day": "周一", "type": "力量 (下肢)", "description": "深蹲 4x4@85%, 硬拉 4x4@85%, 腿举 3x6"},
    {"day": "周二", "type": "比赛强度技术", "description": "专项技术，比赛节奏和战术演练"},
    {"day": "周三", "type": "力量 (上肢) + 爆发", "description": "卧推 4x4@85%, 高翻 5x3@75%, 跳箱 4x5"},
    {"day": "周四", "type": "速度维持", "description": "30m冲刺 4x, 敏捷训练, 轻量激活"},
    {"day": "周五", "type": "全身力量", "description": "深蹲 3x3@87%, 卧推 3x3@87%, 核心训练"},
    {"day": "周六", "type": "比赛/高强度实战", "description": "比赛日或高强度实战模拟"},
    {"day": "周日", "type": "恢复", "description": "赛后/实战后恢复"}
  ]},
  {"week": 2, "focus": "板块1: 集中爆发力", "volume_multiplier": 0.85, "sessions": [
    {"day": "周一", "type": "爆发力 (下肢)", "description": "高翻 5x2@80%, 抓举 4x2@75%, 跳箱 5x4"},
    {"day": "周二", "type": "比赛强度技术", "description": "专项技术，比赛节奏"},
    {"day": "周三", "type": "爆发力 (全身)", "description": "药球抛砸 5x5, 壶铃摆荡 4x12, 深蹲跳 4x4"},
    {"day": "周四", "type": "速度 + 恢复", "description": "40m冲刺 3x, 泡沫轴 + 拉伸"},
    {"day": "周五", "type": "轻量维持 + 核心", "description": "深蹲 2x5@80%, 卧推 2x5@80%, 核心"},
    {"day": "周六", "type": "比赛/高强度实战", "description": "比赛日或高强度实战模拟"},
    {"day": "周日", "type": "恢复", "description": "赛后恢复"}
  ]},
  {"week": 3, "focus": "恢复减量周", "volume_multiplier": 0.5, "sessions": [
    {"day": "周一", "type": "轻量力量维持", "description": "深蹲 2x3@80%, 卧推 2x3@80%, 硬拉 2x3@80%"},
    {"day": "周二", "type": "技术训练", "description": "低强度技术训练"},
    {"day": "周三", "type": "主动恢复", "description": "拉伸、泡沫轴、冷水浸泡"},
    {"day": "周四", "type": "轻量爆发", "description": "高翻 2x2@70%, 跳箱 2x3"},
    {"day": "周五", "type": "赛前激活", "description": "赛前一天: 轻量激活 + 技术确认"},
    {"day": "周六", "type": "比赛日", "description": "正式比赛"},
    {"day": "周日", "type": "赛后恢复", "description": "全面恢复日"}
  ]},
  {"week": 4, "focus": "板块2: 集中力量", "volume_multiplier": 1.0, "sessions": [
    {"day": "周一", "type": "力量 (下肢)", "description": "深蹲 4x4@87%, 硬拉 4x3@90%, 腿举 3x6"},
    {"day": "周二", "type": "比赛强度技术", "description": "专项技术，比赛节奏"},
    {"day": "周三", "type": "力量 (上肢) + 爆发", "description": "卧推 4x4@87%, 高翻 5x3@80%, 跳箱 4x5"},
    {"day": "周四", "type": "速度维持", "description": "30m冲刺 4x, 轻量敏捷"},
    {"day": "周五", "type": "全身力量", "description": "深蹲 3x3@90%, 卧推 3x3@90%, 核心"},
    {"day": "周六", "type": "比赛/高强度实战", "description": "比赛日或高强度实战模拟"},
    {"day": "周日", "type": "恢复", "description": "赛后恢复"}
  ]}
 ]'::jsonb, TRUE);

-- 4. 过渡期 - 主动恢复
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('过渡期 - 主动恢复', '线性周期', '过渡期',
 '赛季后过渡恢复期：以低强度交叉训练和主动恢复为主，允许身体和心理全面恢复。为期 2-4 周。',
 '[
  {"week": 1, "focus": "身心恢复周", "sessions": [
    {"day": "周一", "type": "休息/轻度拉伸", "description": "自主拉伸 15分钟"},
    {"day": "周二", "type": "交叉训练 (游泳)", "description": "轻松游泳 30分钟，非竞技"},
    {"day": "周三", "type": "休息日", "description": "完全休息"},
    {"day": "周四", "type": "全身轻力量 + 核心", "description": "深蹲 2x8@50%, 卧推 2x8@50%, 引体向上 2x6, 核心 2组"},
    {"day": "周五", "type": "娱乐性运动", "description": "篮球/足球/骑行，以娱乐为目的"},
    {"day": "周六", "type": "轻度有氧 + 拉伸", "description": "25分钟轻松跑 + 15分钟静态拉伸"},
    {"day": "周日", "type": "休息日", "description": "完全休息"}
  ]},
  {"week": 2, "focus": "渐进恢复周", "sessions": [
    {"day": "周一", "type": "瑜伽/拉伸", "description": "恢复性瑜伽 30分钟"},
    {"day": "周二", "type": "交叉训练 (自行车)", "description": "轻松骑行 40分钟"},
    {"day": "周三", "type": "休息日", "description": "完全休息"},
    {"day": "周四", "type": "全身轻力量", "description": "深蹲 3x8@55%, 卧推 3x8@55%, 划船 3x8, 肩推 2x8"},
    {"day": "周五", "type": "娱乐性运动", "description": "选择喜欢的运动"},
    {"day": "周六", "type": "轻度有氧 + 核心", "description": "30分钟轻松跑 + 核心训练"},
    {"day": "周日", "type": "休息日", "description": "完全休息"}
  ]},
  {"week": 3, "focus": "迷你准备周 (可选)", "sessions": [
    {"day": "周一", "type": "力量 (全身)", "description": "深蹲 3x6@60%, 卧推 3x6@60%, 硬拉 3x6@65%"},
    {"day": "周二", "type": "有氧耐力", "description": "35分钟稳态有氧"},
    {"day": "周三", "type": "休息/核心", "description": "核心训练 3组 或 完全休息"},
    {"day": "周四", "type": "力量 (全身)", "description": "引体向上 3x8, 腿举 3x10, 肩推 3x8, 划船 3x8"},
    {"day": "周五", "type": "速度/灵活", "description": "敏捷梯 3x, 短距离冲刺 3x30m"},
    {"day": "周六", "type": "娱乐性运动", "description": "自由活动"},
    {"day": "周日", "type": "休息日", "description": "完全休息"}
  ]},
  {"week": 4, "focus": "回归准备周 (可选)", "sessions": [
    {"day": "周一", "type": "力量", "description": "深蹲 3x5@65%, 卧推 3x5@65%, 硬拉 3x5@70%"},
    {"day": "周二", "type": "有氧耐力", "description": "40分钟稳态有氧"},
    {"day": "周三", "type": "力量+爆发", "description": "高翻 4x3@60%, 深蹲 3x5@68%, 核心"},
    {"day": "周四", "type": "休息/恢复", "description": "主动恢复日"},
    {"day": "周五", "type": "速度+技术", "description": "30m冲刺 4x, 专项技术"},
    {"day": "周六", "type": "全身力量", "description": "深蹲 3x5@70%, 卧推 3x5@70%, 划船 3x8"},
    {"day": "周日", "type": "休息日", "description": "迎接新赛季准备期"}
  ]}
 ]'::jsonb, TRUE);
