# 文件：app/api/history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import get_db
from app.models.models import SessionRecord, ConversationLog, EvaluationRecord, FinalReportRecord
import json

router = APIRouter(prefix="/api/history", tags=["历史记录与查询"])

@router.get("/sessions")
def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """获取所有历史会话列表（支持分页）"""
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

@router.get("/sessions/{session_id}")
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """获取指定会话的完整历史（含对话记录、各轮评分和终极报告）"""
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
