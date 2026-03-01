# 文件：app/services/session_manager.py
"""纯内存会话管理器 — 替代 MySQL，管理所有对话会话的生命周期"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from app.models.database import SessionLocal
from app.models.models import SessionRecord, ConversationLog, EvaluationRecord, FinalReportRecord


@dataclass
class SessionData:
    """单个会话的数据结构"""
    session_id: str
    persona_id: str
    created_at: datetime
    turn_count: int = 0
    current_stage: str = "INTRODUCTION"
    is_finished: bool = False
    decision_strike: int = 0                         # 连续判定为决策状态的次数
    evaluations: list = field(default_factory=list)  # EvaluationItem 字典列表
    # Auto-Agent 专用字段
    strategy_id: Optional[str] = None                # 销售策略 ID（auto 模式才有值）
    conversation_history: list = field(default_factory=list)  # [{role, content}] 纯文本历史


class SessionManager:
    """
    纯内存会话管理器。
    - 每个 session 对应一个独立的 LangGraph thread_id (即 session_id)
    - 评分结果暂存于此，后续可平滑迁移到数据库
    """

    def __init__(self):
        self._sessions: dict[str, SessionData] = {}

    def create_session(self, persona_id: str, strategy_id: str = None) -> SessionData:
        """创建一个新的对话会话（普通或Auto模式）"""
        session_id = str(uuid.uuid4())[:8]
        session = SessionData(
            session_id=session_id,
            persona_id=persona_id,
            created_at=datetime.now(),
            strategy_id=strategy_id,
        )
        self._sessions[session_id] = session
        mode = "Auto" if strategy_id else "普通"
        print(f"📋 [会话管理] 新建{mode}会话: {session_id} (画像: {persona_id}" +
              (f", 策略: {strategy_id})" if strategy_id else ")"))
        
        # 写入数据库
        db = SessionLocal()
        try:
            db_session = SessionRecord(
                session_id=session_id,
                persona_id=persona_id,
                strategy_id=strategy_id,
                start_time=session.created_at,
                final_stage="INTRODUCTION"
            )
            db.add(db_session)
            db.commit()
        except Exception as e:
            print(f"❌ [DB持久化] 创建会话失败: {e}")
        finally:
            db.close()
            
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取指定会话"""
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, turn_count: int, current_stage: str, is_finished: bool = False, decision_strike: int = 0):
        """更新会话状态"""
        session = self._sessions.get(session_id)
        if session:
            session.turn_count = turn_count
            session.current_stage = current_stage
            session.is_finished = is_finished
            session.decision_strike = decision_strike
            
            # 写入数据库
            db = SessionLocal()
            try:
                db_session = db.query(SessionRecord).filter(SessionRecord.session_id == session_id).first()
                if db_session:
                    db_session.turn_count = turn_count
                    db_session.final_stage = current_stage
                    db_session.is_finished = is_finished
                    if is_finished:
                        db_session.end_time = datetime.now()
                    db.commit()
            except Exception as e:
                print(f"❌ [DB持久化] 更新会话状态失败: {e}")
            finally:
                db.close()

    def add_conversation_turn(self, session_id: str, role: str, content: str):
        """添加一轮对话记录（Auto模式专用）"""
        session = self._sessions.get(session_id)
        if session:
            session.conversation_history.append({"role": role, "content": content})
            
            # 写入数据库
            db = SessionLocal()
            try:
                log = ConversationLog(
                    session_id=session_id,
                    turn=session.turn_count,
                    role=role,
                    content=content,
                    stage=session.current_stage
                )
                db.add(log)
                db.commit()
            except Exception as e:
                print(f"❌ [DB持久化] 保存对话记录失败: {e}")
            finally:
                db.close()

    def add_evaluation(self, session_id: str, evaluation: dict):
        """添加一轮评分结果"""
        session = self._sessions.get(session_id)
        if session:
            session.evaluations.append(evaluation)
            print(f"✅ [评分入库] 会话 {session_id} 第 {evaluation.get('turn', '?')} 轮评分已保存")
            
            # 写入数据库
            db = SessionLocal()
            try:
                ev_record = EvaluationRecord(
                    session_id=session_id,
                    turn=evaluation.get("turn", session.turn_count),
                    professionalism_score=evaluation.get("professionalism_score", 0),
                    compliance_score=evaluation.get("compliance_score", 0),
                    strategy_score=evaluation.get("strategy_score", 0),
                    professionalism_comment=evaluation.get("professionalism_comment", ""),
                    compliance_comment=evaluation.get("compliance_comment", ""),
                    strategy_comment=evaluation.get("strategy_comment", ""),
                    overall_advice=evaluation.get("overall_advice", "")
                )
                db.add(ev_record)
                db.commit()
            except Exception as e:
                print(f"❌ [DB持久化] 保存评分明细失败: {e}")
            finally:
                db.close()

    def list_sessions(self) -> list[SessionData]:
        """列出所有会话"""
        return list(self._sessions.values())

    def save_final_report(self, session_id: str, report_data: dict):
        """保存终极报告到数据库"""
        db = SessionLocal()
        try:
            # 检查是否已有报告
            existing = db.query(FinalReportRecord).filter(FinalReportRecord.session_id == session_id).first()
            scores = report_data.get("avg_scores", {})
            if not existing:
                report = FinalReportRecord(
                    session_id=session_id,
                    avg_total=scores.get("total", 0.0),
                    avg_professionalism=scores.get("professionalism", 0.0),
                    avg_compliance=scores.get("compliance", 0.0),
                    avg_strategy=scores.get("strategy", 0.0),
                    radar_data=report_data.get("radar", {}),
                    review_content=report_data.get("review", "")
                )
                db.add(report)
                db.commit()
                print(f"✅ [DB持久化] 终极报告保存成功。")
        except Exception as e:
            print(f"❌ [DB持久化] 保存终极报告失败: {e}")
        finally:
            db.close()


# 全局单例
session_manager = SessionManager()
