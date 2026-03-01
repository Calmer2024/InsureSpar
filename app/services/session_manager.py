# 文件：app/services/session_manager.py
"""纯内存会话管理器 — 替代 MySQL，管理所有对话会话的生命周期"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionData:
    """单个会话的数据结构"""
    session_id: str
    persona_id: str
    created_at: datetime
    turn_count: int = 0
    current_stage: str = "INTRODUCTION"
    is_finished: bool = False
    evaluations: list = field(default_factory=list)  # EvaluationItem 字典列表


class SessionManager:
    """
    纯内存会话管理器。
    - 每个 session 对应一个独立的 LangGraph thread_id (即 session_id)
    - 评分结果暂存于此，后续可平滑迁移到数据库
    """

    def __init__(self):
        self._sessions: dict[str, SessionData] = {}

    def create_session(self, persona_id: str) -> SessionData:
        """创建一个新的对话会话"""
        session_id = str(uuid.uuid4())[:8]  # 短ID，方便调试
        session = SessionData(
            session_id=session_id,
            persona_id=persona_id,
            created_at=datetime.now()
        )
        self._sessions[session_id] = session
        print(f"📋 [会话管理] 新建会话: {session_id} (画像: {persona_id})")
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取指定会话"""
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, turn_count: int, current_stage: str, is_finished: bool = False):
        """更新会话状态"""
        session = self._sessions.get(session_id)
        if session:
            session.turn_count = turn_count
            session.current_stage = current_stage
            session.is_finished = is_finished

    def add_evaluation(self, session_id: str, evaluation: dict):
        """添加一轮评分结果"""
        session = self._sessions.get(session_id)
        if session:
            session.evaluations.append(evaluation)
            print(f"✅ [评分入库] 会话 {session_id} 第 {evaluation.get('turn', '?')} 轮评分已保存")

    def list_sessions(self) -> list[SessionData]:
        """列出所有会话"""
        return list(self._sessions.values())


# 全局单例
session_manager = SessionManager()
