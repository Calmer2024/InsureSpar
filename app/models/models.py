# 文件：app/models/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base

class SessionRecord(Base):
    __tablename__ = "sessions"
    
    session_id = Column(String(36), primary_key=True, index=True)
    persona_id = Column(String(50))
    strategy_id = Column(String(50))
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    final_stage = Column(String(50))
    turn_count = Column(Integer, default=0)
    is_finished = Column(Boolean, default=False)
    
    # 关系
    logs = relationship("ConversationLog", back_populates="session", cascade="all, delete-orphan", order_by="ConversationLog.id")
    evaluations = relationship("EvaluationRecord", back_populates="session", cascade="all, delete-orphan", order_by="EvaluationRecord.turn")
    report = relationship("FinalReportRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")


class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True)
    turn = Column(Integer)
    role = Column(String(20)) # 'sales', 'customer', 'system'
    content = Column(Text)
    stage = Column(String(50), nullable=True) # 当时所处的阶段
    created_at = Column(DateTime, default=func.now())
    
    session = relationship("SessionRecord", back_populates="logs")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True)
    turn = Column(Integer)
    
    professionalism_score = Column(Integer)
    compliance_score = Column(Integer)
    strategy_score = Column(Integer)
    
    professionalism_comment = Column(Text)
    compliance_comment = Column(Text)
    strategy_comment = Column(Text)
    
    overall_advice = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    session = relationship("SessionRecord", back_populates="evaluations")


class FinalReportRecord(Base):
    __tablename__ = "final_reports"
    
    session_id = Column(String(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), primary_key=True)
    avg_total = Column(Float)
    avg_professionalism = Column(Float)
    avg_compliance = Column(Float)
    avg_strategy = Column(Float)
    
    radar_data = Column(JSON) # 存储 6个维度的评分和标签映射
    review_content = Column(Text) # LLM 生成的总监综合点评
    
    created_at = Column(DateTime, default=func.now())
    
    session = relationship("SessionRecord", back_populates="report")
