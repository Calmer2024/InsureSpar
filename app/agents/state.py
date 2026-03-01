# 文件：app/agents/state.py
"""Agent 状态定义 — 共享黑板 + 对话阶段枚举"""
from enum import Enum
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ==========================================
# 对话阶段枚举（四大精确状态）
# ==========================================
class DialogueStage(str, Enum):
    INTRODUCTION = "INTRODUCTION"          # 介绍/破冰：探寻需求与产品导入
    OBJECTION = "OBJECTION"                # 异议处理：核心冲突区，客户挑剔条款与价格
    DECISION_SIGN = "DECISION_SIGN"        # 决策-签单：成功转化
    DECISION_REJECT = "DECISION_REJECT"    # 决策-拒绝：彻底流失


# ==========================================
# 共享黑板（AgentState）
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_stage: str          # DialogueStage 的值
    turn_count: int             # 回合计数器（每次销售发言 +1）
    persona_id: str             # 绑定的客户画像 ID
    tool_calls_log: list[str]   # 工具调用日志（供前端展示）
    force_objection: bool       # 是否被强制拉回异议阶段（≥5轮防线触发标记）
