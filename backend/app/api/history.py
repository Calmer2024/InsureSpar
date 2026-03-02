# 文件：app/api/history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import get_db
from app.models.models import SessionRecord, ConversationLog, EvaluationRecord, FinalReportRecord
import json

router = APIRouter(prefix="/api/history", tags=["历史记录与查询"])

@router.get("/sessions", summary="获取历史会话列表（支持分页）")
def list_sessions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, le=100, description="限制返回数量（最多100）"),
    db: Session = Depends(get_db)
):
    """
    **功能**: 查询所有的对话会话历史列表 (包括手动模式及 Auto 模式)。
    **排序**: 按照会话开始时间 `start_time` 倒序排列。
    """
    sessions = db.query(SessionRecord).order_by(desc(SessionRecord.start_time)).offset(skip).limit(limit).all()
    # 返回简要信息
    return [
        {
            "session_id": s.session_id,
            "persona_id": s.persona_id,
            "strategy_id": s.strategy_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "final_stage": s.final_stage,
            "turn_count": s.turn_count,
            "is_finished": s.is_finished,
        }
        for s in sessions
    ]

@router.get("/sessions/{session_id}", summary="获取会话所有明细（对话、评分、报告）")
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """
    **功能**: 获取指定一次会话的超级全量数据。
    
    **返回结构内容包括**:
    1. **`session_info`**: 会话的基础信息（结局、时长等）。
    2. **`conversation_logs`**: 按顺序排好的每一轮对话记录。
    3. **`evaluations`**: AI 考官给出的每一轮 3维度具体打分与教练短评。
    4. **`final_report`**: 对话结束后 AI 总监产出的综合点评和 6维度雷达评分 (如果会话尚未结束且未触发生成报告，则此字段为空)。
    """
    session = db.query(SessionRecord).filter(SessionRecord.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    logs = db.query(ConversationLog).filter(ConversationLog.session_id == session_id).order_by(ConversationLog.id).all()
    evals = db.query(EvaluationRecord).filter(EvaluationRecord.session_id == session_id).order_by(EvaluationRecord.turn).all()
    report = db.query(FinalReportRecord).filter(FinalReportRecord.session_id == session_id).first()
    
    return {
        "session_info": {
            "session_id": session.session_id,
            "persona_id": session.persona_id,
            "strategy_id": session.strategy_id,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "final_stage": session.final_stage,
            "turn_count": session.turn_count,
            "is_finished": session.is_finished,
        },
        "conversation_logs": [
            {
                "id": log.id,
                "turn": log.turn,
                "role": log.role,
                "content": log.content,
                "stage": log.stage,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ],
        "evaluations": [
            {
                "id": ev.id,
                "turn": ev.turn,
                "scores": {
                    "professionalism": ev.professionalism_score,
                    "compliance": ev.compliance_score,
                    "strategy": ev.strategy_score,
                },
                "comments": {
                    "professionalism": ev.professionalism_comment,
                    "compliance": ev.compliance_comment,
                    "strategy": ev.strategy_comment,
                },
                "overall_advice": ev.overall_advice,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in evals
        ],
        "final_report": {
            "avg_scores": {
                "total": report.avg_total,
                "professionalism": report.avg_professionalism,
                "compliance": report.avg_compliance,
                "strategy": report.avg_strategy,
            },
            "radar_data": report.radar_data,
            "review_content": report.review_content,
            "created_at": report.created_at.isoformat() if report.created_at else None,
        } if report else None
    }
