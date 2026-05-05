"""
AthleteIQ - 练习库 API (增强版: 康复分类 / 伤病关联)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from app.database import get_db, logger
from app.models.athlete import ExerciseLibrary, ExerciseInjuryLink
from app.schemas.schemas import (
    ExerciseLibraryCreate, ExerciseLibraryUpdate,
    ExerciseLibraryResponse, ExerciseLibraryListResponse,
)
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/exercises", tags=["练习库"])

# Seed exercises from training template content if library is empty
SEED_EXERCISES = [
    {"name": "热身(动态拉伸)", "category": "柔韧", "category_l1": "柔韧", "description": "全身动态拉伸激活", "preset_params": {"duration_min": 15, "rpe": 3, "weight_kg": 0, "reps": 1, "sets": 1, "rest_seconds": 0}},
    {"name": "步法训练(6点)", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "全场6点步法训练", "preset_params": {"duration_min": 25, "rpe": 6, "weight_kg": 0, "reps": 5, "sets": 1, "rest_seconds": 30}},
    {"name": "高远球练习", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "正手高远球技术练习", "preset_params": {"weight_kg": 0, "reps": 30, "sets": 1, "rpe": 5, "rest_seconds": 0}},
    {"name": "杀球专项", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "正手杀球技术练习", "preset_params": {"weight_kg": 0, "reps": 40, "sets": 1, "rpe": 8, "rest_seconds": 30}},
    {"name": "吊球技术", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "正手/反手吊球", "preset_params": {"weight_kg": 0, "reps": 25, "sets": 1, "rpe": 5, "rest_seconds": 0}},
    {"name": "网前搓球", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "网前搓球技术练习", "preset_params": {"weight_kg": 0, "reps": 25, "sets": 1, "rpe": 4, "rest_seconds": 0}},
    {"name": "深蹲", "category": "力量", "category_l1": "力量", "description": "杠铃后蹲", "preset_params": {"weight_kg": 80, "reps": 8, "sets": 4, "rpe": 7, "rest_seconds": 120}},
    {"name": "卧推", "category": "力量", "category_l1": "力量", "description": "杠铃平躺卧推", "preset_params": {"weight_kg": 60, "reps": 8, "sets": 4, "rpe": 7, "rest_seconds": 90}},
    {"name": "硬拉", "category": "力量", "category_l1": "力量", "description": "传统硬拉", "preset_params": {"weight_kg": 100, "reps": 5, "sets": 3, "rpe": 8, "rest_seconds": 150}},
    {"name": "跳箱", "category": "速度", "category_l1": "速度", "description": "爆发力跳箱训练", "preset_params": {"weight_kg": 0, "reps": 6, "sets": 4, "rpe": 7, "rest_seconds": 90}},
    {"name": "折返跑", "category": "速度", "category_l1": "速度", "description": "20m折返跑", "preset_params": {"weight_kg": 0, "reps": 5, "sets": 3, "rpe": 8, "rest_seconds": 90}},
    {"name": "400m间歇跑", "category": "耐力", "category_l1": "耐力", "description": "400米间歇训练", "preset_params": {"weight_kg": 0, "reps": 8, "sets": 8, "rpe": 8, "rest_seconds": 90}},
    {"name": "核心训练", "category": "力量", "category_l1": "力量", "description": "平板支撑+卷腹+俄罗斯转体", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 6, "rest_seconds": 30}},
    {"name": "静态拉伸", "category": "柔韧", "category_l1": "柔韧", "description": "全身静态拉伸放松", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "rest_seconds": 0}},
    {"name": "半场对抗", "category": "混合", "category_l1": "混合", "description": "半场单打对抗训练", "preset_params": {"duration_min": 25, "rpe": 7, "weight_kg": 0, "reps": 1, "sets": 1, "rest_seconds": 0}},
    {"name": "全场对抗", "category": "混合", "category_l1": "混合", "description": "全场单打/双打模拟比赛", "preset_params": {"duration_min": 35, "rpe": 8, "weight_kg": 0, "reps": 1, "sets": 1, "rest_seconds": 0}},
    {"name": "泡沫轴放松", "category": "柔韧", "category_l1": "柔韧", "description": "全身泡沫轴自筋膜松解", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "rest_seconds": 0}},
    {"name": "正手抽球", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "正手抽球技术练习", "preset_params": {"weight_kg": 0, "reps": 25, "sets": 1, "rpe": 6, "rest_seconds": 0}},
    {"name": "反手抽球", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "反手抽球技术练习", "preset_params": {"weight_kg": 0, "reps": 25, "sets": 1, "rpe": 6, "rest_seconds": 0}},
    {"name": "前后场连贯步法", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "前后场连贯步法训练", "preset_params": {"duration_min": 15, "rpe": 7, "weight_kg": 0, "reps": 1, "sets": 1, "rest_seconds": 0}},
]

# Rehab exercise presets with full NASM / literature data
REHAB_EXERCISE_PRESETS = [
    # ============ 肘部 (6个) ============
    {"name": "前臂伸肌泡沫轴滚动", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "INH", "target_muscles": ["前臂伸肌群", "肱桡肌"],
     "instructions": "1. 俯卧，将泡沫轴置于前臂伸肌下方\n2. 缓慢前后滚动30秒\n3. 找到压痛点后保持15-20秒\n4. 每侧2-3分钟", "literature_ref": "NASM纠正指南 SMR章节",
     "description": "放松前臂伸肌群，改善肱骨外上髁炎相关软组织紧张", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "duration_min": 5, "rest_seconds": 0}},
    {"name": "前臂伸肌静态拉伸", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "LEN", "target_muscles": ["腕伸肌", "指伸肌"],
     "instructions": "1. 手臂伸直，手腕下垂\n2. 另一只手轻轻加压\n3. 保持30秒×3组\n4. 无痛范围内进行", "literature_ref": "网球肘保守治疗标准方案 (Cullinane 2014)",
     "description": "拉伸伸肌腱和腕伸肌，降低肌腱附着点张力", "preset_params": {"weight_kg": 0, "reps": 3, "sets": 1, "rpe": 2, "duration_min": 5, "rest_seconds": 10}},
    {"name": "前臂屈肌静态拉伸", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "LEN", "target_muscles": ["腕屈肌", "指屈肌"],
     "instructions": "1. 手臂伸直，手腕背伸\n2. 另一只手轻轻加压\n3. 保持30秒×3组\n4. 平衡前后肌群张力", "literature_ref": "NASM纠正指南 拉伸章节",
     "description": "拉伸屈肌及腕屈肌，平衡前后肌群柔韧性", "preset_params": {"weight_kg": 0, "reps": 3, "sets": 1, "rpe": 2, "duration_min": 5, "rest_seconds": 10}},
    {"name": "弹力带腕伸肌离心训练", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "ACT", "target_muscles": ["腕伸肌", "桡侧腕短伸肌"],
     "instructions": "1. 坐位，前臂支撑于大腿\n2. 弹力带绕于手背，腕关节起始于屈曲位\n3. 缓慢（3秒）抗阻背伸至中立\n4. 15次×3组，RPE 4", "literature_ref": "Tyler Twist效应——离心训练促进肌腱重塑 (Stasinopoulos 2005)",
     "description": "离心强化伸肌肌腱，促进网球肘肌腱重塑", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 4, "rest_seconds": 60}},
    {"name": "握力球挤压（渐进）", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "ACT", "target_muscles": ["指屈肌", "前臂肌群"],
     "instructions": "1. 手握软式握力球\n2. 缓慢挤压至最大握力的70%\n3. 保持3秒后缓慢释放\n4. 20次×3组", "literature_ref": "肌腱病康复标准——渐进负荷促进血流量 (Khan 2002)",
     "description": "改善握力、促进局部血流量，加速肌腱代谢", "preset_params": {"weight_kg": 0, "reps": 20, "sets": 3, "rpe": 3, "rest_seconds": 30}},
    {"name": "前臂旋后/旋前等长收缩", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "肘部", "nasm_phase": "INT", "target_muscles": ["旋后肌", "旋前圆肌", "肱二头肌"],
     "instructions": "1. 肘关节90°屈曲位\n2. 手持轻哑铃或弹力带\n3. 旋后位等长保持10秒\n4. 旋前位等长保持10秒\n5. 每位置重复5次", "literature_ref": "功能性整合——前臂旋转功能恢复 (NASM CET)",
     "description": "恢复前臂旋转功能，整合至日常和运动模式", "preset_params": {"weight_kg": 2, "reps": 5, "sets": 3, "rpe": 3, "rest_seconds": 45}},

    # ============ 腕部 (4个) ============
    {"name": "腕关节主动活动度训练", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腕部", "nasm_phase": "LEN", "target_muscles": ["腕关节囊", "腕屈伸肌"],
     "instructions": "1. 手臂支撑，手腕悬空\n2. 主动缓慢完成屈伸最大范围\n3. 再做尺偏/桡偏\n4. 每个方向10次慢速", "literature_ref": "关节活动度维持——运动康复基础 (Magee)",
     "description": "改善屈伸/尺偏桡偏活动范围，维持关节囊弹性", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 2, "rpe": 2, "duration_min": 5, "rest_seconds": 15}},
    {"name": "弹力带腕屈曲离心", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腕部", "nasm_phase": "ACT", "target_muscles": ["腕屈肌", "指浅屈肌"],
     "instructions": "1. 前臂旋后（掌心朝上）\n2. 弹力带绕于手掌\n3. 缓慢（3秒）离心背伸\n4. 快速（1秒）向心屈曲\n5. 15次×3组", "literature_ref": "肌腱离心训练原理——渐进负荷刺激胶原合成",
     "description": "强化屈肌腱，利用离心训练促进胶原纤维排列", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 4, "rest_seconds": 60}},
    {"name": "弹力带腕背伸离心", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腕部", "nasm_phase": "ACT", "target_muscles": ["腕伸肌", "指伸肌"],
     "instructions": "1. 前臂旋前（掌心朝下）\n2. 弹力带绕于手背\n3. 缓慢（3秒）离心屈腕\n4. 快速（1秒）向心背伸\n5. 15次×3组", "literature_ref": "肌腱离心训练原理——双侧平衡强化",
     "description": "强化伸肌腱，均衡屈伸肌力比", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 4, "rest_seconds": 60}},
    {"name": "腕关节本体感觉训练（闭眼定位）", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腕部", "nasm_phase": "INT", "target_muscles": ["腕关节机械感受器", "前臂肌梭"],
     "instructions": "1. 闭眼，对侧手将患侧腕置于随机角度\n2. 尝试识别并复现该角度\n3. 10次/方向×2组\n4. 进阶：加入轻弹力带阻力", "literature_ref": "本体感觉损伤预防——韧带/关节囊机械感受器训练 (Riemann 2002)",
     "description": "提高关节位置觉，预防反复性腕关节微损伤", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 2, "rpe": 3, "rest_seconds": 20}},

    # ============ 膝关节 (6个) ============
    {"name": "股四头肌泡沫轴滚动", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "INH", "target_muscles": ["股四头肌", "股直肌", "髂胫束"],
     "instructions": "1. 俯卧，泡沫轴置于大腿前方\n2. 从髋至膝缓慢滚动\n3. 压痛点停留15-20秒\n4. 2-3分钟/侧", "literature_ref": "NASM SMR 自我肌筋膜松解",
     "description": "放松股四头肌，降低髌骨关节压力", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 3, "duration_min": 6, "rest_seconds": 0}},
    {"name": "腘绳肌泡沫轴滚动", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "INH", "target_muscles": ["腘绳肌", "半腱肌", "半膜肌"],
     "instructions": "1. 坐位，泡沫轴置于大腿后方\n2. 从坐骨结节至腘窝缓慢滚动\n3. 避免直接压迫腘窝\n4. 2-3分钟/侧", "literature_ref": "NASM SMR",
     "description": "放松腘绳肌，改善膝关节后侧软组织延展性", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 3, "duration_min": 6, "rest_seconds": 0}},
    {"name": "胫骨前肌/腓肠肌拉伸", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "LEN", "target_muscles": ["胫骨前肌", "腓肠肌", "比目鱼肌"],
     "instructions": "1. 站姿弓步，后腿伸直拉伸腓肠肌\n2. 后腿微屈拉伸比目鱼肌\n3. 每位置30秒×2组\n4. 双脚各做", "literature_ref": "运动链理论——踝背屈受限增加膝前向剪切力",
     "description": "改善踝背屈活动度，间接降低膝关节代偿性负荷", "preset_params": {"weight_kg": 0, "reps": 2, "sets": 1, "rpe": 3, "duration_min": 5, "rest_seconds": 10}},
    {"name": "北欧腘绳肌离心训练", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "ACT", "target_muscles": ["腘绳肌", "半腱肌", "股二头肌"],
     "instructions": "1. 跪姿，脚踝固定\n2. 缓慢前倾，用腘绳肌离心控制下落\n3. 尽可能慢地下落到极限\n4. 手撑回起始位\n5. 6-8次×3组，RPE 6", "literature_ref": "北欧腘绳肌训练被证实可降低ACL损伤风险达50% (van der Horst 2015)",
     "description": "离心强化腘绳肌，预防ACL损伤和腘绳肌拉伤", "preset_params": {"weight_kg": 0, "reps": 6, "sets": 3, "rpe": 6, "rest_seconds": 120}},
    {"name": "靠墙静蹲", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "ACT", "target_muscles": ["股四头肌", "股内侧肌"],
     "instructions": "1. 背靠墙，双脚与肩同宽\n2. 缓慢下滑至膝角~60°\n3. 保持30-60秒\n4. 确保膝盖不超过脚尖\n5. 4-5组", "literature_ref": "髌腱炎康复标准——等长训练缓解疼痛 (Rio 2015)",
     "description": "股四头肌等长训练，增强髌骨稳定性，缓解髌腱炎", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 4, "rpe": 5, "duration_min": 8, "rest_seconds": 60}},
    {"name": "单腿落地控制（升级）", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "膝关节", "nasm_phase": "INT", "target_muscles": ["臀中肌", "股四头肌", "核心稳定肌"],
     "instructions": "1. 站立于20cm箱上\n2. 单腿跳下，软着陆\n3. 控制膝不外翻（对准第2趾）\n4. 保持落地姿势2秒\n5. 8次×3组/侧", "literature_ref": "ACL损伤预防计划——落地机制纠正 (Hewett 2005)",
     "description": "动态膝外翻控制，改善落地生物力学，预防ACL损伤", "preset_params": {"weight_kg": 0, "reps": 8, "sets": 3, "rpe": 6, "rest_seconds": 90}},

    # ============ 腰部 (8个) ============
    {"name": "腰椎泡沫轴滚动", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "INH", "target_muscles": ["竖脊肌", "腰方肌", "胸腰筋膜"],
     "instructions": "1. 仰卧，泡沫轴置于腰部下方\n2. 缓慢左右滚动，避免直接压迫脊柱骨\n3. 找到紧张点后小范围活动\n4. 2-3分钟", "literature_ref": "NASM SMR——胸腰筋膜松解",
     "description": "放松竖脊肌、腰方肌及胸腰筋膜", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 3, "duration_min": 5, "rest_seconds": 0}},
    {"name": "仰卧抱膝拉伸", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "LEN", "target_muscles": ["腰椎", "竖脊肌"],
     "instructions": "1. 仰卧，双膝抱于胸前\n2. 轻轻将膝盖拉向胸部\n3. 保持下背部贴地\n4. 维持30秒×3组", "literature_ref": "McKenzie疗法——被动牵拉减轻椎间盘压力",
     "description": "被动牵拉腰椎，降低椎间盘内压力，缓解腰背痛", "preset_params": {"weight_kg": 0, "reps": 3, "sets": 1, "rpe": 2, "duration_min": 5, "rest_seconds": 10}},
    {"name": "猫驼式", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "LEN", "target_muscles": ["胸椎", "腰椎", "脊柱节段"],
     "instructions": "1. 四足跪姿\n2. 吸气——骨盆前倾、胸椎伸展（驼式）\n3. 呼气——骨盆后倾、脊柱屈曲（猫式）\n4. 缓慢交替10次×2组", "literature_ref": "脊柱节段活动——改善胸腰椎联动 (McGill)",
     "description": "改善胸腰椎灵活性，促进脊柱节段活动", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 2, "rpe": 2, "duration_min": 5, "rest_seconds": 15}},
    {"name": "鸟狗式", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "ACT", "target_muscles": ["多裂肌", "竖脊肌", "腹横肌"],
     "instructions": "1. 四足跪姿，脊柱中立\n2. 缓慢抬对侧手臂和腿\n3. 保持骨盆不旋转\n4. 维持5秒后换侧\n5. 每侧10次×3组", "literature_ref": "核心稳定——多裂肌/腹横肌协同激活 (McGill Big 3)",
     "description": "激活多裂肌和竖脊肌，建立腰椎节段稳定性", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 3, "rpe": 4, "rest_seconds": 45}},
    {"name": "侧桥", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "ACT", "target_muscles": ["腰方肌", "腹斜肌", "臀中肌"],
     "instructions": "1. 侧卧，肘支撑\n2. 抬起髋部，身体成一直线\n3. 保持腹肌收紧\n4. 维持20-30秒×3组/侧", "literature_ref": "抗侧屈稳定——腰方肌/腹斜肌协同 (McGill Big 3)",
     "description": "强化腰方肌和腹斜肌，增强抗侧屈稳定性", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 3, "rpe": 5, "duration_min": 6, "rest_seconds": 45}},
    {"name": "死虫式", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "ACT", "target_muscles": ["腹横肌", "多裂肌", "盆底肌"],
     "instructions": "1. 仰卧，四肢朝天\n2. 腰部贴地（无空隙）\n3. 缓慢下放对侧手臂和腿\n4. 保持腰椎不移动\n5. 每侧10次×3组", "literature_ref": "核心基础——腰椎中立位稳定训练 (McGill Big 3)",
     "description": "腰椎中立稳定，建立深层核心肌肉模式", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 3, "rpe": 4, "rest_seconds": 30}},
    {"name": "麦肯锡俯卧撑", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "ACT", "target_muscles": ["腰椎", "椎间盘"],
     "instructions": "1. 俯卧，双手置于肩旁\n2. 缓慢推起上半身，骨盆保持贴地\n3. 在末端保持2-3秒\n4. 缓慢放下\n5. 10次×2组", "literature_ref": "McKenzie标准——后伸运动促进椎间盘复位",
     "description": "腰椎后伸运动，缓解椎间盘压力，促进髓核前移", "preset_params": {"weight_kg": 0, "reps": 10, "sets": 2, "rpe": 3, "rest_seconds": 20}},
    {"name": "臀桥", "category": "康复/纠正性训练", "category_l1": "康复/纠正性训练", "category_l2": "腰部", "nasm_phase": "ACT", "target_muscles": ["臀大肌", "腘绳肌", "竖脊肌"],
     "instructions": "1. 仰卧，膝盖弯曲，双脚平放\n2. 收紧臀部抬起髋部\n3. 身体肩-髋-膝成直线\n4. 顶峰保持2秒后缓慢下放\n5. 15次×3组", "literature_ref": "腰椎-骨盆节律——臀肌激活减少腰椎代偿 (NASM)",
     "description": "激活臀肌，减少腰椎代偿性过度伸展", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 5, "rest_seconds": 45}},
]

# Injury body part mapping for linking exercises
REHAB_INJURY_LINKS = [
    # 肘部 exercises → elbow
    ("前臂伸肌泡沫轴滚动", "elbow", "rehab", 1),
    ("前臂伸肌静态拉伸", "elbow", "rehab", 1),
    ("前臂屈肌静态拉伸", "elbow", "rehab", 2),
    ("弹力带腕伸肌离心训练", "elbow", "rehab", 1),
    ("握力球挤压（渐进）", "elbow", "rehab", 2),
    ("前臂旋后/旋前等长收缩", "elbow", "rehab", 2),
    # 腕部 exercises → wrist
    ("腕关节主动活动度训练", "wrist", "rehab", 1),
    ("弹力带腕屈曲离心", "wrist", "rehab", 1),
    ("弹力带腕背伸离心", "wrist", "rehab", 1),
    ("腕关节本体感觉训练（闭眼定位）", "wrist", "rehab", 2),
    # 膝关节 exercises → knee
    ("股四头肌泡沫轴滚动", "knee", "rehab", 1),
    ("腘绳肌泡沫轴滚动", "knee", "rehab", 1),
    ("胫骨前肌/腓肠肌拉伸", "knee", "rehab", 2),
    ("北欧腘绳肌离心训练", "knee", "preventive", 1),
    ("靠墙静蹲", "knee", "rehab", 1),
    ("单腿落地控制（升级）", "knee", "preventive", 2),
    # 腰部 exercises → back
    ("腰椎泡沫轴滚动", "back", "rehab", 1),
    ("仰卧抱膝拉伸", "back", "rehab", 1),
    ("猫驼式", "back", "rehab", 2),
    ("鸟狗式", "back", "preventive", 1),
    ("侧桥", "back", "preventive", 2),
    ("死虫式", "back", "preventive", 2),
    ("麦肯锡俯卧撑", "back", "rehab", 1),
    ("臀桥", "back", "preventive", 1),
]


async def seed_exercise_library(db: AsyncSession):
    existing = await db.execute(select(func.count(ExerciseLibrary.id)))
    count = existing.scalar()
    if count == 0:
        for ex in SEED_EXERCISES:
            db.add(ExerciseLibrary(**ex))
        await db.commit()
        logger.info(f"Seeded {len(SEED_EXERCISES)} exercises into library")


@router.get("/", response_model=ExerciseLibraryListResponse)
async def list_exercises(
    category: Optional[str] = Query(None, description="按旧分类筛选"),
    category_l1: Optional[str] = Query(None, description="按一级分类筛选"),
    category_l2: Optional[str] = Query(None, description="按二级分类筛选（肘部/腕部/膝关节/腰部）"),
    nasm_phase: Optional[str] = Query(None, description="按NASM阶段筛选"),
    search: Optional[str] = Query(None, description="按名称搜索"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    await seed_exercise_library(db)
    query = select(ExerciseLibrary)
    count_query = select(func.count(ExerciseLibrary.id))

    if category:
        query = query.where(ExerciseLibrary.category == category)
        count_query = count_query.where(ExerciseLibrary.category == category)
    if category_l1:
        query = query.where(ExerciseLibrary.category_l1 == category_l1)
        count_query = count_query.where(ExerciseLibrary.category_l1 == category_l1)
    if category_l2:
        query = query.where(ExerciseLibrary.category_l2 == category_l2)
        count_query = count_query.where(ExerciseLibrary.category_l2 == category_l2)
    if nasm_phase:
        query = query.where(ExerciseLibrary.nasm_phase == nasm_phase)
        count_query = count_query.where(ExerciseLibrary.nasm_phase == nasm_phase)
    if search:
        query = query.where(ExerciseLibrary.name.ilike(f"%{search}%"))
        count_query = count_query.where(ExerciseLibrary.name.ilike(f"%{search}%"))

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    query = query.offset(offset).limit(limit).order_by(
        ExerciseLibrary.category_l1, ExerciseLibrary.category_l2, ExerciseLibrary.name
    )
    result = await db.execute(query)
    exercises = result.scalars().all()

    return ExerciseLibraryListResponse(
        exercises=[ExerciseLibraryResponse.model_validate(e) for e in exercises],
        total=total,
    )


@router.post("/", response_model=ExerciseLibraryResponse, status_code=201)
async def create_exercise(data: ExerciseLibraryCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(
            select(ExerciseLibrary).where(
                ExerciseLibrary.name == data.name,
                ExerciseLibrary.coach_id == data.coach_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该练习名称已存在")

        exercise = ExerciseLibrary(**data.model_dump())
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        logger.info(f"Created exercise {exercise.id}: {exercise.name}")
        return exercise
    except IntegrityError as e:
        logger.warning(f"IntegrityError creating exercise: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create exercise")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.put("/{exercise_id}", response_model=ExerciseLibraryResponse)
async def update_exercise(
    exercise_id: UUID,
    data: ExerciseLibraryUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        exercise = await db.get(ExerciseLibrary, exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="练习不存在")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(exercise, key, value)

        await db.commit()
        await db.refresh(exercise)
        logger.info(f"Updated exercise {exercise_id}")
        return exercise
    except IntegrityError as e:
        logger.warning(f"IntegrityError updating exercise {exercise_id}: {e}")
        raise HTTPException(status_code=409, detail=f"数据冲突: {str(e.orig)[:200]}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update exercise {exercise_id}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)[:200]}")


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """返回一级和二级分类统计"""
    # L1 categories
    l1_result = await db.execute(
        select(ExerciseLibrary.category_l1, func.count(ExerciseLibrary.id))
        .where(ExerciseLibrary.category_l1.isnot(None))
        .group_by(ExerciseLibrary.category_l1)
        .order_by(ExerciseLibrary.category_l1)
    )
    l1_cats = [{"category_l1": row[0], "count": row[1]} for row in l1_result.all()]

    # L2 categories (only for rehab exercises)
    l2_result = await db.execute(
        select(ExerciseLibrary.category_l2, func.count(ExerciseLibrary.id))
        .where(ExerciseLibrary.category_l2.isnot(None))
        .group_by(ExerciseLibrary.category_l2)
        .order_by(ExerciseLibrary.category_l2)
    )
    l2_cats = [{"category_l2": row[0], "count": row[1]} for row in l2_result.all()]

    # Legacy categories
    legacy_result = await db.execute(
        select(ExerciseLibrary.category, func.count(ExerciseLibrary.id))
        .where(ExerciseLibrary.category.isnot(None))
        .group_by(ExerciseLibrary.category)
        .order_by(ExerciseLibrary.category)
    )
    legacy_cats = [{"category": row[0], "count": row[1]} for row in legacy_result.all()]

    return {"categories_l1": l1_cats, "categories_l2": l2_cats, "categories_legacy": legacy_cats}


@router.delete("/{exercise_id}")
async def delete_exercise(exercise_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        exercise = await db.get(ExerciseLibrary, exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="练习不存在")
        await db.delete(exercise)
        await db.commit()
        logger.info(f"Deleted exercise {exercise_id}")
        return {"status": "deleted", "exercise_id": str(exercise_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete exercise {exercise_id}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)[:200]}")


@router.post("/seed-presets")
async def seed_preset_exercises(db: AsyncSession = Depends(get_db)):
    """Seed the exercise library with 20 badminton-specific exercises + clear old seeded ones."""
    # Clear only exercises without category_l1 (legacy auto-seeded)
    await db.execute(
        select(ExerciseLibrary).where(ExerciseLibrary.category_l1.is_(None))
    )
    existing_all = await db.execute(select(func.count(ExerciseLibrary.id)))
    total = existing_all.scalar()

    # Only seed if fewer than 5 (all were cleared)
    if total >= 5:
        return {"status": "skipped", "message": f"练习库已有 {total} 个动作"}

    presets = [{
        "name": "深蹲", "category": "力量", "category_l1": "力量", "description": "杠铃后蹲", "preset_params": {"weight_kg": 80, "reps": 8, "sets": 4, "rpe": 7, "rest_seconds": 120},
    }, {
        "name": "卧推", "category": "力量", "category_l1": "力量", "description": "杠铃卧推", "preset_params": {"weight_kg": 60, "reps": 8, "sets": 4, "rpe": 7.5, "rest_seconds": 90},
    }, {
        "name": "硬拉", "category": "力量", "category_l1": "力量", "description": "传统硬拉", "preset_params": {"weight_kg": 100, "reps": 5, "sets": 3, "rpe": 8, "rest_seconds": 150},
    }, {
        "name": "400m间歇跑", "category": "耐力", "category_l1": "耐力", "description": "跑道间歇", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 8, "rpe": 8, "rest_seconds": 90},
    }, {
        "name": "多球杀球练习", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "多球杀球", "preset_params": {"weight_kg": 0, "reps": 40, "sets": 3, "rpe": 8, "rest_seconds": 60},
    }, {
        "name": "米字步法跑位", "category": "羽毛球-技战术", "category_l1": "技战术", "description": "全场步法", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 5, "rpe": 6, "rest_seconds": 30},
    }, {
        "name": "半场对抗", "category": "混合", "category_l1": "混合", "description": "半场单打", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 7, "duration_min": 25, "rest_seconds": 0},
    }, {
        "name": "全场对抗", "category": "混合", "category_l1": "混合", "description": "全场模拟赛", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 8, "duration_min": 35, "rest_seconds": 0},
    }, {
        "name": "肩部弹力带外旋", "category": "恢复", "category_l1": "恢复", "description": "肩袖康复", "preset_params": {"weight_kg": 0, "reps": 15, "sets": 3, "rpe": 4, "rest_seconds": 30},
    }, {
        "name": "泡沫轴放松", "category": "恢复", "category_l1": "恢复", "description": "筋膜松解", "preset_params": {"weight_kg": 0, "reps": 1, "sets": 1, "rpe": 2, "duration_min": 15, "rest_seconds": 0},
    }]

    for ex in presets:
        db.add(ExerciseLibrary(**ex))
    await db.commit()
    logger.info(f"Seeded {len(presets)} preset exercises")
    return {"status": "seeded", "count": len(presets)}


@router.post("/seed-rehab")
async def seed_rehab_exercises(db: AsyncSession = Depends(get_db)):
    """Seed 24 rehab exercises (elbow/wrist/knee/back) with full NASM data + injury links."""
    # Check if already seeded
    existing_rehab = await db.execute(
        select(func.count(ExerciseLibrary.id))
        .where(ExerciseLibrary.category_l2.isnot(None))
    )
    rehab_count = existing_rehab.scalar()
    if rehab_count >= 24:
        return {"status": "skipped", "message": f"康复动作已有 {rehab_count} 个"}

    # Clear existing rehab exercises to avoid duplicates
    old_rehab = await db.execute(
        select(ExerciseLibrary).where(ExerciseLibrary.category_l1 == "康复/纠正性训练")
    )
    for old in old_rehab.scalars().all():
        await db.delete(old)
    await db.flush()

    # Insert all rehab exercises
    for ex_data in REHAB_EXERCISE_PRESETS:
        db.add(ExerciseLibrary(**ex_data))
    await db.flush()

    # Create injury links
    link_count = 0
    for ex_name, body_part, risk_factor, priority in REHAB_INJURY_LINKS:
        ex_result = await db.execute(
            select(ExerciseLibrary).where(ExerciseLibrary.name == ex_name)
        )
        exercise = ex_result.scalar_one_or_none()
        if exercise:
            link = ExerciseInjuryLink(
                exercise_id=exercise.id,
                injury_body_part=body_part,
                risk_factor=risk_factor,
                priority=priority,
            )
            db.add(link)
            link_count += 1

    await db.commit()
    logger.info(f"Seeded {len(REHAB_EXERCISE_PRESETS)} rehab exercises + {link_count} injury links")
    return {"status": "seeded", "rehab_count": len(REHAB_EXERCISE_PRESETS), "injury_links": link_count}


@router.get("/injury-links/{body_part}")
async def get_exercises_for_injury(
    body_part: str,
    db: AsyncSession = Depends(get_db),
):
    """Get exercises linked to a specific injury body part (elbow/knee/shoulder/wrist/back)."""
    result = await db.execute(
        select(ExerciseInjuryLink, ExerciseLibrary)
        .join(ExerciseLibrary, ExerciseInjuryLink.exercise_id == ExerciseLibrary.id)
        .where(ExerciseInjuryLink.injury_body_part == body_part.lower())
        .order_by(ExerciseInjuryLink.priority, ExerciseInjuryLink.risk_factor)
    )
    rows = result.all()
    return {
        "body_part": body_part,
        "exercises": [
            {
                "exercise_id": str(ex.id),
                "name": ex.name,
                "category_l2": ex.category_l2,
                "nasm_phase": ex.nasm_phase,
                "risk_factor": link.risk_factor,
                "priority": link.priority,
                "instructions": ex.instructions,
                "target_muscles": ex.target_muscles,
                "literature_ref": ex.literature_ref,
                "preset_params": ex.preset_params,
            }
            for link, ex in rows
        ],
    }
