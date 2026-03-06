# 文件：app/api/dashboard.py
"""用户看板 (Dashboard) API 路由 — 提供个人能力和成长趋势数据"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.database import get_db
from app.models.models import SessionRecord, FinalReportRecord

router = APIRouter(prefix="/api/user/dashboard", tags=["个人看板 (Dashboard)"])

@router.get("/overview", summary="获取看板总览数据")
async def get_overview(db: Session = Depends(get_db)):
    """
    获个人信息与核心指标
    - total_sessions: 总对练次数
    - total_duration_minutes: 总对练时长 (已完成的会话)
    - deal_closed_count: 成功签单次数
    - avg_score_all_time: 历史平均综合得分
    """
    # 计算总场次
    total_sessions = db.query(SessionRecord).count()
    
    # 计算总时长
    # PostgreSQL / MySQL 的直接 sum 时间差比较麻烦，直接用 python 取出计算对于小项目更稳妥，或者利用 SQLite
    # 考虑到通用性，先查所有的 session_start_time, end_time 然后汇总
    finished_sessions = db.query(SessionRecord).filter(SessionRecord.is_finished == True).all()
    total_minutes = 0
    deal_closed = 0
    for s in finished_sessions:
        if s.start_time and s.end_time:
            delta = s.end_time - s.start_time
            total_minutes += int(delta.total_seconds() / 60)
        # 简单判断签单，看 final_stage
        if s.final_stage and "DECISION_SIGN" in s.final_stage:
            deal_closed += 1
            
    # 计算均分
    avg_score = db.query(func.avg(FinalReportRecord.avg_total)).scalar()
    
    return {
        "user_info": {
            "name": "张明远", 
            "rank": "高级财富管家", 
            "avatar_url": "https://api.dicebear.com/7.x/notionists/svg?seed=user&backgroundColor=f3f4f6", 
            "join_date": "2024-01-15"
        },
        "stats": {
            "total_sessions": total_sessions,
            "total_duration_minutes": total_minutes,
            "deal_closed_count": deal_closed,
            "avg_score_all_time": int(avg_score) if avg_score else 0
        }
    }


@router.get("/capabilities", summary="获取能力雷达与弱点分析")
async def get_capabilities(db: Session = Depends(get_db)):
    """
    聚合所有历史结果，提供雷达图分数
    """
    reports = db.query(FinalReportRecord).all()
    if not reports:
        # 如果没有报告，返回全图 0 分和缺省内容
        return {
            "radar": {
                "labels": ["破冰重建", "需求挖掘", "方案制作", "条款讲解", "异议处理", "促成交易"],
                "scores": [0, 0, 0, 0, 0, 0]
            },
            "weaknesses": [
                {"dimension": "暂无数据", "frequency": 0, "advice": "请先完成至少一次完整的对练以生成诊断数据。"}
            ],
            "ai_general_review": "目前系统暂无您的对练记录，快去开启您的第一次实战模拟吧！"
        }

    # 聚合六维分数
    dim_sums = {}
    dim_counts = {}
    
    for r in reports:
        if r.radar_data and "labels" in r.radar_data and "scores" in r.radar_data:
            for label, score in zip(r.radar_data["labels"], r.radar_data["scores"]):
                dim_sums[label] = dim_sums.get(label, 0) + score
                dim_counts[label] = dim_counts.get(label, 0) + 1
                
    radar_labels = []
    radar_scores = []
    # 如果有的报告没有具体六维字段，我们确保默认返回结构不崩
    default_labels = ["破冰重建", "需求挖掘", "方案制作", "条款讲解", "异议处理", "促成交易"]
    
    # 若有真实汇总
    if dim_sums:
        avg_dims = {k: int(dim_sums[k]/dim_counts[k]) for k in dim_sums.keys()}
        radar_labels = list(avg_dims.keys())
        radar_scores = list(avg_dims.values())
        
        # 找最弱的三项
        sorted_dims = sorted(avg_dims.items(), key=lambda x: x[1])
        weaknesses = []
        for d in sorted_dims[:3]:
            weaknesses.append({
                "dimension": d[0],
                "frequency": 1, # 目前频率以1简单代替。
                "advice": f"您在【{d[0]}】环节得分偏低，平均分为 {d[1]}，建议多复习相关话术或查阅工具箱条款。"
            })
    else:
        # 兼容旧数据
        radar_labels = default_labels
        radar_scores = [int(db.query(func.avg(FinalReportRecord.avg_professionalism)).scalar() or 0)] * 2 + \
                       [int(db.query(func.avg(FinalReportRecord.avg_compliance)).scalar() or 0)] * 2 + \
                       [int(db.query(func.avg(FinalReportRecord.avg_strategy)).scalar() or 0)] * 2
        weaknesses = [
            {"dimension": "合规性缺陷", "frequency": 1, "advice": "销售过程的合规性存在待提升空间，请避免夸大收益。"}
        ]
        
    ai_review = "根据您的历史对练数据来看，您在专业与态度上表现良好，能够较好地应对一般客户异议。建议针对您的薄弱环节（得分低于60分的部分）多加练习并借助 AI 工具箱查漏补缺。继续加油！"
    
    return {
        "radar": {"labels": radar_labels, "scores": radar_scores},
        "weaknesses": weaknesses,
        "ai_general_review": ai_review
    }


@router.get("/growth-trend", summary="获取成长趋势")
async def get_growth_trend(period: str = 'last_10_sessions', db: Session = Depends(get_db)):
    """
    提供最近对练记录的成绩曲线
    """
    # 取最近10条 report (关联 session按时间排序)
    # 因为 FinalReport 是与 Session 1:1, 需要 join 判断时间
    recent_reports = db.query(FinalReportRecord, SessionRecord).join(
        SessionRecord, SessionRecord.session_id == FinalReportRecord.session_id
    ).order_by(SessionRecord.start_time.desc()).limit(10).all()
    
    # 由于查询是降序（最近在前），图表 x 轴通常是升序（早的在前），需要反转
    recent_reports.reverse()
    
    if not recent_reports:
        return {
            "x_axis": ["无数据"],
            "series": {
                "total": [0],
                "professionalism": [0],
                "compliance": [0],
                "strategy": [0]
            }
        }
    
    x_axis = []
    series = {
        "total": [],
        "professionalism": [],
        "compliance": [],
        "strategy": []
    }
    
    for idx, (r, s) in enumerate(recent_reports, 1):
        x_axis.append(str(idx))
        
        series["total"].append(int(r.avg_total) if r.avg_total else 0)
        series["professionalism"].append(int(r.avg_professionalism) if r.avg_professionalism else 0)
        series["compliance"].append(int(r.avg_compliance) if r.avg_compliance else 0)
        series["strategy"].append(int(r.avg_strategy) if r.avg_strategy else 0)
        
    return {
        "x_axis": x_axis,
        "series": series
    }
