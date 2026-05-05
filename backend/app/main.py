from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import contextlib
from contextlib import asynccontextmanager
from datetime import datetime, date, timedelta
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import traceback

from app.api import (athletes, training, dashboard, alerts, readiness, exercise_library,
    planner, coach_comments, injury, team_groups, templates, nutrition, mental,
    favorites, wellness, data_generator, competitions, recovery, alerts_enhanced,
    training_logs_v2, training_plans, rehab, journal_generator_api, pro_data_enrichment, auto_adjust)
from app.database import engine, Base, logger, get_db, async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.api.training_plans import seed_preset_templates
    async with async_session() as db:
        await seed_preset_templates(db)
    task = asyncio.create_task(_daily_metric_computation())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def _daily_metric_computation():
    from app.models.athlete import Athlete, TrainingLog, ComputedMetric
    from app.core.acwr import ACWRCalculator, TrainingSession
    from app.core.monotony_strain import MonotonyCalculator
    await asyncio.sleep(30)
    while True:
        try:
            async with async_session() as db:
                athletes = (await db.execute(select(Athlete))).scalars().all()
                calc_start = date.today() - timedelta(days=42)
                for athlete in athletes:
                    logs = (await db.execute(select(TrainingLog).where(
                        TrainingLog.athlete_id == athlete.id,
                        TrainingLog.training_date >= calc_start,
                    ).order_by(TrainingLog.training_date.asc()))).scalars().all()
                    if not logs:
                        continue
                    sessions = [TrainingSession(date=log.training_date, session_load=log.session_load or 0, training_type=log.training_type or "") for log in logs]
                    acwr_result = ACWRCalculator().calculate_timeseries(sessions)
                    latest = acwr_result[-1] if acwr_result else None
                    loads_7d = [s.session_load for s in sessions if (date.today() - s.date).days <= 7]
                    strain_result = MonotonyCalculator().calculate(loads_7d, date.today() - timedelta(days=7), date.today())
                    db.add(ComputedMetric(
                        athlete_id=athlete.id, calc_date=date.today(),
                        acute_load_7d=latest.acute_load if latest else 0,
                        chronic_load_28d=latest.chronic_load if latest else 0,
                        acwr=latest.acwr if latest else 0,
                        acwr_risk_zone=latest.risk_zone if latest else "安全区",
                        monotony=strain_result.monotony if strain_result.monotony != float('inf') else 0,
                        strain=strain_result.strain if strain_result.strain != float('inf') else 0,
                        strain_zscore=strain_result.strain_zscore,
                    ))
                await db.commit()
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(3600)


app = FastAPI(
    title="AthleteIQ - 运动员数据监测系统",
    description="""
基于 **NSCA-CSCS** 和 **CPSS** 标准的运动员监测与训练管理系统。

核心功能:
- **训练负荷监控**: Session RPE、ACWR (急慢性负荷比)、单调性与应变
- **恢复状态评估**: RSSI (恢复-应激状态指数)、HRV、晨起心率
- **过度训练预警**: 多维综合诊断 (CPSS 共识)
- **个性化训练建议**: 基于周期化原则的周训练模板生成
- **体能测试追踪**: 力量/速度/耐力数据的统计显著性分析
    """,
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {str(exc)[:200]}", "path": str(request.url.path)})

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"IntegrityError on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=409, content={"detail": "数据冲突", "path": str(request.url.path)})


# CORS
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ROUTERS = [athletes, training, dashboard, alerts, readiness, exercise_library, planner,
    coach_comments, injury, team_groups, templates, nutrition, mental, favorites, wellness,
    data_generator, competitions, recovery, alerts_enhanced, training_logs_v2, training_plans,
    rehab, journal_generator_api, pro_data_enrichment, auto_adjust]
for r in ROUTERS:
    app.include_router(r.router)


@app.get("/")
async def root():
    return {"name": "AthleteIQ", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "timestamp": str(datetime.utcnow())}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})
