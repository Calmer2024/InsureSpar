# 文件：app/api/dashboard.py
"""Dashboard API 路由 — 个人中心数据接口"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.dashboard_service import (
    get_overview,
    get_capabilities,
    get_growth_trend,
    generate_ai_general_review,
)

router = APIRouter(prefix="/api/user/dashboard", tags=["个人中心 Dashboard"])


@router.get("/overview", summary="获取个人训练概览")
def dashboard_overview(db: Session = Depends(get_db)):
    """
    **返回结构**:
    - `user_info`: 用户基础信息（姓名、职级、头像、入职日期）
    - `stats`: 训练统计（总会话数、总时长、成交数、历史平均分）
    """
    data = get_overview(db)
    return {"data": data}


@router.get("/capabilities", summary="获取能力雷达与弱点诊断")
async def dashboard_capabilities(db: Session = Depends(get_db)):
    """
    **返回结构**:
    - `radar`: 6维能力雷达图数据 `{ labels, scores }`
    - `weaknesses`: 薄弱维度 Top3（含低分频次和改进建议）
    - `ai_general_review`: AI 综合分析点评（LLM 生成）
    """
    # 先聚合数据库中的能力数据
    cap_data = get_capabilities(db)

    # 获取 overview 统计作为 LLM 上下文
    overview_data = get_overview(db)

    # 调用 LLM 生成综合点评
    ai_review = await generate_ai_general_review(cap_data, overview_data.get("stats", {}))
    cap_data["ai_general_review"] = ai_review

    # 清理内部字段，不返回给前端
    cap_data.pop("_avg_by_dim", None)
    cap_data.pop("_key_to_label", None)
    cap_data.pop("_reports_count", None)

    return {"data": cap_data}


@router.get("/growth-trend", summary="获取能力成长趋势")
def dashboard_growth_trend(
    period: str = Query("last_10_sessions", description="时间范围（暂仅支持 last_10_sessions）"),
    db: Session = Depends(get_db),
):
    """
    **返回结构**:
    - `x_axis`: 日期标签列表
    - `series`: 各维度分数折线 `{ total, professionalism, compliance, strategy }`
    """
    # 解析 limit（未来支持更多 period 选项）
    limit = 10
    if period == "last_20_sessions":
        limit = 20

    data = get_growth_trend(db, limit=limit)
    return {"data": data}
