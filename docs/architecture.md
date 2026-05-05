# AthleteIQ v2.0 系统架构文档

## 1. 系统架构图 (Mermaid)

```mermaid
graph TB
    subgraph Frontend["Frontend (React 18 + TS + Recharts + Tailwind)"]
        A[仪表板 Dashboard] --> A1[团队热力图 TeamHeatmap]
        B[运动员管理 AthleteList] --> B1[档案/伤病/雷达图 AthleteDetail]
        C[训练日志 TrainingLog] --> C1[准备状态 ReadinessCard]
        C --> C2[教练批注 CoachComment]
        D[训练安排 Planner] --> D1[快捷动作 QuickAddExercise]
        D --> D2[模板库 Templates]
        E[预警中心 Alerts]
        F[报告中心 Reports]
    end

    subgraph API["API Gateway (FastAPI)"]
        G1[/api/athletes] --> DB
        G2[/api/training] --> DB
        G3[/api/dashboard] --> DB
        G4[/api/alerts] --> DB
        G5[/api/readiness] --> DB
        G6[/api/planner] --> DB
        G7[/api/coach] --> DB
        G8[/api/injury] --> DB
        G9[/api/exercises] --> DB
        G10[/api/groups] --> DB
        G11[/api/templates] --> DB
    end

    subgraph Core["Core Engine"]
        ACWR[ACWR Calculator]
        RSSI[RSSI Evaluator]
        MS[Monotony & Strain]
        DEV[Deviation Analyzer]
        DLD[Deload Suggester]
        RADAR[Radar Chart Computer]
        REC[Training Advisor]
    end

    subgraph DB["PostgreSQL 15+"]
        T1[(athletes)]
        T2[(training_logs)]
        T3[(daily_readiness)]
        T4[(exercise_library)]
        T5[(planned_sessions)]
        T6[(planned_exercises)]
        T7[(exercise_logs)]
        T8[(coach_comments)]
        T9[(injury_records)]
        T10[(injury_restrictions)]
        T11[(return_to_play_checklist)]
        T12[(team_groups)]
        T13[(periodization_templates)]
        T14[(wellness_questionnaires)]
        T15[(performance_tests)]
        T16[(computed_metrics)]
        T17[(alert_events)]
    end

    Frontend --> API
    API --> Core
    Core --> DB
```

## 2. 数据库 ER 图 (新增表)

```
athletes ──1:N──> daily_readiness
athletes ──1:N──> injury_records ──1:N──> injury_rehab_logs
                                      ──1:N──> injury_restrictions
                                      ──1:N──> return_to_play_checklist
athletes ──1:N──> planned_sessions ──1:N──> planned_exercises ──N:1──> exercise_library
athletes ──1:N──> training_logs ──1:N──> exercise_logs ──N:1──> exercise_library
training_logs ──1:N──> coach_comments
team_groups ──N:M──> team_group_members ──N:1──> athletes

periodization_templates (coach_id FK->users, nullable=system)
exercise_library (coach_id FK->users, nullable=system)
```

## 3. 完整 API 端点

### 3.1 运动员管理 `/api/athletes`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create athlete |
| GET | `/` | List (filter: sport, group, status) |
| GET | `/{id}` | Detail with profile, injuries, radar data |
| PUT | `/{id}` | Update |
| POST | `/{id}/baseline` | Set baseline value |
| GET | `/{id}/baselines` | Get all baselines |
| POST | `/import` | CSV/Excel batch import |

### 3.2 每日准备状态 `/api/readiness`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Submit daily readiness survey |
| GET | `/{athlete_id}` | Readiness history (date range) |
| GET | `/{athlete_id}/today` | Today's readiness status |

### 3.3 训练日志 `/api/training`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/log` | Submit training log |
| POST | `/log/batch` | Batch import |
| GET | `/log/{athlete_id}` | Get logs (filter: date, type) |
| GET | `/log/{athlete_id}/acwr` | ACWR time series |
| GET | `/log/{athlete_id}/load-summary` | Weekly load summary |

### 3.4 训练计划 `/api/planner`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Create planned session |
| GET | `/sessions` | List planned sessions |
| GET | `/sessions/{id}` | Session detail with exercises |
| PUT | `/sessions/{id}` | Update session |
| DELETE | `/sessions/{id}` | Delete session |
| POST | `/sessions/{id}/assign` | Assign to multiple athletes |
| GET | `/athlete/{id}/today` | Get today's plan for athlete |
| POST | `/sessions/{id}/complete` | Complete plan → create exercise_logs |
| GET | `/sessions/{id}/deviation` | Plan vs actual deviation |

### 3.5 动作库 `/api/exercises`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List exercises (?category=, ?search=) |
| POST | `/` | Create custom exercise |
| PUT | `/{id}` | Update exercise |
| GET | `/categories` | List categories |

### 3.6 教练批注 `/api/coach`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/comments` | Add coach comment + rating |
| GET | `/comments` | List comments (?athlete_id=, dates) |
| PUT | `/comments/{id}` | Update comment |
| DELETE | `/comments/{id}` | Delete comment |

### 3.7 伤病管理 `/api/injury`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/records` | Create injury record |
| GET | `/records` | List injuries (?athlete_id=, ?status=) |
| GET | `/records/{id}` | Injury with restrictions & checklist |
| PUT | `/records/{id}` | Update injury |
| POST | `/records/{id}/rehab-logs` | Add rehab log entry |
| POST | `/records/{id}/restrictions` | Add restriction |
| PUT | `/checklist/{id}` | Update RTP checklist item |
| GET | `/athlete/{id}/active-restrictions` | Active restrictions for planning |

### 3.8 团队分组 `/api/groups`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create group |
| GET | `/` | List groups |
| GET | `/{id}` | Group with members |
| PUT | `/{id}` | Update name |
| POST | `/{id}/members` | Add member |
| DELETE | `/{id}/members/{athlete_id}` | Remove member |
| GET | `/{id}/heatmap` | Team heatmap data |

### 3.9 周期模板 `/api/templates`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List templates (?template_type=, ?cycle_phase=) |
| POST | `/` | Create template |
| GET | `/{id}` | Template detail |
| POST | `/{id}/apply` | Apply template to athlete(s) |

### 3.10 仪表板 `/api/dashboard`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/overview` | Team overview (risk stats, alerts) |
| GET | `/athlete/{id}/rssi` | RSSI analysis |
| GET | `/athlete/{id}/performance-comparison` | Performance changes |
| GET | `/athlete/{id}/recommendation` | Training recommendation |
| GET | `/athlete/{id}/radar` | Radar chart data |

### 3.11 预警 `/api/alerts`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List alerts (filtered) |
| GET | `/unread-count` | Unread count |
| PATCH | `/{id}` | Update status |
| POST | `/{id}/resolve` | Resolve alert |

## 4. 核心算法实现

### 4.1 ACWR (急慢性负荷比)
- 急性: 7天滚动平均 Session RPE Load
- 慢性: 28天滚动平均
- 风险区间: 0.8-1.3 (安全), 1.3-1.5 (谨慎), >1.5/<0.8 (高风险)
- 实现: `backend/app/core/acwr.py`

### 4.2 RSSI (恢复-应激状态指数)
- 5维度加权评分: ACWR(25), 晨脉(25), HRV(25), 疲劳(15), 体能(10)
- 风险等级: 正常(<30), FOR(30-50), NFOR(50-70), OTS(>70)
- 实现: `backend/app/core/rssi.py`

### 4.3 训练偏差分析
- 计划负荷 = Σ(目标重量×目标次数×目标组数)
- 实际负荷 = Σ(实际重量×实际次数×实际组数)
- 偏差率 = (实际-计划)/计划 × 100%
- 连续3天偏差超过阈值(默认±20%) → 触发预警
- 实现: `backend/app/core/deviation.py`

### 4.4 智能减载建议
- 触发: ACWR>1.3连续≥14天 AND (HRV下降 OR 主观疲劳恶化)
- 生成减载模板: 保持强度, 容量降低40%, 增加恢复日
- 实现: `backend/app/core/deload.py`

### 4.5 体能雷达图
- 维度: 力量/爆发力/速度/代谢/敏捷
- 三层叠加: 当前值 / 历史最佳 / 项目常模区间
- 弱点识别: 低于常模1SD → 优先强化提示
- 实现: `backend/app/core/radar.py`

## 5. 前侧组件清单

| 页面 | 组件 | 功能 |
|------|------|------|
| 仪表板 | TeamHeatmap | 团队热力图表格 |
| 运动员列表 | AthleteList | 搜索/筛选/分页/分组 |
| 运动员详情 | RadarChart, ReadinessCard | 雷达图 + 伤病列表 + 档案 |
| 训练日志 | ReadinessCard, CoachComment, ExerciseCard | 准备状态 + 动作记录 + 批注 |
| 训练安排 | QuickAddExercise, ExerciseCard | 快速添加 + 拖拽排序 + 模板 |
| 报告中心 | Reports | ACWR/RSSI图表 + 建议 |

## 6. 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.109+ (async) |
| ORM | SQLAlchemy 2.0 + asyncpg |
| 数据库 | PostgreSQL 15+ |
| 前端 | React 18 + TypeScript + Vite 5 |
| 图表 | Recharts 2.10 (Line, Radar, Bar) |
| 样式 | Tailwind CSS 3.4 |
| 计算 | NumPy 1.24+ / SciPy 1.10+ |
