# 文件：app/agents/state.py
"""Agent 状态定义 — 共享黑板 + 对话阶段枚举"""
from enum import Enum
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ==========================================
# 对话阶段枚举（六大精确状态）
# ==========================================
class DialogueStage(str, Enum):
    INTRODUCTION = "INTRODUCTION"                        # 介绍/破冰：探寻需求与产品导入
    OBJECTION = "OBJECTION"                              # 异议处理：核心冲突区
    DECISION_SIGN = "DECISION_SIGN"                      # 极速签单：标体承保，当场缴费
    DECISION_PENDING = "DECISION_PENDING"                # 同意核保：客户愿意提交资料/体检
    DECISION_FOLLOW_UP = "DECISION_FOLLOW_UP"            # 需跟进：要和家人商量/下次再说
    DECISION_REJECT = "DECISION_REJECT"                  # 明确拒绝：彻底流失
    DECISION_ABANDON = "DECISION_ABANDON"                # 放弃投保：因健康/资格等客观原因无法投保


# ==========================================
# 共享黑板（AgentState）
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_stage: str          # DialogueStage 的值
    turn_count: int             # 回合计数器（每次销售发言 +1）
    persona_id: str             # 绑定的客户画像 ID
    tool_calls_log: list[str]   # 工具调用日志（供前端展示）
    force_objection: bool       # 是否被强制拉回异议阶段
    stage_reasoning: str        # 状态判定理由（透传到前端）
    decision_strike: int        # 连续判定为决策状态的次数（需达3次才算真结束）
    pending_shutdown: bool      # 标记是否进入最后一轮告别，此时跳过状态判定
    detected_stage_raw: str     # DM 原始判定阶段（被防线覆盖前），供前端展示实际检测结果
