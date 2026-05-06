"""
AthleteIQ - Training Templates & Assignments API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from uuid import UUID
from typing import List, Optional

from app.database import get_db, logger
from app.models.athlete import (
    Athlete, DailyMetric, TrainingTemplate, TrainingAssignment,
)
from app.schemas.schemas import (
    TrainingTemplateCreate, TrainingTemplateUpdate, TrainingTemplateResponse,
    TrainingAssignmentCreate, TrainingAssignmentResponse,
)

router = APIRouter(prefix="/api", tags=["训练模板与计划"])

# ============ 17 Evidence-Based Preset Templates (11 Badminton + 6 Universal) ============

PRESET_TEMPLATES = [
    # ================================================================
    # Template 1: 基础力量训练
    # ================================================================
    {
        "name": "基础力量训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["力量", "基础"],
        "weekly_frequency": "2-3次（非连续日）",
        "is_public": True, "description": "低强度力量基础：上肢+下肢+核心稳定性，为后续爆发力训练建立最大力量储备",
        "content": {"target_load": 45, "target_rpe": 5, "target_duration_min": 75, "total_minutes": 75,
            "weekly_frequency": "2-3次（非连续日）",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 15, "rpe": 3,
                 "content": "肩袖激活（弹力带肩外旋、YTW伸展）+ 臀肌激活（臀桥、蚌式）+ 核心激活（鸟狗式、死虫式）",
                 "evidence": "羽毛球初学者运动损伤率高达42%，动态热身10~15分钟可激活挥拍所需肌群，预防损伤。"},
                {"name": "力量基础—上肢", "type": "力量", "duration_min": 20, "rpe": 5,
                 "content": "俯卧撑（膝式或常规）3组×8-12次；弹力带划船3组×12次；哑铃/弹力带肩推3组×10次",
                 "evidence": "羽毛球技术为主导、体能为支撑，基础力量为后续爆发力训练提供最大力量储备。"},
                {"name": "力量基础—下肢", "type": "力量", "duration_min": 15, "rpe": 5,
                 "content": "自重深蹲3组×12次；弓步蹲3组×10次/侧；臀桥3组×15次",
                 "evidence": "下肢在杀球起跳和快速启动中至关重要，要求高强度的爆发力与敏捷性。"},
                {"name": "核心稳定性", "type": "力量", "duration_min": 10, "rpe": 4,
                 "content": "平板支撑3组×30-45秒；侧平板支撑2组×30秒/侧；仰卧举腿3组×12次",
                 "evidence": "核心稳定增强击球控制力，减少非受迫性失误。"},
                {"name": "冷身整理", "type": "耐力", "duration_min": 5, "rpe": 2,
                 "content": "5分钟缓慢慢跑（50-60%心率），帮助清除乳酸、逐渐降低心率和呼吸",
                 "evidence": "积极恢复有助于代谢产物清除。"},
                {"name": "静态拉伸", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "腘绳肌、股四头肌、小腿、肩部、前臂各20-30秒",
                 "evidence": "静态拉伸有助于恢复肌肉长度、降低紧张、促进血液循环。"},
            ]},
    },
    # ================================================================
    # Template 2: 专项耐力训练
    # ================================================================
    {
        "name": "专项耐力训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "中", "target_focus": ["耐力", "专项"],
        "weekly_frequency": "1-2次",
        "is_public": True, "description": "中强度专项耐力：多球连续杀接杀+全场四角跑动+间歇步法，模拟实战能耗模式",
        "content": {"target_load": 65, "target_rpe": 7, "target_duration_min": 72, "total_minutes": 72,
            "weekly_frequency": "1-2次",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 15, "rpe": 3,
                 "content": "米字步法慢速预热 + 动态拉伸（高抬腿、后踢腿、开合跳）",
                 "evidence": ""},
                {"name": "多球连续杀接杀训练", "type": "技战术", "duration_min": 15, "rpe": 7,
                 "content": "1分钟全力回击 + 2分钟休息，重复5组",
                 "evidence": "采用持续90分钟训练后，每次训练的负荷变化控制在周增幅10%以内，避免ACWR超过1.3。"},
                {"name": "全场四角跑动接球", "type": "技战术", "duration_min": 15, "rpe": 7,
                 "content": "教练喂球至四角，运动员快速覆盖全场接球，每组15次×3组，组间休息90秒",
                 "evidence": "模拟实战中快速移动和连续性击球的耐力需求。"},
                {"name": "间歇步法训练", "type": "耐力", "duration_min": 12, "rpe": 7,
                 "content": "6点米字步法间歇冲刺（启动→触网→回中→后退），每组6点×8次，间歇比1:1",
                 "evidence": "基于比赛时间结构分析构建专项步法爆发力间歇训练计划。"},
                {"name": "冷身慢跑", "type": "耐力", "duration_min": 5, "rpe": 2,
                 "content": "5分钟低强度慢跑（50-60%最大心率）",
                 "evidence": ""},
                {"name": "静态拉伸+泡沫轴", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "重点放松小腿、股四头肌、腘绳肌、肩部，可用按摩球放松腕伸肌和旋转肌群",
                 "evidence": "泡沫轴释放激痛点，改善血流，加速组织氧合。"},
            ]},
    },
    # ================================================================
    # Template 3: 速度爆发训练
    # ================================================================
    {
        "name": "速度爆发训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "高", "target_focus": ["速度", "爆发力"],
        "weekly_frequency": "1-2次（与力量日间隔48小时）",
        "is_public": True, "description": "高强度爆发力：复合训练法(PAPE效应)+跳箱+杀球专项+短距离冲刺",
        "content": {"target_load": 85, "target_rpe": 8, "target_duration_min": 80, "total_minutes": 80,
            "weekly_frequency": "1-2次（与力量日间隔48小时）",
            "segments": [
                {"name": "专项激活", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "动态拉伸 + 弹力带抗阻步法（侧移、交叉步、后退步激活神经肌肉）",
                 "evidence": ""},
                {"name": "跳箱连续蹲跳", "type": "力量", "duration_min": 10, "rpe": 8,
                 "content": "30cm跳箱连续蹲跳10次×3组，组间休息45秒",
                 "evidence": "提升下肢爆发力的经典增强式训练，适用于起跳杀球需求。"},
                {"name": "复合训练法（Complex Training）", "type": "力量", "duration_min": 18, "rpe": 9,
                 "content": "深蹲（75-85% 1RM，6次）→ 休息30秒→ 跳箱（5次） → 休息3分钟 ×3组",
                 "evidence": "利用PAPE效应增强爆发力：大重量运动后PAPE效应持续5-10分钟，激活神经肌肉增强后续爆发力。"},
                {"name": "杀球专项爆发力", "type": "技战术", "duration_min": 12, "rpe": 8,
                 "content": "杀球起跳练习（无球）10次×3组 + 多球杀球训练（15次/组×3组，连续杀球）",
                 "evidence": "下肢爆发力与短距离冲刺、方向变化能力高度相关，上肢鞭打效应传递动能。"},
                {"name": "短距离冲刺", "type": "速度", "duration_min": 10, "rpe": 9,
                 "content": "5米、10米、20米冲刺，每组各2次，组间休息按1:5工作休息比",
                 "evidence": "复合训练法对5/10/20米冲刺提速效果显著优于传统抗阻训练。"},
                {"name": "冷身+拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟低强度慢跑 + 10分钟静态拉伸（下肢大肌群+肩袖肌群）",
                 "evidence": ""},
            ]},
    },
    # ================================================================
    # Template 4: 技术打磨训练
    # ================================================================
    {
        "name": "技术打磨训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "极高", "target_focus": ["技术", "战术"],
        "weekly_frequency": "2次（技术日）",
        "is_public": True, "description": "高强度技战术：吊上网循环+网前两点步法+录像分析拆解+实战模拟",
        "content": {"target_load": 70, "target_rpe": 6, "target_duration_min": 92, "total_minutes": 92,
            "weekly_frequency": "2次（技术日）",
            "segments": [
                {"name": "动态准备", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "低强度有氧5分钟 + 专项挥拍准备（正手/反手高远球空挥30次）",
                 "evidence": ""},
                {"name": "吊球上网搓球循环", "type": "技战术", "duration_min": 15, "rpe": 6,
                 "content": "接发高球→两拍直线高球→第三拍吊直线上网搓球→回位",
                 "evidence": "陈其遒训练模式：重复两拍高球再吊球上网，提升吊上网连贯性节奏感。"},
                {"name": "网前两点上网步法", "type": "技战术", "duration_min": 12, "rpe": 6,
                 "content": "正手接网前球→反手接网前球，来回快速反应",
                 "evidence": "正反手接网前球步法通用总结：正手两步反手一步，提升网前应对能力。"},
                {"name": "录像分析与技术拆解", "type": "混合", "duration_min": 25, "rpe": 5,
                 "content": "分析对手及自身比赛录像15分钟，讨论技术缺陷与战术对策后再上场实练",
                 "evidence": "录像分析可帮助教练和运动员更科学地制订训练计划，减少错误动作模式。"},
                {"name": "实战模拟", "type": "混合", "duration_min": 15, "rpe": 7,
                 "content": "对抗练习15分钟（半场压制对攻），聚焦特定技术",
                 "evidence": "将分析得出的技术缺陷在场上实战中针对性修正。"},
                {"name": "冷却+拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟冷身 + 10分钟全身静态拉伸，尤其放松前臂、手腕和小鱼际肌",
                 "evidence": "赛后重点按摩小鱼际肌群可提升23%控球稳定性。"},
            ]},
    },
    # ================================================================
    # Template 5: 恢复调整训练
    # ================================================================
    {
        "name": "恢复调整训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["恢复", "柔韧", "康复"],
        "weekly_frequency": "1-2次（安排在高强度日次日为佳）",
        "is_public": True, "description": "低强度主动恢复：有氧恢复+本体感觉训练+康复预防+身心放松",
        "content": {"target_load": 20, "target_rpe": 3, "target_duration_min": 50, "total_minutes": 50,
            "weekly_frequency": "1-2次（安排在高强度日次日为佳）",
            "segments": [
                {"name": "低强度有氧恢复", "type": "耐力", "duration_min": 20, "rpe": 3,
                 "content": "慢跑/游泳/骑自行车15-20分钟（50-60%最大心率）",
                 "evidence": "游泳是绝佳的低冲击恢复工具，水的浮力减少压力同时促进血流和主动恢复。"},
                {"name": "本体感觉/康复预防", "type": "柔韧", "duration_min": 15, "rpe": 3,
                 "content": "单腿平衡训练（每侧30秒×3组）+ 弹力带肩袖强化（肩外旋、内旋、YTW伸展，15次×3组）",
                 "evidence": "羽毛球常见损伤部位为肩袖、前臂、膝部、腰背，本体感觉训练强化关节稳定性。"},
                {"name": "拉伸与身心放松", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "全身静态拉伸（大肌群+肩袖+前臂各20-30秒）+ 深呼吸放松5分钟",
                 "evidence": "拉伸可放松肌肉、消除紧张；深呼吸触发副交感神经系统，帮助身体切换到恢复模式。"},
            ]},
    },
    # ================================================================
    # Template 6: 比赛模拟训练
    # ================================================================
    {
        "name": "比赛模拟训练", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "中", "target_focus": ["实战", "对抗"],
        "weekly_frequency": "1次（临近比赛周可增至2次）",
        "is_public": True, "description": "21分制全场对抗+关键分情景模拟+录像分析+针对性短板强化",
        "content": {"target_load": 75, "target_rpe": 7, "target_duration_min": 85, "total_minutes": 85,
            "weekly_frequency": "1次（临近比赛周可增至2次）",
            "segments": [
                {"name": "专项热身", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "米字步法+平抽快挡预热 + 全场移动预热",
                 "evidence": "激活神经肌肉和反应速度。"},
                {"name": "全场对抗比赛", "type": "混合", "duration_min": 25, "rpe": 9,
                 "content": "21分制正式对抗1-2局，模拟真实比赛节奏（每局间休息2分钟）",
                 "evidence": "结合ACWR监控防止负荷过大；超过ACWR>1.3危险区时次日安排低强度恢复。"},
                {"name": "关键分情景模拟", "type": "混合", "duration_min": 10, "rpe": 8,
                 "content": "16-16/17-18等关键分对抗，训练心理耐压和战术执行力（每局5分钟×2组）",
                 "evidence": ""},
                {"name": "战术录像分析", "type": "混合", "duration_min": 10, "rpe": 2,
                 "content": "对抗后回放分析运动员特定时间段的跑位、出球线路选择与失误类型",
                 "evidence": "录像分析是国内外优秀选手技战术升级的核心训练手段。"},
                {"name": "针对性短板强化", "type": "技战术", "duration_min": 10, "rpe": 6,
                 "content": "根据对抗暴露短板进行单项强化训练10分钟（如后场两侧被动过渡、网前搓球稳定性）",
                 "evidence": "将分析结果转化为场上实践。"},
                {"name": "整理活动", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "慢跑5分钟 + 静态拉伸10分钟（重点：全身大肌群+前臂）",
                 "evidence": ""},
            ]},
    },
    # ================================================================
    # Template 7: 基础耐力日
    # ================================================================
    {
        "name": "基础耐力日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "中", "target_focus": ["技术", "步法", "耐力"],
        "weekly_frequency": "1-2次",
        "is_public": True, "description": "技术练习+步法训练+低强度有氧耐力，体能与技术相互融合",
        "content": {"target_load": 60, "target_rpe": 5, "target_duration_min": 80, "total_minutes": 80,
            "weekly_frequency": "1-2次",
            "segments": [
                {"name": "动态准备", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "5分钟慢跑 + 动态拉伸全身（肩、髋、膝、踝全方位活动）",
                 "evidence": ""},
                {"name": "技术练习环节", "type": "技战术", "duration_min": 20, "rpe": 5,
                 "content": "高远球对拉练习，固定落点交替正手/反手各5分钟；平抽挡节奏练习5分钟（两人连续平抽）",
                 "evidence": "体能训练与技术训练相互强化，训练期化分段，相互融合。"},
                {"name": "步法训练环节", "type": "技战术", "duration_min": 15, "rpe": 6,
                 "content": "米字步法练习（每个点位折返触球/障碍物），每组6点×5次，2组；网前两点+后场两点跑动练习",
                 "evidence": "步法是羽毛球致胜的核心，提升移动效率显著提升实战表现。"},
                {"name": "低强度有氧耐力", "type": "耐力", "duration_min": 10, "rpe": 4,
                 "content": "全场跑动接多球5分钟连续（≤60%最大心率），维持有氧区间120-150次/分",
                 "evidence": "结合ACWR监控，确保负荷积累不损伤免疫和内分泌恢复。"},
                {"name": "步法+击球模拟", "type": "技战术", "duration_min": 10, "rpe": 5,
                 "content": "全场跑动并做正手、反手击球挥拍动作，模拟实战连续击球",
                 "evidence": ""},
                {"name": "恢复与拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟冷身慢跑 + 10分钟全身静态拉伸（大肌群+前臂手腕）",
                 "evidence": ""},
            ]},
    },
    # ================================================================
    # Template 8: 爆发力日
    # ================================================================
    {
        "name": "爆发力日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "高", "target_focus": ["爆发力", "杀球", "速度"],
        "weekly_frequency": "1次（与力量日间隔48小时）",
        "is_public": True, "description": "高强度爆发力：杀球发力链拆解+增强式跳箱/跳深+冲刺速度+核心爆发力",
        "content": {"target_load": 85, "target_rpe": 8, "target_duration_min": 80, "total_minutes": 80,
            "weekly_frequency": "1次（与力量日间隔48小时）",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "慢跑、动态拉伸+跳跃准备（轻跳、高抬腿、弓步跳）",
                 "evidence": "激活神经肌肉。"},
                {"name": "杀球专项训练", "type": "技战术", "duration_min": 15, "rpe": 8,
                 "content": "杀球发力链条拆解：转肩后收腹发力；多球杀球练习15次×3组",
                 "evidence": "杀球起跳依赖于腿部肌肉瞬时发力，深蹲/跳箱增强下肢力量。"},
                {"name": "增强式训练跳箱/跳深", "type": "力量", "duration_min": 15, "rpe": 9,
                 "content": "30-40cm跳箱训练/跳深练习5次×3组；连续交叉跳进阶训练，每组8次×3组",
                 "evidence": "增强式训练可通过PAPE效应提高瞬发力和杀球力量。"},
                {"name": "冲刺速度训练", "type": "速度", "duration_min": 12, "rpe": 9,
                 "content": "短距离冲刺5m/10m/15m各2次；折返跑加速/急停能力训练6组",
                 "evidence": "冲刺加速与多方向敏捷性在复合训练后显著改善。"},
                {"name": "核心爆发力", "type": "力量", "duration_min": 8, "rpe": 8,
                 "content": "药球过顶砸地10次×3组；旋转抛球8次×3组",
                 "evidence": "增强身体旋转能力，提升鞭打效应力学效率。"},
                {"name": "冷却恢复", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟慢跑+10分钟静态拉伸（重点：下肢、肩部、核心）",
                 "evidence": ""},
            ]},
    },
    # ================================================================
    # Template 9: 技术日
    # ================================================================
    {
        "name": "技术日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["技术", "精准", "分析"],
        "weekly_frequency": "2次",
        "is_public": True, "description": "低强度技术打磨：吊球劈吊+网前搓球/放网+录像分析+场地实练强化",
        "content": {"target_load": 55, "target_rpe": 5, "target_duration_min": 105, "total_minutes": 105,
            "weekly_frequency": "2次",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "动态拉伸+关节活动度练习：挥拍空挥30次，手腕/肩关节灵活热身",
                 "evidence": ""},
                {"name": "吊球专项训练", "type": "技战术", "duration_min": 20, "rpe": 5,
                 "content": "正手劈吊+滑板吊球交替练习（劈吊手腕快速切球，落点控制在发球线稍前）",
                 "evidence": "技术为主导，体能为支撑，优先保证击球精准度和动作效率。"},
                {"name": "网前技术训练", "type": "技战术", "duration_min": 20, "rpe": 5,
                 "content": "搓球练习（正手搓/反手搓交替，强调贴网和旋转）；放网+推球转换练习",
                 "evidence": "网前两点上网步法（正手两步反手一步）是网前控球基础。"},
                {"name": "录像分析环节", "type": "混合", "duration_min": 20, "rpe": 2,
                 "content": "回放比赛录像或国际顶级选手技术集锦，观察吊球滑板、网前搓球等技术跑位",
                 "evidence": ""},
                {"name": "场地实练强化", "type": "技战术", "duration_min": 20, "rpe": 6,
                 "content": "将录像分析中发现的技术要点转化为场上训练：吊球结合网前搓球连贯练习10分钟+网前球处理10分钟",
                 "evidence": ""},
                {"name": "冷身拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟慢跑 + 10分钟全身静态拉伸（重点放松前臂、肩袖、背肌）",
                 "evidence": ""},
            ]},
    },
    # ================================================================
    # Template 10: 对抗日
    # ================================================================
    {
        "name": "对抗日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "高", "target_focus": ["实战", "战术", "对抗"],
        "weekly_frequency": "1次",
        "is_public": True, "description": "高强度实战：21分制全场比赛+战术模拟+关键分情景+跑位改进与弱点强化",
        "content": {"target_load": 80, "target_rpe": 8, "target_duration_min": 100, "total_minutes": 100,
            "weekly_frequency": "1次",
            "segments": [
                {"name": "动态热身+对抗准备", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "全场6点步伐快节奏移动+连续跳跃准备",
                 "evidence": "提升神经兴奋。"},
                {"name": "全场比赛模拟", "type": "混合", "duration_min": 25, "rpe": 9,
                 "content": "21分制1-2局正赛（裁判+记分）",
                 "evidence": "注意ACWR负荷管理，防止对抗日过度负荷。"},
                {"name": "战术模拟", "type": "技战术", "duration_min": 20, "rpe": 8,
                 "content": "指定战术任务对抗训练（例如压制反手位+跟进上网），10分钟×2节",
                 "evidence": "战术训练通过录像分析技术和战术数据统计提升临场决策能力。"},
                {"name": "情景对抗", "type": "混合", "duration_min": 10, "rpe": 9,
                 "content": "重要比分阶段模拟17-17/18-18等关键分对抗",
                 "evidence": "强化心理与执行耐力。"},
                {"name": "跑位改进与弱点强化", "type": "技战术", "duration_min": 10, "rpe": 6,
                 "content": "根据对抗中暴露的战术执行短板针对性训练10分钟（如被动过渡、反手过渡质量+回位训练）",
                 "evidence": "录像观察可发现技术执行偏差并针对性修正。"},
                {"name": "冷身整理", "type": "柔韧", "duration_min": 20, "rpe": 2,
                 "content": "5分钟慢跑+15分钟静态拉伸（全身大肌群，重点关注膝、肩、前臂）",
                 "evidence": "缓解延迟性肌肉酸痛（DOMS），防止疲劳堆积。"},
            ]},
    },
    # ================================================================
    # Template 11: 赛前减量日
    # ================================================================
    {
        "name": "赛前减量日", "type": "daily", "sport": "羽毛球",
        "intensity_zone": "低", "target_focus": ["恢复", "技术", "心理"],
        "weekly_frequency": "赛前2-3天执行1-2次",
        "is_public": True, "description": "赛前减量：轻量技术巩固+反应步法+心理预演+拉伸恢复，负荷下降20-40%",
        "content": {"target_load": 35, "target_rpe": 3, "target_duration_min": 75, "total_minutes": 75,
            "weekly_frequency": "赛前2-3天执行1-2次",
            "segments": [
                {"name": "专项激活", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "全场慢速米字步法移动10分钟+低强度挥拍（30%最大力量）",
                 "evidence": "强化神经肌肉记忆。"},
                {"name": "轻量技术巩固", "type": "技战术", "duration_min": 20, "rpe": 3,
                 "content": "单一技术巩固（网前搓球稳定性/高远球落点精准控制）配合教练喂球限区域练习",
                 "evidence": "赛前减量阶段负荷下降20-40%以便神经肌肉从疲劳中恢复，储备比赛爆发力。"},
                {"name": "轻量步法+反应训练", "type": "技战术", "duration_min": 15, "rpe": 4,
                 "content": "全场不同点位落球反应步法练习，侧重于反应速度和步法正确性",
                 "evidence": "步法训练目的是保持神经肌肉控制而不是增加疲劳。"},
                {"name": "心理预演/战术影像分析", "type": "混合", "duration_min": 10, "rpe": 1,
                 "content": "比赛路线和战术录像分析5分钟+正念/心理预演5分钟",
                 "evidence": "心理干预是多重周期化模型重要组成部分，有助于保持竞技状态。"},
                {"name": "冷身整理", "type": "柔韧", "duration_min": 20, "rpe": 2,
                 "content": "5分钟慢跑+15分钟静态拉伸（全身放松、灵活度保持）",
                 "evidence": "静态拉伸有助于消除肌肉紧张，加速血液循环，减轻疲劳。"},
            ]},
    },
    # ================================================================
    # Template 12: 基础力量训练（通用）
    # 普适版 — 适用于球类、田径、格斗等大多数项目
    # ================================================================
    {
        "name": "基础力量训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "低", "target_focus": ["力量", "基础"],
        "weekly_frequency": "2-3次（非连续日）",
        "is_public": True, "description": "通用低强度力量基础：下肢+上肢推拉+核心稳定性，无需器械，适合所有运动项目早期基础力量阶段",
        "content": {"target_load": 40, "target_rpe": 5, "target_duration_min": 70, "total_minutes": 70,
            "weekly_frequency": "2-3次（非连续日）",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 12, "rpe": 3,
                 "content": "关节活动（肩、髋、膝、踝） + 臀肌激活（臀桥、蚌式） + 核心激活（鸟狗式、平板支撑变式）",
                 "evidence": "激活主要肌群，预防损伤。动态热身可提高肌肉温度、增加关节活动度。"},
                {"name": "下肢力量基础", "type": "力量", "duration_min": 18, "rpe": 5,
                 "content": "自重深蹲 3×12次；保加利亚分腿蹲（无负重或轻负重）3×10次/侧；臀桥 3×15次",
                 "evidence": "发展下肢基础力量和关节稳定性，为后续爆发力训练打底。保加利亚分腿蹲能有效纠正左右不平衡。"},
                {"name": "上肢推力", "type": "力量", "duration_min": 10, "rpe": 5,
                 "content": "俯卧撑（标准或跪姿）3×8~12次；平板支撑交替抬手 3×10次/侧",
                 "evidence": "提升推力和核心抗旋转能力。俯卧撑是上肢基础力量的黄金动作。"},
                {"name": "上肢拉力/背部", "type": "力量", "duration_min": 10, "rpe": 5,
                 "content": "弹力带划船 3×12次；弹力带肩胛后缩 3×15次",
                 "evidence": "强化上背部与肩袖，改善姿态，预防圆肩。"},
                {"name": "核心稳定性", "type": "力量", "duration_min": 10, "rpe": 4,
                 "content": "死虫式 3×10次/侧；臀桥抬单腿 3×12次/侧",
                 "evidence": "深层核心激活，提升运动中的躯干刚性。"},
                {"name": "冷身拉伸", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "全身静态拉伸（腘绳肌、股四头肌、胸大肌、背阔肌各20-30秒）",
                 "evidence": "促进恢复，降低肌肉紧张度。"},
            ]},
    },
    # ================================================================
    # Template 13: 专项耐力训练（通用）
    # 普适版 — 适用于足球、篮球、网球等需要反复高强度跑动的项目
    # ================================================================
    {
        "name": "专项耐力训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "中", "target_focus": ["耐力", "专项"],
        "weekly_frequency": "1-2次",
        "is_public": True, "description": "通用中强度耐力：间歇跑+节奏跑+变向能力耐力，提升有氧阈和乳酸耐受，可用自行车或划船机替代跑步",
        "content": {"target_load": 60, "target_rpe": 6, "target_duration_min": 65, "total_minutes": 65,
            "weekly_frequency": "1-2次",
            "segments": [
                {"name": "动态热身", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "慢跑5分钟 + 动态拉伸（高抬腿、后踢腿、开合跳、弓步转体）",
                 "evidence": "提升心率和肌肉温度，预防拉伤。"},
                {"name": "间歇跑（有氧-无氧混合）", "type": "耐力", "duration_min": 16, "rpe": 7,
                 "content": "400米跑×4组，组间休息90秒（配速为80%最大努力）",
                 "evidence": "提升乳酸耐受和最大摄氧量。400米间歇是经典的耐力训练手段。"},
                {"name": "节奏跑", "type": "耐力", "duration_min": 15, "rpe": 6,
                 "content": "以'能说话但吃力'的强度持续跑15分钟",
                 "evidence": "提高有氧阈值，适合大多数球类和耐力项目。"},
                {"name": "变向能力耐力", "type": "耐力", "duration_min": 12, "rpe": 7,
                 "content": "20米折返跑（Beep测试模式） × 6次，每次休息30秒",
                 "evidence": "模拟比赛中反复冲刺-减速-变向的需求。"},
                {"name": "冷身慢跑", "type": "耐力", "duration_min": 5, "rpe": 2,
                 "content": "5分钟极慢跑（心率降至120以下）",
                 "evidence": "清除乳酸，避免血液淤积。"},
                {"name": "静态拉伸", "type": "柔韧", "duration_min": 7, "rpe": 2,
                 "content": "大腿前后侧、小腿、髋部各20秒",
                 "evidence": "恢复肌肉长度，减少DOMS。"},
            ]},
    },
    # ================================================================
    # Template 14: 速度爆发训练（通用）
    # 普适版 — 适用于篮球、排球、田径短跑、格斗等需要短距离加速和跳跃的项目
    # ================================================================
    {
        "name": "速度爆发训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "高", "target_focus": ["速度", "爆发力"],
        "weekly_frequency": "1-2次（与力量日间隔48小时）",
        "is_public": True, "description": "通用高强度爆发力：增强式训练(PAPE效应)+跳箱+短距离冲刺+反应速度，跳箱可用台阶替代",
        "content": {"target_load": 85, "target_rpe": 8, "target_duration_min": 75, "total_minutes": 75,
            "weekly_frequency": "1-2次（与力量日间隔48小时）",
            "segments": [
                {"name": "神经激活", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "动态拉伸 + 快速小步跑、高抬腿、后蹬跑各30秒×2组",
                 "evidence": "激活神经系统，提升动作频率。"},
                {"name": "增强式训练", "type": "力量", "duration_min": 15, "rpe": 8,
                 "content": "跳箱（30-45cm）3×5次；立定跳远3×4次；连续纵跳2×8次",
                 "evidence": "提升下肢反应力和爆发力。增强式训练利用牵张缩短循环（SSC）。"},
                {"name": "复合爆发力组合", "type": "力量", "duration_min": 18, "rpe": 9,
                 "content": "轻负荷跳蹲（20%1RM）×6次 → 休息15秒 → 跳箱×3次，重复3组，组间休息3分钟",
                 "evidence": "利用PAPE（后激活增强效应）最大化爆发力输出。"},
                {"name": "短距离冲刺", "type": "速度", "duration_min": 12, "rpe": 9,
                 "content": "10米×3次、20米×3次、30米×2次，休息比1:5",
                 "evidence": "发展加速能力和最大速度。短冲对神经肌肉要求极高。"},
                {"name": "反应速度训练", "type": "速度", "duration_min": 10, "rpe": 7,
                 "content": "听信号/视觉信号冲刺5米×6次（不同起始姿势）",
                 "evidence": "提升启动反应时，对比赛关键动作有益。"},
                {"name": "冷身+拉伸", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟慢跑 + 10分钟静态拉伸（重点：腘绳肌、股四头肌、髋屈肌、小腿）",
                 "evidence": "降低肌肉过度紧张风险，促进恢复。"},
            ]},
    },
    # ================================================================
    # Template 15: 技术打磨训练（通用）
    # 普适版 — 适用于所有技巧性项目（球类、体操、跳水、格斗等）
    # ================================================================
    {
        "name": "技术打磨训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "极高", "target_focus": ["技术", "精准", "分析"],
        "weekly_frequency": "2次",
        "is_public": True, "description": "通用技术打磨：封闭性技术循环+开放性情景模拟+录像纠错+针对性强化，认知负荷高，可替换为项目专项技术动作",
        "content": {"target_load": 65, "target_rpe": 6, "target_duration_min": 90, "total_minutes": 90,
            "weekly_frequency": "2次",
            "segments": [
                {"name": "专项准备活动", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "徒手模仿关键技术动作（如投篮、挥拍、踢腿）30次 + 动态关节活动",
                 "evidence": "活化技术相关神经肌肉通路。"},
                {"name": "封闭性技术循环", "type": "技战术", "duration_min": 25, "rpe": 6,
                 "content": "单一技术重复练习（例如固定点投篮/对墙传球/定点踢准），要求成功率>80%",
                 "evidence": "动作自动化的关键。高质量重复形成正确运动记忆。"},
                {"name": "开放性情景模拟", "type": "技战术", "duration_min": 20, "rpe": 7,
                 "content": "设计2-3种压力情景（防守干扰、时间限制），执行同一技术",
                 "evidence": "提升技术在对抗下的稳定性。符合'感知-行动'耦合原则。"},
                {"name": "录像分析/纠错", "type": "混合", "duration_min": 15, "rpe": 2,
                 "content": "回放个人技术动作，与标准模型对比，找出偏差",
                 "evidence": "视觉反馈促进动作学习。"},
                {"name": "针对性强化", "type": "技战术", "duration_min": 20, "rpe": 6,
                 "content": "针对刚才发现的技术缺陷，再次进行封闭性练习（10分钟） + 低强度压力情景（10分钟）",
                 "evidence": "即时修正，巩固正确模式。"},
                {"name": "整理活动", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "5分钟低强度有氧 + 5分钟全身静态拉伸 + 5分钟呼吸放松",
                 "evidence": "技术训练后神经系统恢复尤为重要。"},
            ]},
    },
    # ================================================================
    # Template 16: 恢复调整训练（通用）
    # 普适版 — 任何运动员高强度日后均可使用，完全通用
    # ================================================================
    {
        "name": "恢复调整训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "低", "target_focus": ["恢复", "柔韧", "康复"],
        "weekly_frequency": "1-2次（高强度日后安排）",
        "is_public": True, "description": "通用低强度主动恢复：有氧+本体感觉+筋膜放松+静态拉伸+呼吸冥想，比纯休息更有效的恢复策略",
        "content": {"target_load": 15, "target_rpe": 2, "target_duration_min": 50, "total_minutes": 50,
            "weekly_frequency": "1-2次（高强度日后安排）",
            "segments": [
                {"name": "低强度有氧", "type": "耐力", "duration_min": 20, "rpe": 3,
                 "content": "游泳/慢跑/自行车（心率<120次/分），促进血液循环",
                 "evidence": "主动恢复可加速代谢产物清除，比纯休息更有效。"},
                {"name": "本体感觉与稳定性", "type": "柔韧", "duration_min": 10, "rpe": 3,
                 "content": "单腿站立（睁眼/闭眼）每侧1分钟×3组；不稳定平面平衡（如枕头）",
                 "evidence": "增强关节稳定性，预防损伤。对脚踝、膝盖康复尤其重要。"},
                {"name": "筋膜放松", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "泡沫轴放松大腿前/后/外侧、小腿、背部，每个部位30秒",
                 "evidence": "缓解肌肉紧张点，改善组织延展性。"},
                {"name": "全身静态拉伸", "type": "柔韧", "duration_min": 10, "rpe": 2,
                 "content": "每个主要肌群30秒，配合深呼吸（吸气伸展，呼气加深）",
                 "evidence": "改善柔韧性，激活副交感神经。"},
                {"name": "呼吸放松/冥想", "type": "柔韧", "duration_min": 5, "rpe": 1,
                 "content": "腹式呼吸或正念扫描5分钟",
                 "evidence": "降低皮质醇水平，促进心理恢复。"},
            ]},
    },
    # ================================================================
    # Template 17: 比赛模拟训练（通用）
    # 普适版 — 适用于所有对抗性项目，非对抗项目可替换为比赛环境模拟
    # ================================================================
    {
        "name": "比赛模拟训练（通用）", "type": "daily", "sport": "通用",
        "intensity_zone": "中", "target_focus": ["实战", "战术", "对抗"],
        "weekly_frequency": "1次（比赛周期可增至2次）",
        "is_public": True, "description": "通用实战模拟：正式对抗赛+关键场景模拟+即时复盘+短板强化，精神强度极高，适合所有对抗性项目",
        "content": {"target_load": 70, "target_rpe": 7, "target_duration_min": 95, "total_minutes": 95,
            "weekly_frequency": "1次（比赛周期可增至2次）",
            "segments": [
                {"name": "比赛节奏热身", "type": "柔韧", "duration_min": 15, "rpe": 4,
                 "content": "动态热身 + 专项动作预热（如移动接球、轻度对抗）",
                 "evidence": "提升神经兴奋度，进入竞技模式。"},
                {"name": "正式对抗赛", "type": "混合", "duration_min": 30, "rpe": 9,
                 "content": "按比赛规则进行（如全场5v5篮球、11v11足球、21分制羽毛球），记录比分",
                 "evidence": "模拟真实比赛强度，检验技战术和体能。"},
                {"name": "关键场景模拟", "type": "混合", "duration_min": 20, "rpe": 8,
                 "content": "比分落后、最后2分钟、发球权争夺等压力情景，进行小型对抗（5-10分钟×2组）",
                 "evidence": "提升心理抗压能力和决策质量。"},
                {"name": "战术录像/即时复盘", "type": "混合", "duration_min": 10, "rpe": 2,
                 "content": "观看刚才对抗中的2-3个回合，指出战术执行问题",
                 "evidence": "视觉反馈加速战术学习。"},
                {"name": "短板强化", "type": "技战术", "duration_min": 10, "rpe": 6,
                 "content": "针对比赛中暴露的弱点（如防守轮转、反击衔接）进行10分钟专项演练",
                 "evidence": "将复盘结论转化为行动。"},
                {"name": "整理活动", "type": "柔韧", "duration_min": 15, "rpe": 2,
                 "content": "慢跑5分钟 + 静态拉伸10分钟 + 冰敷/冷水浴（可选）",
                 "evidence": "快速降低核心温度，减轻炎症反应。"},
            ]},
    },
]


async def seed_preset_templates(db: AsyncSession):
    """Seed or upgrade 17 evidence-based preset templates."""
    existing = await db.execute(
        select(TrainingTemplate).where(TrainingTemplate.created_by.is_(None))
    )
    system_templates = existing.scalars().all()

    # Detect if templates are stale (old format without evidence in segments)
    stale = False
    if system_templates:
        first_tmpl = system_templates[0]
        segments = (first_tmpl.content or {}).get('segments', [])
        if segments and 'evidence' not in segments[0]:
            stale = True

    if not system_templates or stale or len(system_templates) != len(PRESET_TEMPLATES):
        # Remove stale system templates
        if system_templates:
            for tmpl in system_templates:
                await db.delete(tmpl)
            await db.flush()
        # Re-seed
        for tmpl in PRESET_TEMPLATES:
            db.add(TrainingTemplate(**tmpl))
        await db.commit()
        logger.info(f"Seeded {len(PRESET_TEMPLATES)} preset templates"
                    f"{' (upgraded from old format)' if stale else ''}")


# ============ Template CRUD ============

@router.get("/templates", response_model=List[TrainingTemplateResponse])
async def list_templates(
    type: Optional[str] = Query(None),
    focus: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await seed_preset_templates(db)
    query = select(TrainingTemplate)
    if type:
        query = query.where(TrainingTemplate.type == type)
    if focus:
        query = query.where(TrainingTemplate.target_focus.contains([focus]))
    query = query.order_by(TrainingTemplate.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/templates", response_model=TrainingTemplateResponse, status_code=201)
async def create_template(data: TrainingTemplateCreate, db: AsyncSession = Depends(get_db)):
    template = TrainingTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=TrainingTemplateResponse)
async def update_template(template_id: UUID, data: TrainingTemplateUpdate, db: AsyncSession = Depends(get_db)):
    template = await db.get(TrainingTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    for field in ["name", "type", "intensity_zone", "weekly_frequency", "is_public", "content", "description"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(template, field, val)
    if data.target_focus is not None:
        template.target_focus = data.target_focus
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
async def delete_template(template_id: UUID, db: AsyncSession = Depends(get_db)):
    template = await db.get(TrainingTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    await db.delete(template)
    await db.commit()
    return {"status": "deleted"}


# ============ Assignment CRUD ============

@router.post("/assignments", response_model=TrainingAssignmentResponse, status_code=201)
async def create_assignment(data: TrainingAssignmentCreate, db: AsyncSession = Depends(get_db)):
    athlete = await db.get(Athlete, data.athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="运动员不存在")
    template = await db.get(TrainingTemplate, data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    existing = await db.execute(select(TrainingAssignment).where(
        TrainingAssignment.athlete_id == data.athlete_id,
        TrainingAssignment.scheduled_date == data.scheduled_date))
    assignment = existing.scalar_one_or_none()

    if assignment:
        assignment.template_id = data.template_id
        assignment.overrides = data.overrides or {}
        assignment.notes = data.notes
    else:
        assignment = TrainingAssignment(
            athlete_id=data.athlete_id, template_id=data.template_id,
            scheduled_date=data.scheduled_date,
            overrides=data.overrides or {}, notes=data.notes)
        db.add(assignment)

    await db.commit()
    await db.refresh(assignment)
    assignment.template_name = template.name
    assignment.template_content = template.content
    return assignment


@router.get("/assignments/calendar", response_model=List[TrainingAssignmentResponse])
async def get_calendar_assignments(
    athlete_id: UUID = Query(...),
    month: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(TrainingAssignment).where(TrainingAssignment.athlete_id == athlete_id)
    if month:
        year, mon = month.split("-")
        start_date = date(int(year), int(mon), 1)
        if int(mon) == 12:
            end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(int(year), int(mon) + 1, 1) - timedelta(days=1)
        query = query.where(TrainingAssignment.scheduled_date >= start_date,
                           TrainingAssignment.scheduled_date <= end_date)
    query = query.order_by(TrainingAssignment.scheduled_date.asc())
    result = await db.execute(query)
    assignments = result.scalars().all()
    for a in assignments:
        if a.template_id:
            tmpl = await db.get(TrainingTemplate, a.template_id)
            if tmpl:
                a.template_name = tmpl.name
                a.template_content = tmpl.content
    return assignments


@router.post("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: UUID,
    actual_log_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
):
    assignment = await db.get(TrainingAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="计划不存在")
    assignment.status = "completed"
    if actual_log_id:
        assignment.actual_log_id = actual_log_id
    await db.commit()
    return {"status": "completed"}
