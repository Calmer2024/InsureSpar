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
from app.core.config import PERSONAS, DECISION_STRIKES_REQUIRED
from app.services.session_manager import session_manager
from app.agents.customer_graph import customer_graph
from app.agents.evaluator import evaluate_turn, generate_final_report
from app.agents.state import DialogueStage

router = APIRouter(prefix="/api", tags=["人机手动对练 (Manual)"])


# ==========================================
# 1. 创建对话会话
# ==========================================
@router.post("/session/create", response_model=CreateSessionResponse, summary="创建手动对练会话")
async def create_session(request: CreateSessionRequest):
    """
    **功能**: 创建一个新的手动对练会话。
    **流程**: 
    1. 根据传入的 `persona_id` 获取对应的客户画像。
    2. 生成唯一的 `session_id` 并初始化会话状态 (默认 `INTRODUCTION`)。
    """
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
@router.post("/chat/send", response_model=ChatSendResponse, summary="发送销售话术并获取回复")
async def send_message(request: ChatSendRequest, background_tasks: BackgroundTasks):
    """
    **功能**: （同步接口）销售发送一句话，AI客户思考后返回回复。
    **说明**: 
    此接口为同步等待结果，不建议在需要看到中间思考过程（如工具调用）的场景使用。
    建议前端使用 `/api/chat/stream` 接口替代。
    """
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
        "stage_reasoning": "",
        "decision_strike": session.decision_strike,
        "pending_shutdown": session.pending_shutdown,
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

    # 判断是否结束 (优雅关机逻辑)
    is_finished = False
    pending_shutdown = session.pending_shutdown

    if pending_shutdown:
        # 已完成最后告别，彻底终结
        is_finished = True
    else:
        # 本轮结束时是否达到挂起告别条件
        hit_decision = (current_stage in [
            DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT,
            DialogueStage.DECISION_PENDING, DialogueStage.DECISION_FOLLOW_UP,
        ]) and (result.get("decision_strike", 0) >= DECISION_STRIKES_REQUIRED)

        if hit_decision:
            pending_shutdown = True
            print("⚠️ [手动模式] 达成决策条件，进入 pending_shutdown 最后告别回合。")
            session_manager.add_conversation_turn(
                session.session_id, 
                "system", 
                "【系统通知：客户已做出最终决定，对话即将在本轮结束后彻底关闭。请您进行简短的礼貌告别或确认（如：好的，马上为您发送方案，祝您生活愉快），不要再引入任何新话题。】"
            )
    
    session.decision_strike = result.get("decision_strike", session.decision_strike)

    # 更新会话状态
    session_manager.update_session(
        session.session_id,
        turn_count=turn_count,
        current_stage=current_stage,
        is_finished=is_finished,
        pending_shutdown=pending_shutdown,
    )

    # 记录到会话历史以便考官使用最近上下文
    session_manager.add_conversation_turn(session.session_id, "sales", request.message)
    if customer_reply:
        session_manager.add_conversation_turn(session.session_id, "customer", customer_reply)

    # 获取上一轮评分用于连贯性参考
    prev_scores = None
    if session.evaluations:
        valid_evals = [e for e in session.evaluations if e.get("professionalism_score", -1) >= 0]
        if valid_evals:
            prev_scores = valid_evals[-1]

    # 异步后台评分（不阻塞主流程）
    background_tasks.add_task(
        evaluate_turn,
        session_id=session.session_id,
        turn_count=turn_count,
        sales_msg=request.message,
        customer_reply=customer_reply,
        persona_id=session.persona_id,
        current_stage=current_stage,
        conversation_history=session.conversation_history,
        prev_scores=prev_scores,
    )

    # 阶段中文标签映射
    stage_labels = {
        DialogueStage.INTRODUCTION:       "💬 破冰与探寻",
        DialogueStage.OBJECTION:          "⚡ 异议处理",
        DialogueStage.DECISION_SIGN:      "✅ 签单成功",
        DialogueStage.DECISION_PENDING:   "📋 同意核保",
        DialogueStage.DECISION_FOLLOW_UP: "📞 需要跟进",
        DialogueStage.DECISION_REJECT:    "❌ 客户拒绝",
    }

    return ChatSendResponse(
        customer_reply=customer_reply,
        current_stage=current_stage,
        stage_label=stage_labels.get(current_stage, current_stage),
        turn_count=turn_count,
        tool_calls_log=tool_calls_log,
        is_finished=is_finished,
        is_pending_shutdown=pending_shutdown,
    )


# ==========================================
# 3. 获取对话历史
# ==========================================
@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse, summary="查询会话对话历史")
async def get_session_history(session_id: str):
    """
    **功能**: 获取指定手动对练会话的完整对话聊天记录。
    **说明**: 返回数据包括发言角色 (sales/customer)，发言内容以及所属的轮次。
    """
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
@router.get("/session/{session_id}/evaluation", response_model=SessionEvaluationResponse, summary="查询会话评分记录")
async def get_session_evaluation(session_id: str):
    """
    **功能**: 获取指定会话由考官Agent后台“异步打分”产生的所有轮次评分结果。
    **说明**: 包含每轮的专业、合规、策略得分及教练点评，并自动计算出当前平均分。
    """
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
@router.get("/personas", summary="列出支持的客户画像")
async def list_personas():
    """
    **功能**: 返回系统内置的所有 AI 客户画像列表。
    **说明**: 获取画像的 `persona_id`，用于在 `/session/create` 中选用。
    """
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
    DialogueStage.INTRODUCTION:       "💬 破冰与探寻",
    DialogueStage.OBJECTION:          "⚡ 异议处理",
    DialogueStage.DECISION_SIGN:      "✅ 签单成功",
    DialogueStage.DECISION_PENDING:   "📋 同意核保",
    DialogueStage.DECISION_FOLLOW_UP: "📞 需要跟进",
    DialogueStage.DECISION_REJECT:    "❌ 客户拒绝",
}


@router.post("/chat/stream", summary="流式发送话术并获取实时响应 (SSE)")
async def stream_chat(request: ChatSendRequest):
    """
    **功能**: （推荐前端使用）发送一条销售消息，并以 Server-Sent Events (SSE) 格式实时获取 AI 思考过程和恢复。
    
    **返回事件类型**包括：
    - `status`: 内部节点的执行状态提示
    - `tool_call`: 客户AI正在调用查找条款工具
    - `tool_result`: 工具返回的核查结果
    - `token`: 客户回复文字的打字机流式输出
    - `stage_update`: 对话管理器对本轮状态的重新判定
    - `force_guard`: 触发防线规则的系统级警告信息
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        # 尝试从数据库恢复
        session = session_manager.restore_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话 '{request.session_id}' 不存在或无法恢复")
            
    if session.is_finished:
        raise HTTPException(status_code=400, detail="此会话已结束，无法继续对话")

    async def event_generator():
        """SSE 事件生成器"""
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "current_stage": session.current_stage,
            "turn_count": session.turn_count,
            "persona_id": session.persona_id,
            "tool_calls_log": [],
            "force_objection": False,
            "stage_reasoning": "",
            "decision_strike": session.decision_strike,
            "pending_shutdown": session.pending_shutdown,
        }
        config = {"configurable": {"thread_id": session.session_id}}

        customer_reply = ""
        current_stage = session.current_stage
        turn_count = session.turn_count
        tool_logs = []
        force_triggered = False
        dm_finished = False  # 对话管理器是否已结束（兼容旧逻辑）
        customer_done = False  # 客户是否已完成回复

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
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        current_stage = output.get("current_stage", current_stage)
                        force_triggered = output.get("force_objection", False)
                        session.decision_strike = output.get("decision_strike", session.decision_strike)
                        reasoning = output.get("stage_reasoning", "")
                        label = STAGE_LABELS.get(current_stage, current_stage)
                        yield _sse({
                            "type": "stage_update",
                            "stage": current_stage,
                            "stage_label": label,
                            "turn_count": turn_count,
                            "reasoning": reasoning,
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
                        turn_count = output.get("turn_count", turn_count)
                        msgs = output.get("messages", [])
                        for msg in msgs:
                            if hasattr(msg, "content") and msg.content and hasattr(msg, "type") and msg.type == "ai":
                                if not customer_reply:
                                    customer_reply = msg.content
                                    yield _sse({"type": "token", "content": msg.content})
                        customer_done = True

                # === 客户 LLM 逐 Token 流式输出 ===
                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    # 使用 langgraph_node 判断来源
                    is_customer_node = langgraph_node == "customer" and not customer_done
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

        # === 优雅关机 (Graceful Shutdown) 逻辑判定 ===
        is_finished = False
        pending_shutdown = session.pending_shutdown

        if pending_shutdown:
            # 已完成最后告别，彻底终结
            is_finished = True
        else:
            hit_decision = (current_stage in [
                DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT,
                DialogueStage.DECISION_PENDING, DialogueStage.DECISION_FOLLOW_UP,
            ]) and (session.decision_strike >= DECISION_STRIKES_REQUIRED)
            
            if hit_decision:
                pending_shutdown = True
                print("⚠️ [流式分析] 达成决策条件，进入 pending_shutdown 最后告别回合并塞入暗号。")
                session_manager.add_conversation_turn(
                    session.session_id, 
                    "system", 
                    "【系统通知：客户已做出最终决定，对话即将在本轮结束后彻底关闭。请向客户进行简短的礼貌告别或确认（如：好的，马上为您发送方案，祝您生活愉快），不要再引入任何新话题。】"
                )

        session_manager.update_session(
            session.session_id,
            turn_count=turn_count,
            current_stage=current_stage,
            is_finished=is_finished,
            decision_strike=session.decision_strike,
            pending_shutdown=pending_shutdown,
        )

        # 记录到会话历史以便考官使用最近上下文
        session_manager.add_conversation_turn(session.session_id, "sales", request.message)
        if customer_reply:
            session_manager.add_conversation_turn(session.session_id, "customer", customer_reply)

        yield _sse({
            "type": "done",
            "customer_reply": customer_reply,
            "current_stage": current_stage,
            "stage_label": STAGE_LABELS.get(current_stage, current_stage),
            "turn_count": turn_count,
            "is_finished": is_finished,
            "tool_calls_log": tool_logs,
            "is_pending_shutdown": pending_shutdown,
        })

        # 获取上一轮评分
        prev_scores = None
        if session.evaluations:
            valid_evals = [e for e in session.evaluations if e.get('professionalism_score', -1) >= 0]
            if valid_evals:
                prev_scores = valid_evals[-1]

        # 后台异步评分（传入上轮评分与最近对话上下文）
        asyncio.create_task(evaluate_turn(
            session_id=session.session_id,
            turn_count=turn_count,
            sales_msg=request.message,
            customer_reply=customer_reply,
            persona_id=session.persona_id,
            current_stage=current_stage,
            conversation_history=session.conversation_history,
            prev_scores=prev_scores,
        ))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ==========================================
# 终极评估报告
# ==========================================
@router.get("/session/{session_id}/final-report", summary="生成并获取终极能力评估报告")
async def get_final_report(session_id: str):
    """
    **功能**: 当对话结束（成交/明确拒绝/待跟进）后，总结一整局的能力表现并生成报告。

    **处理逻辑**:
    1. 读取当前会话每一轮的考官打分日志。
    2. 将整局对话合并提炼，发送给大模型（AI 总监）。
    3. 产出两项核心内容：
       - `review`: 500字左右的总监综合点评。
       - `radar`: 6个维度（沟通、产品熟悉度、合规、异议处理、需求挖掘、促成）的具体评分(1-10分)。
    4. **持久化**: 同时将最终报告异步存入 `final_reports` 表。
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")

    report = await generate_final_report(
        session_id=session_id,
        persona_id=session.persona_id,
        conversation_history=session.conversation_history,
        evaluations=session.evaluations,
        final_stage=session.current_stage,
        turn_count=session.turn_count,
        strategy_id=session.strategy_id,
    )

    # 持久化到数据库
    if "error" not in report:
        session_manager.save_final_report(session_id, report)

    return report

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

