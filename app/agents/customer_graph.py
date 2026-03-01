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
        description="当前对话阶段，必须严格输出: INTRODUCTION, OBJECTION, DECISION_SIGN, DECISION_PENDING, DECISION_FOLLOW_UP, DECISION_REJECT"
    )
    reasoning: str = Field(description="判断理由，简短说明")


# ==========================================
# 节点 1：对话管理员（状态跟踪 + ≥5轮防线）
# ==========================================
def dialogue_manager_node(state: AgentState) -> dict:
    """分析销售发言 → 判定对话阶段 → 执行强制≥5轮逻辑"""
    turn_count = state.get("turn_count", 0) + 1
    print(f"\n{'='*50}")
    print(f"🚦 [对话管理] 第 {turn_count} 轮开始")

    human_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    sales_msg = human_msg.content if human_msg else ""

    # 精简的状态判定 Prompt（节约 token）
    tracker_prompt = f"""你是对话状态跟踪器。根据销售最新发言判定当前阶段。
销售说："{sales_msg[:300]}"

六个阶段（严格输出英文标识）：
1. INTRODUCTION — 寒暄问候、了解需求、介绍产品概括
2. OBJECTION — 应对客户质疑（太贵/不赔/条款等），详细解释产品
3. DECISION_SIGN — 客户明确表示"我买""签吧""交钱"，没有附加条件
4. DECISION_PENDING — 客户积极但有条件：如"先做核保""提交体检报告""看看核保结果再说"
5. DECISION_FOLLOW_UP — 客户态度缓和但拖延："要和老公商量""下个月再说""回去考虑"
6. DECISION_REJECT — 客户明确拒绝："不买了""太贵了不考虑""再见"

⚠️ 判定要点：
- 客户说"可以先配置基础保障，但要看核保结果" → DECISION_PENDING（不是SIGN！）
- 客户说"好的我买" → DECISION_SIGN
- 客户说"我回去和老公商量" → DECISION_FOLLOW_UP
- 客户问"犹豫期怎么退"只是在了解信息 → OBJECTION（不是SIGN！）

输出 JSON：
{{
  "current_stage": "填入上述六个英文阶段之一",
  "reasoning": "一句话说明理由"
}}"""

    structured_llm = llm.with_structured_output(DialogueStateUpdate, method="json_mode")
    result: DialogueStateUpdate = structured_llm.invoke(tracker_prompt)

    detected_stage = result.current_stage
    reasoning = result.reasoning
    force_objection = False

    print(f"📌 [状态判定] LLM 判定为: {detected_stage} (理由: {reasoning})")

    # ========== 核心：强制 ≥5 轮防线 ==========
    is_decision = detected_stage in [
        DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT,
        DialogueStage.DECISION_PENDING, DialogueStage.DECISION_FOLLOW_UP,
    ]
    if is_decision and turn_count < MIN_TURNS_BEFORE_DECISION:
        print(f"🛡️ [防线触发] 第 {turn_count} 轮就想进入决策？强制拖回 OBJECTION！(需要至少 {MIN_TURNS_BEFORE_DECISION} 轮)")
        detected_stage = DialogueStage.OBJECTION
        force_objection = True
        reasoning += f" [防线触发: 第{turn_count}轮 < {MIN_TURNS_BEFORE_DECISION}轮]"

    print(f"📌 [最终阶段] → {detected_stage} (第 {turn_count} 轮)")
    print(f"{'='*50}")

    return {
        "current_stage": detected_stage,
        "turn_count": turn_count,
        "force_objection": force_objection,
        "tool_calls_log": [],
        "stage_reasoning": reasoning,
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

    stage_instructions = _build_stage_instructions(stage, turn_count, force_objection, persona)

    # 核心 System Prompt（精简版，节约 token）
    sys_prompt_content = f"""你正在参与保险销售对练，完美扮演以下客户，绝不暴露AI身份。

【本次销售产品】
唯一产品：泰康乐享健康2026重大疾病保险。不要讨论或购买其他产品。

【你的基本信息】
{persona.get('demographics', '未知')} | {persona.get('financial_status', '未知')} | {persona.get('health_status', '未知')}

【性格与认知】
态度：{persona.get('insurance_awareness', '未知')}
风险偏好：{persona.get('risk_preference', '未知')}
核心关注：{persona.get('core_focus', '未知')}

【行为准则】
1. 沟通风格：{persona.get('communication_style', '正常沟通')}
2. 核心机密：{persona.get('hidden_secrets', '无')}
3. 决策强制线：当【当前回合】达到或超过 8 轮时，你必须根据之前的感受，逐渐引导明确走向【签单成交】或【彻底拒绝】，不要再继续抛出新问题无限纠结！
4. 当前回合：第 {turn_count} 轮 | 阶段：{stage}

{stage_instructions}

【工具使用】
如果你懂保险且有能力查核，可调用工具查证销售的说法。如果你的画像表明你不懂或不看条款，则不调用。

直接以第一人称与销售对话，不要带前缀或内心OS。回复简洁有力，不超过100字。"""

    sys_prompt = SystemMessage(content=sys_prompt_content)
    messages_to_send = [sys_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_send)

    return {"messages": [response]}


def _build_stage_instructions(stage: str, turn_count: int, force_objection: bool, persona: dict) -> str:
    """根据当前阶段和状态构建行为指令"""

    if force_objection:
        triggers = persona.get("objection_triggers", [])
        trigger_hint = triggers[turn_count % len(triggers)] if triggers else "我还要再想想"
        return f"""【⚠️ 强制指令】销售试图过早逼单，但你还不买账！
你必须找借口拖延或提出新的质疑。参考方向："{trigger_hint}"
不要轻易被说服，保持你的怀疑态度！"""

    if stage == DialogueStage.INTRODUCTION:
        return """【阶段 - 破冰探寻】
你刚见到销售，保持警惕但愿意听听。简单回应寒暄，不主动暴露太多信息。"""

    elif stage == DialogueStage.OBJECTION:
        return """【阶段 - 异议处理】
你对保险持质疑态度，根据你的性格提出尖锐问题。
- 如果销售说得有道理，可以稍微软化
- 如果销售说得不专业或有漏洞，立刻反驳"""

    elif stage == DialogueStage.DECISION_SIGN:
        return """【阶段 - 签单成交】
经过多轮交流，你被说服了。
- 表示认可销售的专业度
- 整体态度积极"""

    elif stage == DialogueStage.DECISION_PENDING:
        return """【阶段 - 同意核保】
你有一定购买意愿，但你有非标体情况（或想更稳妥），所以：
- 表示愿意先提交体检报告或病历进行预核保
- 态度积极但谨慎，想看核保结果再做最终决定
- 可以询问核保流程和时间"""

    elif stage == DialogueStage.DECISION_FOLLOW_UP:
        return """【阶段 - 需要跟进】
你态度缓和但还没准备好当场决定：
- 说出你的拖延理由（和家人商量/资金不到位/需要时间考虑）
- 不要完全拒绝，留下跟进的口子
- 如果销售说的好可以松口约下次见面"""

    elif stage == DialogueStage.DECISION_REJECT:
        return """【阶段 - 明确拒绝】
你已下定决心不买了。
- 明确但礼貌地拒绝
- 给出核心原因
- 立场坚定"""

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

memory = MemorySaver()
customer_graph = workflow.compile(checkpointer=memory)

print("✅ 客户专用 LangGraph 图编译完成！")
