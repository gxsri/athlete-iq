# AthleteIQ 更新日志

## v2.1.1 — 2026-04-28 — 紧急修复：消除所有写入 API 500 错误

### 诊断结论
31 个写入端点（POST/PUT/PATCH/DELETE）在 14 个 API 文件中**全部缺少 try/except 和日志**。
对任意未处理异常（唯一约束冲突、外键错误、DB 连接丢失），FastAPI 默认返回 500 Internal Server Error。
后端日志完全空白，无法追踪错误根因。

### 基础设施修复

#### 日志系统
- `database.py`: 引入 `logging.basicConfig`（INFO 级别，带时间戳和模块名），导出 `logger = logging.getLogger("athleteiq")`
- 所有 API 文件通过 `from app.database import logger` 统一使用

#### 全局异常处理器 (`main.py`)
- `@app.exception_handler(Exception)` — 捕获所有未处理异常，记录 traceback 到日志，返回 500 + 异常类型名 + 路径
- `@app.exception_handler(IntegrityError)` — SQLAlchemy 完整性冲突 → 返回 409 + 中文错误信息
- `GET /health/check` — 数据库连接验证端点，返回 {status, database, timestamp}

### Schema/Model Bug 修复
| 文件 | Bug | 修复 |
|------|-----|------|
| `schemas.py:CoachCommentCreate` | 缺少 `created_by`（模型 `nullable=False`），导致创建评论必然 409/500 | 新增 `created_by: UUID` |
| `schemas.py:CoachCommentCreate` | `rating` 字段为 Optional，未验证范围 | 改为必填 `Field(ge=1, le=10)` |
| `schemas.py:PeriodizationTemplateResponse` | `weekly_structure` 声明为 `Optional[Dict]` 但 DB 存的是 JSONB 数组 | 类型改为 `Any` |

### 写入端点 try/except 修复 (31 个端点)
所有 POST/PUT/PATCH/DELETE 端点统一应用以下模式：
```python
try:
    # 写入逻辑
    await db.commit()
    logger.info("成功")
    return item
except IntegrityError as e:
    logger.warning(f"完整性错误: {e}")
    raise HTTPException(409, detail=f"数据冲突: ...")
except HTTPException:
    raise  # 保留业务层异常
except Exception as e:
    logger.exception("写入失败")
    raise HTTPException(500, detail=f"保存失败: ...")
```

**受影响的文件（12 个 API 文件）：**
| 文件 | 修复端点 |
|------|---------|
| `training.py` | POST /log, POST /log/batch (关键: commit 移入 try 块) |
| `athletes.py` | POST /, PUT /{id}, POST /{id}/baseline |
| `nutrition.py` | POST / |
| `mental.py` | POST / |
| `readiness.py` | POST / |
| `planner.py` | POST /sessions, PUT /{id}, DELETE /{id}, POST /{id}/assign, POST /{id}/complete |
| `coach_comments.py` | POST /comments, PUT /{id}, DELETE /{id} |
| `exercise_library.py` | POST /, PUT /{id} |
| `injury.py` | POST /records, PUT /{id}, POST /{id}/rehab-logs, POST /{id}/restrictions, PUT /checklist/{id} |
| `team_groups.py` | POST /, PUT /{id}, POST /{id}/members, DELETE /{id}/members/{id} |
| `templates.py` | POST /, POST /{id}/apply |
| `alerts.py` | PATCH /{id}, POST /{id}/resolve |

### 错误响应规范
- **409 Conflict** — 数据完整性冲突（重复键、外键约束）
- **500 Internal Server Error** — 包含 `detail` (`type(exc).__name__` + 前 200 字符错误信息) + 后台日志有完整 traceback
- **404 Not Found** — 业务逻辑层拒绝，维护现有行为
- **422 Unprocessable Entity** — Pydantic 校验失败时 FastAPI 自动返回

### 验证方法
```bash
# 健康检查
curl http://localhost:8000/health/check

# 创建运动员（正常）
curl -X POST http://localhost:8000/api/athletes/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试运动员","date_of_birth":"2000-01-01","gender":"男","sport":"羽毛球"}'

# 重复创建（应返回 409 而非 500）
# 同上请求

# 检查日志输出应有详细信息
```
