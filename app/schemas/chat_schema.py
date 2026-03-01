# 文件：app/schemas/chat_schema.py
"""聊天相关的 Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


# ==========================================
# 请求模型
# ==========================================
class CreateSessionRequest(BaseModel):
    persona_id: str = Field(
        default="hard_boss",
        description="客户画像ID，可选: hard_boss, tech_savvy, young_mother"
    )


class ChatSendRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., min_length=1, description="销售人员的消息")


# ==========================================
# 响应模型
# ==========================================
class CreateSessionResponse(BaseModel):
    session_id: str
    persona_id: str
    persona_name: str
    persona_description: str
    difficulty: str


class ChatSendResponse(BaseModel):
    customer_reply: str = Field(description="客户AI的回复")
    current_stage: str = Field(description="当前对话阶段")
    stage_label: str = Field(description="阶段中文标签")
    turn_count: int = Field(description="当前回合数")
    tool_calls_log: list[str] = Field(default_factory=list, description="本轮工具调用日志")
    is_finished: bool = Field(default=False, description="对话是否已结束（进入决策状态）")


class MessageItem(BaseModel):
    role: str = Field(description="发送者角色: sales / customer / system")
    content: str
    turn: Optional[int] = None


class SessionHistoryResponse(BaseModel):
    session_id: str
    persona_id: str
    total_turns: int
    current_stage: str
    messages: list[MessageItem]


class EvaluationItem(BaseModel):
    turn: int
    professionalism_score: int
    compliance_score: int
    strategy_score: int
    professionalism_comment: str
    compliance_comment: str
    strategy_comment: str
    overall_advice: str


class SessionEvaluationResponse(BaseModel):
    session_id: str
    evaluations: list[EvaluationItem]
    average_scores: Optional[dict] = None
