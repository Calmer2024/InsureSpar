# 文件：app/api/chat.py
"""聊天 API 路由 — 会话管理 + 对话交互 + 评分查询"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from langchain_core.messages import HumanMessage

from app.schemas.chat_schema import (
    CreateSessionRequest, CreateSessionResponse,
    ChatSendRequest, ChatSendResponse,
    SessionHistoryResponse, MessageItem,
    SessionEvaluationResponse, EvaluationItem,
)
from app.core.config import PERSONAS
from app.services.session_manager import session_manager
from app.agents.customer_graph import customer_graph
from app.agents.evaluator import evaluate_turn
from app.agents.state import DialogueStage

router = APIRouter(prefix="/api", tags=["智能体对练"])


# ==========================================
# 1. 创建对话会话
# ==========================================
@router.post("/session/create", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """创建一个新的对练会话，选择客户画像"""
    persona = PERSONAS.get(request.persona_id)
    if not persona:
        available = list(PERSONAS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"画像 '{request.persona_id}' 不存在。可选画像: {available}"
        )

    session = session_manager.create_session(request.persona_id)

    return CreateSessionResponse(
        session_id=session.session_id,
        persona_id=persona["persona_id"],
        persona_name=persona["name"],
        persona_description=persona["description"],
        difficulty=persona["difficulty"],
    )


# ==========================================
# 2. 发送销售消息
# ==========================================
@router.post("/chat/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest, background_tasks: BackgroundTasks):
    """发送一条销售消息，获取客户AI的回复"""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{request.session_id}' 不存在")

    if session.is_finished:
        raise HTTPException(status_code=400, detail="此会话已结束（已进入决策阶段），请创建新会话")

    # 构造初始状态
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "current_stage": session.current_stage,
        "turn_count": session.turn_count,
        "persona_id": session.persona_id,
        "tool_calls_log": [],
        "force_objection": False,
    }

    # 使用 session_id 作为 LangGraph 的 thread_id
    config = {"configurable": {"thread_id": session.session_id}}

    # 调用客户专用图
    result = customer_graph.invoke(initial_state, config=config)

    # 提取结果
    customer_reply = ""
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            customer_reply = msg.content
            break

    current_stage = result.get("current_stage", session.current_stage)
    turn_count = result.get("turn_count", session.turn_count)
    tool_calls_log = result.get("tool_calls_log", [])

    # 判断是否结束
    is_finished = current_stage in [DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT]

    # 更新会话状态
    session_manager.update_session(
        session.session_id,
        turn_count=turn_count,
        current_stage=current_stage,
        is_finished=is_finished,
    )

    # 异步后台评分（不阻塞主流程）
    background_tasks.add_task(
        evaluate_turn,
        session_id=session.session_id,
        turn_count=turn_count,
        sales_msg=request.message,
        customer_reply=customer_reply,
        persona_id=session.persona_id,
    )

    # 阶段中文标签映射
    stage_labels = {
        DialogueStage.INTRODUCTION: "💬 破冰与探寻",
        DialogueStage.OBJECTION: "⚡ 异议处理",
        DialogueStage.DECISION_SIGN: "✅ 签单成功",
        DialogueStage.DECISION_REJECT: "❌ 客户拒绝",
    }

    return ChatSendResponse(
        customer_reply=customer_reply,
        current_stage=current_stage,
        stage_label=stage_labels.get(current_stage, current_stage),
        turn_count=turn_count,
        tool_calls_log=tool_calls_log,
        is_finished=is_finished,
    )


# ==========================================
# 3. 获取对话历史
# ==========================================
@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """获取指定会话的完整对话历史"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")

    # 从 LangGraph 的 checkpoint 中读取消息历史
    config = {"configurable": {"thread_id": session_id}}
    try:
        graph_state = customer_graph.get_state(config)
        messages_raw = graph_state.values.get("messages", [])
    except Exception:
        messages_raw = []

    # 转换为前端友好格式
    messages = []
    turn = 0
    for msg in messages_raw:
        if msg.type == "human":
            turn += 1
            messages.append(MessageItem(role="sales", content=msg.content, turn=turn))
        elif msg.type == "ai" and msg.content:
            messages.append(MessageItem(role="customer", content=msg.content, turn=turn))
        elif msg.type == "tool":
            messages.append(MessageItem(role="system", content=f"[工具结果] {msg.content[:200]}...", turn=turn))

    return SessionHistoryResponse(
        session_id=session_id,
        persona_id=session.persona_id,
        total_turns=session.turn_count,
        current_stage=session.current_stage,
        messages=messages,
    )


# ==========================================
# 4. 获取评分报告
# ==========================================
@router.get("/session/{session_id}/evaluation", response_model=SessionEvaluationResponse)
async def get_session_evaluation(session_id: str):
    """获取指定会话的所有评分（后台异步打分的结果）"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")

    evaluations = [
        EvaluationItem(**e) for e in session.evaluations if e.get("professionalism_score", -1) >= 0
    ]

    # 计算平均分
    average_scores = None
    if evaluations:
        avg_p = sum(e.professionalism_score for e in evaluations) / len(evaluations)
        avg_c = sum(e.compliance_score for e in evaluations) / len(evaluations)
        avg_s = sum(e.strategy_score for e in evaluations) / len(evaluations)
        average_scores = {
            "avg_professionalism": round(avg_p, 1),
            "avg_compliance": round(avg_c, 1),
            "avg_strategy": round(avg_s, 1),
            "avg_total": round((avg_p + avg_c + avg_s) / 3, 1),
        }

    return SessionEvaluationResponse(
        session_id=session_id,
        evaluations=evaluations,
        average_scores=average_scores,
    )


# ==========================================
# 5. 辅助：列出可用画像
# ==========================================
@router.get("/personas")
async def list_personas():
    """列出所有可用的客户画像"""
    return [
        {
            "persona_id": p["persona_id"],
            "name": p["name"],
            "difficulty": p["difficulty"],
            "description": p["description"],
        }
        for p in PERSONAS.values()
    ]
