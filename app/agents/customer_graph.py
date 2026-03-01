# 文件：app/agents/customer_graph.py
"""客户专用 LangGraph 图 — 不含考官，只负责 [对话管理 → 客户思考 → 工具调用] 闭环"""
import os
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState, DialogueStage
from app.core.config import (
    LLM_MODEL, LLM_BASE_URL, LLM_API_KEY,
    MIN_TURNS_BEFORE_DECISION, PERSONAS,
)
from app.tools.rag_tool import search_insurance_rules
from app.tools.calculators import query_premium_rate, query_cash_value


# ==========================================
# LLM 初始化
# ==========================================
llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

tools = [search_insurance_rules, query_premium_rate, query_cash_value]
llm_with_tools = llm.bind_tools(tools)


# ==========================================
# 结构化输出模型
# ==========================================
class DialogueStateUpdate(BaseModel):
    current_stage: str = Field(
        description="当前对话阶段，必须严格输出: INTRODUCTION, OBJECTION, DECISION_SIGN, DECISION_REJECT"
    )
    reasoning: str = Field(description="判断理由，简短说明")


# ==========================================
# 节点 1：对话管理员（状态跟踪 + ≥5轮防线）
# ==========================================
def dialogue_manager_node(state: AgentState) -> dict:
    """分析销售发言 → 判定对话阶段 → 执行强制≥5轮逻辑"""
    # 回合计数 +1
    turn_count = state.get("turn_count", 0) + 1
    print(f"\n{'='*50}")
    print(f"🚦 [对话管理] 第 {turn_count} 轮开始")

    # 获取最新的销售发言
    human_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    sales_msg = human_msg.content if human_msg else ""

    # 构造状态判定 Prompt
    tracker_prompt = f"""你是保险销售对练系统的对话状态跟踪器。请分析销售刚说的话，判断当前阶段。
销售说："{sales_msg}"

可选阶段（必须严格输出英文标识）：
1. INTRODUCTION：销售在寒暄、拉家常、询问健康/财务状况、介绍产品概览。
2. OBJECTION：销售在应对客户质疑（如太贵、不赔、条款问题等），或者在详细解释产品细节。
3. DECISION_SIGN：销售明确催促签单、要求支付、确认购买意向，且客户态度已转为积极。
4. DECISION_REJECT：客户已经明确多次拒绝，销售无法挽回。

请严格按以下 JSON 格式输出：
{{
  "current_stage": "填入上述四个英文阶段之一",
  "reasoning": "简短说明判断理由"
}}"""

    structured_llm = llm.with_structured_output(DialogueStateUpdate, method="json_mode")
    result: DialogueStateUpdate = structured_llm.invoke(tracker_prompt)

    detected_stage = result.current_stage
    force_objection = False

    print(f"📌 [状态判定] LLM 判定为: {detected_stage} (理由: {result.reasoning})")

    # ========== 核心：强制 ≥5 轮防线 ==========
    is_decision = detected_stage in [DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT]
    if is_decision and turn_count < MIN_TURNS_BEFORE_DECISION:
        print(f"🛡️ [防线触发] 第 {turn_count} 轮就想进入决策？强制拖回 OBJECTION！(需要至少 {MIN_TURNS_BEFORE_DECISION} 轮)")
        detected_stage = DialogueStage.OBJECTION
        force_objection = True

    print(f"📌 [最终阶段] → {detected_stage} (第 {turn_count} 轮)")
    print(f"{'='*50}")

    return {
        "current_stage": detected_stage,
        "turn_count": turn_count,
        "force_objection": force_objection,
        "tool_calls_log": [],  # 每轮重置工具日志
    }


# ==========================================
# 节点 2：客户 Agent（基于画像思考并回复）
# ==========================================
def customer_node(state: AgentState) -> dict:
    """根据画像和当前阶段生成客户回复"""
    persona_id = state.get("persona_id", "hard_boss")
    persona = PERSONAS.get(persona_id, {})
    stage = state.get("current_stage", DialogueStage.INTRODUCTION)
    turn_count = state.get("turn_count", 1)
    force_objection = state.get("force_objection", False)

    print(f"👤 [客户Agent] 画像={persona.get('name', persona_id)}, 阶段={stage}, 第{turn_count}轮")

    # 构建阶段行为指令
    stage_instructions = _build_stage_instructions(stage, turn_count, force_objection, persona)

    # 核心 System Prompt
    sys_prompt_content = f"""你正在参与一场真实的健康险销售对练。请你完美扮演以下客户，绝不能暴露你是AI。

【你的基本信息】
身份：{persona.get('demographics', '未知')}
财务状况：{persona.get('financial_status', '未知')}
健康状况：{persona.get('health_status', '未知')}

【你的性格与认知】
对待保险的态度：{persona.get('insurance_awareness', '未知')}
风险偏好：{persona.get('risk_preference', '未知')}
最关心的问题：{persona.get('core_focus', '未知')}

【绝对行为准则（你必须严格遵守）】
1. 沟通风格：{persona.get('communication_style', '正常沟通')}
2. 核心机密：{persona.get('hidden_secrets', '无')}
3. 当前回合：第 {turn_count} 轮对话
4. 当前阶段：{stage}

{stage_instructions}

【工具使用规则】
如果销售提到特定的保险条款、费率、现金价值等你不确定的信息，请调用工具查证，绝不要瞎编数据。

注意：请直接以第一人称（我）与销售对话，输出你的真实反应，不要带任何前缀或内心OS。保持回复简洁有力，通常不超过100字。"""

    sys_prompt = SystemMessage(content=sys_prompt_content)
    messages_to_send = [sys_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_send)

    return {"messages": [response]}


def _build_stage_instructions(stage: str, turn_count: int, force_objection: bool, persona: dict) -> str:
    """根据当前阶段和状态构建行为指令"""

    # 如果被强制拉回异议阶段
    if force_objection:
        triggers = persona.get("objection_triggers", [])
        trigger_hint = triggers[turn_count % len(triggers)] if triggers else "我还要再想想"
        return f"""【⚠️ 强制指令】销售试图过早逼单，但你还不买账！
你必须找借口拖延或提出新的质疑。参考方向："{trigger_hint}"
不要轻易被说服，保持你的怀疑态度！"""

    if stage == DialogueStage.INTRODUCTION:
        return """【阶段指令 - 破冰探寻】
你刚见到这个销售，对他保持警惕但愿意听听。
- 可以简单回应寒暄，但不要主动暴露太多个人信息
- 等销售引导话题，适当回应"""

    elif stage == DialogueStage.OBJECTION:
        return """【阶段指令 - 异议处理】
你对保险持质疑态度，根据你的性格提出尖锐问题。
- 根据你最关心的问题进行追问
- 如果销售说得有道理，可以稍微软化态度，但依然保持谨慎
- 如果销售说得不专业或有漏洞，立刻反驳"""

    elif stage == DialogueStage.DECISION_SIGN:
        return """【阶段指令 - 决策签单】
经过多轮交流，你被说服了。
- 表示认可销售的专业度
- 询问具体投保流程和细节
- 可以提出最后一些小问题但整体态度积极"""

    elif stage == DialogueStage.DECISION_REJECT:
        return """【阶段指令 - 决策拒绝】
你已经下定决心不买了。
- 明确但礼貌地拒绝
- 给出你拒绝的核心原因
- 保持立场坚定"""

    return ""


# ==========================================
# 节点 3：工具执行（ToolNode）
# ==========================================
tool_node = ToolNode(tools)

def tools_with_logging(state: AgentState) -> dict:
    """包装 ToolNode，添加工具调用日志"""
    last_msg = state["messages"][-1]
    log_entries = state.get("tool_calls_log", [])

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        for tc in last_msg.tool_calls:
            log_entry = f"🔧 调用工具: {tc['name']}({tc.get('args', {})})"
            log_entries.append(log_entry)
            print(f"  {log_entry}")

    # 执行真实的工具
    result = tool_node.invoke(state)

    return {**result, "tool_calls_log": log_entries}


# ==========================================
# 路由：客户思考完后去哪里
# ==========================================
def route_customer(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("🔀 [路由] → 客户需要查资料 → 工具节点")
        return "tools"
    print("🔀 [路由] → 客户回复完毕 → 结束本轮")
    return END


# ==========================================
# 编译图
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("dialogue_manager", dialogue_manager_node)
workflow.add_node("customer", customer_node)
workflow.add_node("tools", tools_with_logging)

workflow.add_edge(START, "dialogue_manager")
workflow.add_edge("dialogue_manager", "customer")
workflow.add_conditional_edges("customer", route_customer)
workflow.add_edge("tools", "customer")

# 使用 MemorySaver 保持对话记忆（session_id 作为 thread_id）
memory = MemorySaver()
customer_graph = workflow.compile(checkpointer=memory)

print("✅ 客户专用 LangGraph 图编译完成！")
