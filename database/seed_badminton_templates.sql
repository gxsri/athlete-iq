-- ============================================================================
-- AthleteIQ - 羽毛球周期化模板种子数据
-- 基于羽毛球专项特征设计的4个周期化训练模板
-- ============================================================================

-- 扩展 periodization_templates 约束，支持羽毛球专项阶段
DO $$
BEGIN
    ALTER TABLE periodization_templates DROP CONSTRAINT IF EXISTS periodization_templates_template_type_check;
EXCEPTION
    WHEN undefined_object THEN NULL;
END $$;
ALTER TABLE periodization_templates ADD CONSTRAINT periodization_templates_template_type_check
    CHECK (template_type IN ('线性周期', '非线性DUP', '板块周期', '比赛期', '过渡期'));

DO $$
BEGIN
    ALTER TABLE periodization_templates DROP CONSTRAINT IF EXISTS periodization_templates_cycle_phase_check;
EXCEPTION
    WHEN undefined_object THEN NULL;
END $$;
ALTER TABLE periodization_templates ADD CONSTRAINT periodization_templates_cycle_phase_check
    CHECK (cycle_phase IN ('一般准备期', '专项准备期', '比赛期', '过渡期', '休赛期', '备赛期'));

-- ============================================================================
-- 1. 休赛期 (4周) - 非线性DUP
-- 目标: 维持基础体能，保持技术手感，预防伤病
-- RPE 范围: 4-6
-- ============================================================================
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('羽毛球-休赛期 (非线性DUP)', '非线性DUP', '休赛期',
 '休赛期非线性DUP模板：保持基础力量和体能，同时维持羽毛球技术手感。每日波动训练目标（力量日/技术日/恢复日交替），为期4周，RPE控制在4-6范围内。',
 '[
   {"week": 1, "focus": "基础力量 + 后场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉","引体向上"], "duration_min": 75, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球","平高球"], "duration_min": 60, "rpe_target": 5}
      ]},
      {"day": "周二", "sessions": [
        {"type": "代谢", "exercises": ["划船机间歇","自行车冲刺"], "duration_min": 40, "rpe_target": 5},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体","鸟狗式"], "duration_min": 20, "rpe_target": 4}
      ]},
      {"day": "周三", "sessions": [
        {"type": "力量", "exercises": ["杠铃划船","肩推","腿举","俯卧撑"], "duration_min": 70, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["正手抽球","反手抽球","挡网"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周四", "sessions": [
        {"type": "速度", "exercises": ["敏捷梯","折返跑"], "duration_min": 40, "rpe_target": 6},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 60, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","挑球"], "duration_min": 60, "rpe_target": 5}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边","正手发高远球","反手发网前球"], "duration_min": 60, "rpe_target": 5},
        {"type": "核心", "exercises": ["死虫式","平板支撑"], "duration_min": 15, "rpe_target": 4}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 2, "focus": "爆发力 + 中场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","杠铃划船"], "duration_min": 60, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["正手抽球","反手抽球","挡网"], "duration_min": 60, "rpe_target": 5}
      ]},
      {"day": "周二", "sessions": [
        {"type": "爆发力", "exercises": ["高翻","跳箱","药球抛砸"], "duration_min": 60, "rpe_target": 6},
        {"type": "代谢", "exercises": ["400m间歇"], "duration_min": 30, "rpe_target": 6}
      ]},
      {"day": "周三", "sessions": [
        {"type": "力量", "exercises": ["肩推","引体向上","腿举"], "duration_min": 60, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周四", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "爆发力", "exercises": ["抓举","壶铃摆荡","反向纵跳"], "duration_min": 60, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周六", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","反应起跑","敏捷梯"], "duration_min": 45, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边"], "duration_min": 45, "rpe_target": 6}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["瑜伽","静态拉伸"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 3, "focus": "肌肥大耐力 + 前场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","杠铃划船","肩推"], "duration_min": 75, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","挑球"], "duration_min": 60, "rpe_target": 5}
      ]},
      {"day": "周二", "sessions": [
        {"type": "代谢", "exercises": ["划船机间歇","800m节奏跑"], "duration_min": 50, "rpe_target": 5},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体","鸟狗式","死虫式"], "duration_min": 25, "rpe_target": 4}
      ]},
      {"day": "周三", "sessions": [
        {"type": "力量", "exercises": ["硬拉","引体向上","腿举","俯卧撑"], "duration_min": 70, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["高远球","平高球","正手抽球","反手抽球"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周四", "sessions": [
        {"type": "速度", "exercises": ["折返跑","敏捷梯"], "duration_min": 40, "rpe_target": 6},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 60, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["杀球","吊球","挡网"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","正手发高远球","反手发网前球"], "duration_min": 60, "rpe_target": 5},
        {"type": "爆发力", "exercises": ["跳箱","壶铃摆荡"], "duration_min": 30, "rpe_target": 6}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 4, "focus": "减载恢复 + 综合技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 45, "rpe_target": 5}
      ]},
      {"day": "周二", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["高远球","吊球","搓球"], "duration_min": 45, "rpe_target": 4},
        {"type": "核心", "exercises": ["平板支撑","鸟狗式"], "duration_min": 15, "rpe_target": 3}
      ]},
      {"day": "周三", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","冷水浸泡","静态拉伸"], "duration_min": 35, "rpe_target": 2}
      ]},
      {"day": "周四", "sessions": [
        {"type": "力量", "exercises": ["引体向上","肩推","腿举"], "duration_min": 40, "rpe_target": 5}
      ]},
      {"day": "周五", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["正手发高远球","反手发网前球","前后场连贯步法"], "duration_min": 45, "rpe_target": 4},
        {"type": "恢复", "exercises": ["瑜伽"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周六", "sessions": [
        {"type": "恢复", "exercises": ["娱乐性运动"], "duration_min": 45, "rpe_target": 3}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["完全休息"], "duration_min": 0, "rpe_target": 1}
      ]}
    ]
   }
 ]'::jsonb, TRUE);

-- ============================================================================
-- 2. 备赛期 (6周) - 板块周期
-- 目标: 逐步提升专项体能和技术强度，为比赛做准备
-- RPE 范围: 5-8
-- ============================================================================
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('羽毛球-备赛期 (板块周期)', '板块周期', '备赛期',
 '备赛期板块周期模板：6周循序渐进，从力量板块（下肢→上肢）过渡到爆发力板块，再到速度板块，最后赛前强度。每周6天训练+1天恢复，RPE从5递增至8。',
 '[
   {"week": 1, "focus": "板块1: 下肢力量 + 后场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","硬拉","腿举"], "duration_min": 80, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球"], "duration_min": 60, "rpe_target": 6}
      ]},
      {"day": "周二", "sessions": [
        {"type": "代谢", "exercises": ["400m间歇","划船机间歇"], "duration_min": 50, "rpe_target": 7},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体","鸟狗式"], "duration_min": 20, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["正手抽球","反手抽球","挡网","前后场连贯步法"], "duration_min": 75, "rpe_target": 6},
        {"type": "力量", "exercises": ["深蹲","杠铃划船"], "duration_min": 45, "rpe_target": 6}
      ]},
      {"day": "周四", "sessions": [
        {"type": "速度", "exercises": ["敏捷梯","折返跑","反应起跑"], "duration_min": 45, "rpe_target": 7},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "力量", "exercises": ["硬拉","腿举","引体向上"], "duration_min": 75, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["平高球","吊球","挑球"], "duration_min": 50, "rpe_target": 5}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["左右摸边","正手发高远球","反手发网前球","搓球"], "duration_min": 70, "rpe_target": 6},
        {"type": "核心", "exercises": ["死虫式"], "duration_min": 15, "rpe_target": 5}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","冷水浸泡"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 2, "focus": "板块2: 上肢力量 + 中场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["卧推","肩推","杠铃划船","引体向上"], "duration_min": 80, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["正手抽球","反手抽球","挡网"], "duration_min": 60, "rpe_target": 6}
      ]},
      {"day": "周二", "sessions": [
        {"type": "代谢", "exercises": ["800m节奏跑","自行车冲刺"], "duration_min": 55, "rpe_target": 7},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体"], "duration_min": 20, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["高远球","平高球","前后场连贯步法"], "duration_min": 75, "rpe_target": 7},
        {"type": "力量", "exercises": ["卧推","深蹲"], "duration_min": 45, "rpe_target": 6}
      ]},
      {"day": "周四", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","折返跑"], "duration_min": 45, "rpe_target": 7},
        {"type": "恢复", "exercises": ["泡沫轴放松","瑜伽"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "力量", "exercises": ["肩推","杠铃划船","俯卧撑","腿举"], "duration_min": 70, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["杀球","吊球","推球"], "duration_min": 50, "rpe_target": 6}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["搓球","勾对角","左右摸边","正手发高远球"], "duration_min": 70, "rpe_target": 6},
        {"type": "爆发力", "exercises": ["跳箱","药球抛砸"], "duration_min": 30, "rpe_target": 7}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","冷水浸泡"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 3, "focus": "板块3: 爆发力 + 前场技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "爆发力", "exercises": ["高翻","抓举","跳箱"], "duration_min": 75, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","挑球"], "duration_min": 60, "rpe_target": 6}
      ]},
      {"day": "周二", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","60m冲刺","反应起跑"], "duration_min": 50, "rpe_target": 8},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体","鸟狗式","死虫式"], "duration_min": 25, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","正手抽球","反手抽球"], "duration_min": 80, "rpe_target": 7},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周四", "sessions": [
        {"type": "爆发力", "exercises": ["药球抛砸","壶铃摆荡","反向纵跳"], "duration_min": 65, "rpe_target": 7},
        {"type": "力量", "exercises": ["深蹲","卧推"], "duration_min": 40, "rpe_target": 6}
      ]},
      {"day": "周五", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边","挡网"], "duration_min": 70, "rpe_target": 7},
        {"type": "代谢", "exercises": ["划船机间歇"], "duration_min": 30, "rpe_target": 7}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["高远球","吊球","正手发高远球","反手发网前球"], "duration_min": 70, "rpe_target": 6},
        {"type": "核心", "exercises": ["俄罗斯转体","鸟狗式"], "duration_min": 15, "rpe_target": 5}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 35, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 4, "focus": "板块4: 速度 + 步法强化",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","60m冲刺","敏捷梯","折返跑"], "duration_min": 60, "rpe_target": 8},
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边"], "duration_min": 50, "rpe_target": 7}
      ]},
      {"day": "周二", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","正手抽球"], "duration_min": 70, "rpe_target": 7},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体"], "duration_min": 20, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "爆发力", "exercises": ["高翻","跳箱","壶铃摆荡"], "duration_min": 70, "rpe_target": 7},
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 45, "rpe_target": 7}
      ]},
      {"day": "周四", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","挑球"], "duration_min": 60, "rpe_target": 6},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "速度", "exercises": ["反应起跑","30m冲刺","敏捷梯"], "duration_min": 55, "rpe_target": 8},
        {"type": "羽毛球-技战术", "exercises": ["平高球","吊球","挡网","正手抽球"], "duration_min": 50, "rpe_target": 6}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边","正手发高远球","反手发网前球"], "duration_min": 75, "rpe_target": 7},
        {"type": "代谢", "exercises": ["400m间歇"], "duration_min": 25, "rpe_target": 8}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","冷水浸泡"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 5, "focus": "板块5: 赛前强度 + 实战模拟",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 65, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球"], "duration_min": 55, "rpe_target": 7}
      ]},
      {"day": "周二", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["实战对抗 - 全场比赛模拟"], "duration_min": 90, "rpe_target": 8},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体"], "duration_min": 15, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","折返跑","反应起跑"], "duration_min": 50, "rpe_target": 8},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角"], "duration_min": 45, "rpe_target": 6}
      ]},
      {"day": "周四", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边"], "duration_min": 60, "rpe_target": 7},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["实战对抗 - 比赛节奏演练"], "duration_min": 80, "rpe_target": 8},
        {"type": "恢复", "exercises": ["冷水浸泡","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周六", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["正手发高远球","反手发网前球","战术套跑"], "duration_min": 60, "rpe_target": 6},
        {"type": "核心", "exercises": ["鸟狗式","死虫式"], "duration_min": 15, "rpe_target": 5}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 35, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 6, "focus": "减量周: 轻量维持 + 赛前激活",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 45, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["高远球","吊球"], "duration_min": 40, "rpe_target": 5}
      ]},
      {"day": "周二", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","正手发高远球","反手发网前球"], "duration_min": 50, "rpe_target": 5},
        {"type": "核心", "exercises": ["平板支撑","鸟狗式"], "duration_min": 15, "rpe_target": 4}
      ]},
      {"day": "周三", "sessions": [
        {"type": "速度", "exercises": ["30m冲刺","敏捷梯"], "duration_min": 35, "rpe_target": 7},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周四", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["实战对抗 - 轻强度"], "duration_min": 50, "rpe_target": 6},
        {"type": "恢复", "exercises": ["冷水浸泡","静态拉伸"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推"], "duration_min": 35, "rpe_target": 6},
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边"], "duration_min": 35, "rpe_target": 5}
      ]},
      {"day": "周六", "sessions": [
        {"type": "恢复", "exercises": ["赛前激活: 轻量技术 + 动态拉伸"], "duration_min": 40, "rpe_target": 4}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["比赛日/完全休息"], "duration_min": 0, "rpe_target": 1}
      ]}
    ]
   }
 ]'::jsonb, TRUE);

-- ============================================================================
-- 3. 比赛期 (2周) - 音量递减 + 维持强度
-- 目标: 减量不减强度，保持竞技状态
-- RPE 范围: 6-9，战略性安排恢复
-- ============================================================================
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('羽毛球-比赛期 (减量+维持)', '比赛期', '比赛期',
 '比赛期间模板：采用逐渐减量策略，降低训练容量但保持强度以维持竞技状态。每日包含赛前激活流程，比赛日有完整的赛前/赛中/赛后方案。为期2周，RPE 6-9。',
 '[
   {"week": 1, "focus": "赛前减量 + 保持强度",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","轻量技术热身"], "duration_min": 20, "rpe_target": 4},
        {"type": "力量", "exercises": ["深蹲","卧推","硬拉"], "duration_min": 50, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球"], "duration_min": 45, "rpe_target": 7}
      ]},
      {"day": "周二", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","敏捷梯"], "duration_min": 20, "rpe_target": 4},
        {"type": "羽毛球-技战术", "exercises": ["正手抽球","反手抽球","挡网","前后场连贯步法"], "duration_min": 60, "rpe_target": 7},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体"], "duration_min": 15, "rpe_target": 5}
      ]},
      {"day": "周三", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","反应起跑"], "duration_min": 20, "rpe_target": 4},
        {"type": "速度", "exercises": ["30m冲刺","折返跑"], "duration_min": 35, "rpe_target": 8},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","挑球"], "duration_min": 50, "rpe_target": 7}
      ]},
      {"day": "周四", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","轻量技术"], "duration_min": 15, "rpe_target": 4},
        {"type": "羽毛球-技战术", "exercises": ["实战对抗 - 比赛节奏"], "duration_min": 70, "rpe_target": 8},
        {"type": "恢复", "exercises": ["泡沫轴放松","冷水浸泡","静态拉伸"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","轻量技术"], "duration_min": 20, "rpe_target": 4},
        {"type": "力量", "exercises": ["深蹲","肩推","引体向上"], "duration_min": 45, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["正手发高远球","反手发网前球","左右摸边"], "duration_min": 40, "rpe_target": 6}
      ]},
      {"day": "周六", "sessions": [
        {"type": "赛前激活", "exercises": ["完整赛前准备流程"], "duration_min": 30, "rpe_target": 5},
        {"type": "比赛", "exercises": ["正式比赛/高强度实战"], "duration_min": 90, "rpe_target": 9},
        {"type": "恢复", "exercises": ["赛后: 冷水浸泡","泡沫轴放松","静态拉伸"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 35, "rpe_target": 2}
      ]}
    ]
   },
   {"week": 2, "focus": "比赛周: 最低容量 + 最高质量",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","轻量技术"], "duration_min": 15, "rpe_target": 4},
        {"type": "力量", "exercises": ["深蹲","卧推"], "duration_min": 35, "rpe_target": 7},
        {"type": "羽毛球-技战术", "exercises": ["高远球","杀球","吊球"], "duration_min": 35, "rpe_target": 7}
      ]},
      {"day": "周二", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","敏捷梯"], "duration_min": 15, "rpe_target": 4},
        {"type": "羽毛球-技战术", "exercises": ["搓球","推球","勾对角","前后场连贯步法"], "duration_min": 50, "rpe_target": 7}
      ]},
      {"day": "周三", "sessions": [
        {"type": "赛前激活", "exercises": ["动态拉伸","轻量技术"], "duration_min": 15, "rpe_target": 4},
        {"type": "速度", "exercises": ["30m冲刺"], "duration_min": 25, "rpe_target": 8},
        {"type": "羽毛球-技战术", "exercises": ["正手发高远球","反手发网前球","战术演练"], "duration_min": 40, "rpe_target": 6}
      ]},
      {"day": "周四", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周五", "sessions": [
        {"type": "赛前激活", "exercises": ["赛前技术确认 + 动态热身"], "duration_min": 30, "rpe_target": 5},
        {"type": "羽毛球-技战术", "exercises": ["轻量实战对抗"], "duration_min": 40, "rpe_target": 6}
      ]},
      {"day": "周六", "sessions": [
        {"type": "赛前激活", "exercises": ["完整赛前准备流程"], "duration_min": 30, "rpe_target": 5},
        {"type": "比赛", "exercises": ["关键比赛日"], "duration_min": 90, "rpe_target": 9},
        {"type": "恢复", "exercises": ["赛后: 冷水浸泡","泡沫轴放松"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 30, "rpe_target": 2}
      ]}
    ]
   }
 ]'::jsonb, TRUE);

-- ============================================================================
-- 4. 过渡期 (2周) - 低强度交叉训练 + 主动恢复
-- 目标: 身心全面恢复，为下一个训练周期做准备
-- RPE 范围: 2-4
-- ============================================================================
INSERT INTO periodization_templates (name, template_type, cycle_phase, description, weekly_structure, is_system) VALUES
('羽毛球-过渡期 (主动恢复)', '过渡期', '过渡期',
 '过渡期恢复模板：赛季后或高强度训练周期后的主动恢复阶段。以低强度交叉训练和娱乐性活动为主，允许身体和心理全面恢复。注意监测伤病和疲劳。为期2周，RPE控制在2-4。',
 '[
   {"week": 1, "focus": "身心恢复周",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周二", "sessions": [
        {"type": "交叉训练", "exercises": ["轻松游泳"], "duration_min": 35, "rpe_target": 3},
        {"type": "恢复", "exercises": ["瑜伽"], "duration_min": 25, "rpe_target": 2}
      ]},
      {"day": "周三", "sessions": [
        {"type": "恢复", "exercises": ["完全休息"], "duration_min": 0, "rpe_target": 1}
      ]},
      {"day": "周四", "sessions": [
        {"type": "交叉训练", "exercises": ["轻松骑行"], "duration_min": 40, "rpe_target": 3},
        {"type": "核心", "exercises": ["平板支撑","鸟狗式"], "duration_min": 15, "rpe_target": 3}
      ]},
      {"day": "周五", "sessions": [
        {"type": "娱乐运动", "exercises": ["篮球/足球/乒乓球"], "duration_min": 50, "rpe_target": 4},
        {"type": "恢复", "exercises": ["静态拉伸"], "duration_min": 15, "rpe_target": 2}
      ]},
      {"day": "周六", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸","瑜伽"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["完全休息"], "duration_min": 0, "rpe_target": 1}
      ]}
    ]
   },
   {"week": 2, "focus": "渐进恢复 + 轻技术",
    "days": [
      {"day": "周一", "sessions": [
        {"type": "力量", "exercises": ["深蹲","卧推","引体向上"], "duration_min": 40, "rpe_target": 4},
        {"type": "恢复", "exercises": ["泡沫轴放松","静态拉伸"], "duration_min": 15, "rpe_target": 2}
      ]},
      {"day": "周二", "sessions": [
        {"type": "交叉训练", "exercises": ["轻松慢跑"], "duration_min": 30, "rpe_target": 3},
        {"type": "羽毛球-技战术", "exercises": ["高远球","搓球","正手发高远球"], "duration_min": 40, "rpe_target": 3}
      ]},
      {"day": "周三", "sessions": [
        {"type": "恢复", "exercises": ["泡沫轴放松","瑜伽"], "duration_min": 30, "rpe_target": 2}
      ]},
      {"day": "周四", "sessions": [
        {"type": "力量", "exercises": ["肩推","杠铃划船","腿举"], "duration_min": 40, "rpe_target": 4},
        {"type": "核心", "exercises": ["平板支撑","俄罗斯转体","鸟狗式"], "duration_min": 20, "rpe_target": 3}
      ]},
      {"day": "周五", "sessions": [
        {"type": "羽毛球-技战术", "exercises": ["前后场连贯步法","左右摸边","反手发网前球"], "duration_min": 45, "rpe_target": 3},
        {"type": "恢复", "exercises": ["静态拉伸","泡沫轴放松"], "duration_min": 20, "rpe_target": 2}
      ]},
      {"day": "周六", "sessions": [
        {"type": "娱乐运动", "exercises": ["自由活动 - 选择喜欢的运动"], "duration_min": 50, "rpe_target": 4},
        {"type": "恢复", "exercises": ["静态拉伸"], "duration_min": 15, "rpe_target": 2}
      ]},
      {"day": "周日", "sessions": [
        {"type": "恢复", "exercises": ["完全休息 - 迎接新训练周期"], "duration_min": 0, "rpe_target": 1}
      ]}
    ]
   }
 ]'::jsonb, TRUE);
