# 文件：app/api/chat.py
"""聊天 API 路由 — 会话管理 + 对话交互 + 评分查询 + SSE流式输出"""
import json
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
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


# ==========================================
# 6. SSE 流式聊天接口
# ==========================================
STAGE_LABELS = {
    DialogueStage.INTRODUCTION: "💬 破冰与探寻",
    DialogueStage.OBJECTION: "⚡ 异议处理",
    DialogueStage.DECISION_SIGN: "✅ 签单成功",
    DialogueStage.DECISION_REJECT: "❌ 客户拒绝",
}


@router.post("/chat/stream")
async def stream_chat(request: ChatSendRequest):
    """SSE 流式对话：实时推送对话管理、客户回复(逐token)、工具调用等内部事件"""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{request.session_id}' 不存在")
    if session.is_finished:
        raise HTTPException(status_code=400, detail="此会话已结束，请创建新会话")

    async def event_generator():
        """SSE 事件生成器"""
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "current_stage": session.current_stage,
            "turn_count": session.turn_count,
            "persona_id": session.persona_id,
            "tool_calls_log": [],
            "force_objection": False,
        }
        config = {"configurable": {"thread_id": session.session_id}}

        customer_reply = ""
        current_stage = session.current_stage
        turn_count = session.turn_count
        tool_logs = []
        force_triggered = False
        dm_finished = False  # 对话管理器是否已结束

        try:
            async for event in customer_graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                kind = event.get("event", "")
                name = event.get("name", "")
                data = event.get("data", {})
                tags = event.get("tags", [])
                metadata = event.get("metadata", {})
                langgraph_node = metadata.get("langgraph_node", "")

                # === 节点开始 ===
                if kind == "on_chain_start" and name == "dialogue_manager":
                    yield _sse({"type": "status", "content": "🚦 对话管理器正在分析状态..."})

                elif kind == "on_chain_start" and name == "customer":
                    yield _sse({"type": "status", "content": "👤 客户正在思考..."})

                elif kind == "on_chain_start" and name == "tools":
                    yield _sse({"type": "status", "content": "🔧 正在调用工具..."})

                # === 节点结束 → 获取状态更新 ===
                elif kind == "on_chain_end" and name == "dialogue_manager":
                    dm_finished = True
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        turn_count = output.get("turn_count", turn_count)
                        current_stage = output.get("current_stage", current_stage)
                        force_triggered = output.get("force_objection", False)
                        label = STAGE_LABELS.get(current_stage, current_stage)
                        yield _sse({
                            "type": "stage_update",
                            "stage": current_stage,
                            "stage_label": label,
                            "turn_count": turn_count,
                        })
                        if force_triggered:
                            yield _sse({
                                "type": "force_guard",
                                "content": f"🛡️ 强制≥5轮防线触发！第{turn_count}轮不允许进入决策，强制拖回异议处理。"
                            })

                # === 工具执行结果 ===
                elif kind == "on_chain_end" and name == "tools":
                    output = data.get("output", {})
                    messages = output.get("messages", []) if isinstance(output, dict) else []
                    for msg in messages:
                        if hasattr(msg, "content") and hasattr(msg, "name"):
                            tool_name = getattr(msg, "name", "unknown")
                            tool_content = msg.content if isinstance(msg.content, str) else str(msg.content)
                            tool_logs.append({"tool": tool_name, "result": tool_content[:300]})
                            yield _sse({
                                "type": "tool_result",
                                "tool": tool_name,
                                "content": tool_content[:500],
                            })

                # === 客户节点结束 → 提取完整回复（作为最终回退）===
                elif kind == "on_chain_end" and name == "customer":
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        msgs = output.get("messages", [])
                        for msg in msgs:
                            if hasattr(msg, "content") and msg.content and hasattr(msg, "type") and msg.type == "ai":
                                if not customer_reply:
                                    # token流没捕获到，用完整回复作为回退
                                    customer_reply = msg.content
                                    yield _sse({"type": "token", "content": msg.content})

                # === 客户 LLM 逐 Token 流式输出 ===
                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    # 使用 langgraph_node 判断来源（最可靠），或用 dm_finished 状态判断
                    is_customer_node = langgraph_node == "customer" or (dm_finished and langgraph_node != "dialogue_manager")
                    if chunk and hasattr(chunk, "content") and chunk.content and is_customer_node:
                        customer_reply += chunk.content
                        yield _sse({"type": "token", "content": chunk.content})
                    # 捕获工具调用请求
                    if chunk and hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks and is_customer_node:
                        for tc in chunk.tool_call_chunks:
                            if tc.get("name"):
                                tool_logs.append({"tool": tc["name"], "result": "调用中..."})
                                yield _sse({
                                    "type": "tool_call",
                                    "tool": tc["name"],
                                    "args": tc.get("args", ""),
                                })

        except Exception as e:
            yield _sse({"type": "error", "content": f"系统错误: {str(e)}"})

        # === 最终结果 ===
        is_finished = current_stage in [DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT]
        session_manager.update_session(
            session.session_id,
            turn_count=turn_count,
            current_stage=current_stage,
            is_finished=is_finished,
        )

        yield _sse({
            "type": "done",
            "customer_reply": customer_reply,
            "current_stage": current_stage,
            "stage_label": STAGE_LABELS.get(current_stage, current_stage),
            "turn_count": turn_count,
            "is_finished": is_finished,
            "tool_calls_log": tool_logs,
        })

        # 后台异步评分
        asyncio.create_task(evaluate_turn(
            session_id=session.session_id,
            turn_count=turn_count,
            sales_msg=request.message,
            customer_reply=customer_reply,
            persona_id=session.persona_id,
        ))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(data: dict) -> str:
    """格式化 SSE 事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ==========================================
# 7. 评分轮询（前端用来实时拉取最新评分）
# ==========================================
@router.get("/session/{session_id}/evaluation/latest")
async def get_latest_evaluation(session_id: str, turn: int = 0):
    """获取指定会话中指定轮次之后的新评分（前端轮询用）"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")

    new_evals = [
        e for e in session.evaluations
        if e.get("turn", 0) > turn and e.get("professionalism_score", -1) >= 0
    ]
    return {"session_id": session_id, "new_evaluations": new_evals}

