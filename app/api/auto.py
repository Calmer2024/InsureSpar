# 文件：app/api/auto.py
"""Auto-Agent 路由 — 销售AI自动对战模式"""
import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.core.config import PERSONAS, SALES_STRATEGIES, DECISION_STRIKES_REQUIRED
from app.services.session_manager import session_manager
from app.agents.sales_agent import sales_agent_step
from app.agents.customer_graph import customer_graph
from app.agents.evaluator import evaluate_turn, generate_final_report
from app.agents.state import DialogueStage

router = APIRouter(prefix="/api/auto", tags=["全自动对战 (Auto)"])

STAGE_LABELS = {
    DialogueStage.INTRODUCTION:       "💬 破冰与探寻",
    DialogueStage.OBJECTION:          "⚡ 异议处理",
    DialogueStage.DECISION_SIGN:      "✅ 签单成功",
    DialogueStage.DECISION_PENDING:   "📋 同意核保",
    DialogueStage.DECISION_FOLLOW_UP: "📞 需要跟进",
    DialogueStage.DECISION_REJECT:    "❌ 客户拒绝",
}

# 所有决策阶段（进入后对话结束）
DECISION_STAGES = {
    DialogueStage.DECISION_SIGN,
    DialogueStage.DECISION_PENDING,
    DialogueStage.DECISION_FOLLOW_UP,
    DialogueStage.DECISION_REJECT,
}


# ==========================================
# Schema
# ==========================================
class CreateAutoSessionRequest(BaseModel):
    persona_id: str
    strategy_id: str = "consultant"


class AutoStepRequest(BaseModel):
    session_id: str


# ==========================================
# 1. 列出销售策略
# ==========================================
@router.get("/strategies", summary="列出自动对战支持的销售策略")
async def list_strategies():
    """
    **功能**: 获取系统可用的“AI销售策略”列表（仅在Auto模式使用）。
    **说明**: 不同策略决定了 AI 销售在应对异议和逼单时的强硬程度及切入点。
    """
    return [
        {
            "strategy_id": s["strategy_id"],
            "name": s["name"],
            "description": s["description"],
            "difficulty": s["difficulty"],
            "strengths": s["strengths"],
            "weaknesses": s["weaknesses"],
        }
        for s in SALES_STRATEGIES.values()
    ]


# ==========================================
# 2. 创建自动对战会话
# ==========================================
@router.post("/session/create", summary="创建自动对战会话")
async def create_auto_session(request: CreateAutoSessionRequest):
    """
    **功能**: 创建一个由 AI销售 和 AI客户 全程自动演绎的对练会话。
    **流程**:
    1. 校验客户画像 (`persona_id`) 和 销售策略 (`strategy_id`)。
    2. 绑定策略到对话会话，生成 ID 并返回。
    """
    persona = PERSONAS.get(request.persona_id)
    if not persona:
        raise HTTPException(400, f"画像 '{request.persona_id}' 不存在")

    strategy = SALES_STRATEGIES.get(request.strategy_id)
    if not strategy:
        raise HTTPException(400, f"销售策略 '{request.strategy_id}' 不存在")

    session = session_manager.create_session(
        persona_id=request.persona_id,
        strategy_id=request.strategy_id,
    )

    return {
        "session_id": session.session_id,
        "persona_id": persona["persona_id"],
        "persona_name": persona["name"],
        "persona_description": persona["description"],
        "strategy_id": strategy["strategy_id"],
        "strategy_name": strategy["name"],
        "strategy_description": strategy["description"],
        "mode": "auto",
    }


# ==========================================
# 3. 推进一步（SSE 流式）
# ==========================================
@router.post("/step", summary="执行自动对战触发器 (SSE)")
async def auto_step(request: AutoStepRequest):
    """
    **功能**: 触发并直播一轮全自动的对话演绎过程。
    
    **流程**: 
    1. **销售Agent**: 依据当前对战策略和对话历史生成推销话术 (包含内部思考和工具查询)。
    2. **客户Agent**: 从节点接入，回复或反驳。
    3. **对话管理器 (DM)**: 分析最终的一来一回，判定阶段变化。
    
    **返回 (Server-Sent Events 格式)**:
    - 销售、客户打字机令牌
    - DM判断状态流事件
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(404, f"会话 '{request.session_id}' 不存在")
    if session.is_finished:
        raise HTTPException(400, "此会话已结束，请创建新会话")
    if not session.strategy_id:
        raise HTTPException(400, "此会话不是 Auto-Agent 模式")

    async def event_generator():
        turn_count = session.turn_count
        current_stage = session.current_stage
        customer_reply = ""
        sales_message = ""
        sales_tool_calls_log = []  # 收集销售的工具调用

        # ========================================
        # 阶段1：销售 Agent 发言（含工具调用）
        # ========================================
        yield _sse({"type": "phase", "content": "🤖 销售Agent正在行动..."})

        async for event in sales_agent_step(
            session_id=session.session_id,
            strategy_id=session.strategy_id,
            persona_id=session.persona_id,
            current_stage=current_stage,
            turn_count=turn_count,
            conversation_history=session.conversation_history,
        ):
            yield _sse(event)
            # 收集销售的工具调用日志
            if event["type"] == "sales_tool_call":
                sales_tool_calls_log.append({
                    "tool": event.get("tool", ""),
                    "args": event.get("args", ""),
                    "result": "",  # 结果在下一个事件中
                })
            elif event["type"] == "sales_tool_result" and sales_tool_calls_log:
                sales_tool_calls_log[-1]["result"] = event.get("content", "")
            elif event["type"] == "sales_message_done":
                sales_message = event["content"]

        if not sales_message:
            yield _sse({"type": "error", "content": "销售Agent未能生成有效发言"})
            return

        # 记录销售发言
        session_manager.add_conversation_turn(session.session_id, "sales", sales_message)

        # ========================================
        # 阶段2：客户 Agent 响应（LangGraph，含流式token）
        # ========================================
        yield _sse({"type": "phase", "content": "👤 客户正在回应..."})

        initial_state = {
            "messages": [HumanMessage(content=sales_message)],
            "current_stage": current_stage,
            "turn_count": turn_count,
            "persona_id": session.persona_id,
            "tool_calls_log": [],
            "force_objection": False,
            "stage_reasoning": "",
            "decision_strike": session.decision_strike,
        }
        config = {"configurable": {"thread_id": session.session_id}}
        customer_done = False  # 客户是否已完成回复

        try:
            async for event in customer_graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                kind = event.get("event", "")
                name = event.get("name", "")
                data = event.get("data", {})
                metadata = event.get("metadata", {})
                langgraph_node = metadata.get("langgraph_node", "")

                if kind == "on_chain_start" and name == "dialogue_manager":
                    yield _sse({"type": "customer_status", "content": "🚦 状态分析中..."})

                elif kind == "on_chain_end" and name == "dialogue_manager":
                    dm_finished = True
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        turn_count = output.get("turn_count", turn_count)
                        current_stage = output.get("current_stage", current_stage)
                        reasoning = output.get("stage_reasoning", "")
                        session.decision_strike = output.get("decision_strike", session.decision_strike)
                        label = STAGE_LABELS.get(current_stage, current_stage)
                        yield _sse({
                            "type": "stage_update",
                            "stage": current_stage,
                            "stage_label": label,
                            "turn_count": turn_count,
                            "reasoning": reasoning,
                        })
                        if output.get("force_objection"):
                            yield _sse({
                                "type": "force_guard",
                                "content": f"🛡️ 强制≥5轮防线触发！第{turn_count}轮强制拖回异议。",
                            })

                elif kind == "on_chain_end" and name == "tools":
                    output = data.get("output", {})
                    messages = output.get("messages", []) if isinstance(output, dict) else []
                    for msg in messages:
                        if hasattr(msg, "content") and hasattr(msg, "name"):
                            yield _sse({
                                "type": "customer_tool_result",
                                "tool": getattr(msg, "name", ""),
                                "content": (msg.content if isinstance(msg.content, str) else str(msg.content))[:400],
                            })

                elif kind == "on_chain_end" and name == "customer":
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        turn_count = output.get("turn_count", turn_count)
                        for msg in output.get("messages", []):
                            if hasattr(msg, "content") and msg.content and getattr(msg, "type", "") == "ai":
                                if not customer_reply:
                                    customer_reply = msg.content
                                    yield _sse({"type": "customer_token", "content": msg.content})
                        customer_done = True

                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    is_customer = langgraph_node == "customer" and not customer_done
                    if chunk and hasattr(chunk, "content") and chunk.content and is_customer:
                        customer_reply += chunk.content
                        yield _sse({"type": "customer_token", "content": chunk.content})

        except Exception as e:
            yield _sse({"type": "error", "content": f"客户Agent错误: {str(e)}"})
            return

        # 记录客户回复
        if customer_reply:
            session_manager.add_conversation_turn(session.session_id, "customer", customer_reply)

        # 更新会话状态 (连续 N 轮才算结束)
        is_finished = (current_stage in DECISION_STAGES) and (session.decision_strike >= DECISION_STRIKES_REQUIRED)
        session_manager.update_session(
            session.session_id,
            turn_count=turn_count,
            current_stage=current_stage,
            is_finished=is_finished,
            decision_strike=session.decision_strike,
        )

        # 推送本轮完成事件
        yield _sse({
            "type": "step_done",
            "sales_message": sales_message,
            "customer_reply": customer_reply,
            "current_stage": current_stage,
            "stage_label": STAGE_LABELS.get(current_stage, current_stage),
            "turn_count": turn_count,
            "is_finished": is_finished,
        })

        # 获取上一轮评分用于连贯性参考
        prev_scores = None
        if session.evaluations:
            valid_evals = [e for e in session.evaluations if e.get("professionalism_score", -1) >= 0]
            if valid_evals:
                prev_scores = valid_evals[-1]

        # 后台考官评分（传入销售工具日志 + 上轮评分）
        asyncio.create_task(evaluate_turn(
            session_id=session.session_id,
            turn_count=turn_count,
            sales_msg=sales_message,
            customer_reply=customer_reply,
            persona_id=session.persona_id,
            sales_tool_calls=sales_tool_calls_log if sales_tool_calls_log else None,
            prev_scores=prev_scores,
        ))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ==========================================
# 4. 查询自动对战状态
# ==========================================
@router.get("/session/{session_id}/status")
async def get_auto_status(session_id: str):
    """查询 Auto-Agent 会话当前状态"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, f"会话 '{session_id}' 不存在")

    evaluations = [e for e in session.evaluations if e.get("professionalism_score", -1) >= 0]
    avg = None
    if evaluations:
        avg_p = sum(e["professionalism_score"] for e in evaluations) / len(evaluations)
        avg_c = sum(e["compliance_score"] for e in evaluations) / len(evaluations)
        avg_s = sum(e["strategy_score"] for e in evaluations) / len(evaluations)
        avg = {
            "avg_professionalism": round(avg_p, 1),
            "avg_compliance": round(avg_c, 1),
            "avg_strategy": round(avg_s, 1),
            "avg_total": round((avg_p + avg_c + avg_s) / 3, 1),
        }

    return {
        "session_id": session_id,
        "persona_id": session.persona_id,
        "strategy_id": session.strategy_id,
        "turn_count": session.turn_count,
        "current_stage": session.current_stage,
        "stage_label": STAGE_LABELS.get(session.current_stage, session.current_stage),
        "is_finished": session.is_finished,
        "conversation_count": len(session.conversation_history),
        "evaluation_count": len(evaluations),
        "average_scores": avg,
        "conversation_history": session.conversation_history,
        "evaluations": evaluations,
    }


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


# ==========================================
# 工具函数
# ==========================================
def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
