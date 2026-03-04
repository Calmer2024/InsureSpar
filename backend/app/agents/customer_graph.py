# 文件：app/agents/customer_graph.py
"""客户专用 LangGraph 图 — 不含考官，只负责 [客户思考 → 工具调用 → 状态判定] 闭环

⚠️ 核心架构说明：
  一轮完整交互 = 销售说一句(HumanMessage传入) + 客户回一句(customer_node) + 状态判定(DM)
  
  图执行顺序：START → customer_node → (tools循环) → dialogue_manager → END
  - customer_node 使用上一轮 DM 设定的 current_stage 来决定回复风格
  - dialogue_manager 在客户回复后，分析完整的销售+客户一来一回，判定阶段供下一轮使用
"""
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
    DECISION_STRIKES_REQUIRED,
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
# 节点 1：客户 Agent（基于画像思考并回复）
# ==========================================
def customer_node(state: AgentState) -> dict:
    """根据画像和当前阶段（由上一轮 DM 设定）生成客户回复"""
    persona_id = state.get("persona_id", "hard_boss")
    persona = PERSONAS.get(persona_id, {})
    stage = state.get("current_stage", DialogueStage.INTRODUCTION)
    # 回合计数逻辑：仅由于人类/销售发言触发才会增加回合数，避免使用工具时反复循环累加
    turn_count = state.get("turn_count", 0)
    messages = state.get("messages", [])
    is_first_entry = bool(messages and messages[-1].type == "human")
    
    if is_first_entry:
        turn_count += 1

    force_objection = state.get("force_objection", False)
    pending_shutdown = state.get("pending_shutdown", False)

    if is_first_entry:
        print(f"\n{'='*50}")
        print(f"🚦 第 {turn_count} 轮开始 | 当前阶段: {stage}{' (准备关闭)' if pending_shutdown else ''}")
        print(f"👤 [客户Agent] 画像={persona.get('name', persona_id)}, 第{turn_count}轮")

    stage_instructions = _build_stage_instructions(stage, turn_count, force_objection, persona, pending_shutdown)

    sys_prompt_content = f"""你正在参与保险销售对练，完美扮演以下客户，绝不暴露AI身份。

⚠️ 身份锚定 — 你是【客户】，不是销售！
- 你是来被推销的那个人，销售在向你推销保险
- 你绝对不能站在销售立场说话、不能推荐产品、不能介绍保障方案
- 如果你发现自己在"推销"或"介绍产品优势"，立刻停下来，那不是你该做的事

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
如果你懂保险且有能力查核，可调用工具查证销售的说法。如果你的画像表明你不懂或不看条款，则绝对不调用进行查证核实。

直接以第一人称与销售对话，不要带前缀或内心OS。回复简洁有力，不超过100字。
重申：你是客户，你在回应销售对你说的话。"""

    sys_prompt = SystemMessage(content=sys_prompt_content)
    # 在对话历史末尾额外注入角色提醒，对抗多轮对话后的角色漂移
    role_reminder = SystemMessage(content="记住：你现在是【客户】，正在回应销售的话。请以客户身份回复。")
    messages_to_send = [sys_prompt] + state["messages"] + [role_reminder]
    response = llm_with_tools.invoke(messages_to_send)

    return {"messages": [response], "turn_count": turn_count}


# ==========================================
# 节点 2：工具执行（ToolNode）
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
# 节点 3：对话管理员（本轮结束后判定阶段）
# ==========================================
def dialogue_manager_node(state: AgentState) -> dict:
    """在客户回复完毕后，分析完整的一来一回，判定阶段供下一轮使用。

    此时 state["messages"] 中：
    - 最新的 AI 消息 = 本轮客户刚说的话 ✅
    - 最新的 Human 消息 = 本轮销售说的话 ✅
    两者都是本轮的，时序完全对齐！
    """
    turn_count = state.get("turn_count", 1)
    pending_shutdown = state.get("pending_shutdown", False)
    prev_stage = state.get("current_stage", DialogueStage.INTRODUCTION)

    # 如果已经在准备关闭阶段，直接继承上一阶段并返回，不再进行任何评判
    if pending_shutdown:
        print(f"🚦 [状态判定] 当前处于 pending_shutdown 告别阶段，跳过判断，直接完成。")
        return {
            "current_stage": prev_stage,
            "detected_stage_raw": prev_stage,
            "force_objection": False,
            "tool_calls_log": [],
            "stage_reasoning": "会话已彻底关闭",
            "decision_strike": state.get("decision_strike", 2),
        }

    # ========== 提取本轮 + 上一轮的对话 ==========
    sales_msg = ""
    customer_msg = ""
    prev_sales_msg = ""
    prev_customer_msg = ""
    round_found = 0  # 已找到几轮完整对话

    for m in reversed(state["messages"]):
        if round_found == 0:
            # 本轮
            if m.type == "ai" and not customer_msg:
                if hasattr(m, "tool_calls") and m.tool_calls and not m.content:
                    continue
                customer_msg = m.content
            elif m.type == "human" and not sales_msg:
                sales_msg = m.content
            if sales_msg and customer_msg:
                round_found = 1
        elif round_found == 1:
            # 上一轮
            if m.type == "ai" and not prev_customer_msg:
                if hasattr(m, "tool_calls") and m.tool_calls and not m.content:
                    continue
                prev_customer_msg = m.content
            elif m.type == "human" and not prev_sales_msg:
                prev_sales_msg = m.content
            if prev_sales_msg and prev_customer_msg:
                round_found = 2
                break

    print(f"🚦 [状态判定] 分析第 {turn_count} 轮完整对话...")
    print(f"   销售说: {sales_msg[:80]}...")
    print(f"   客户说: {customer_msg[:80]}...")

    # ========== 构建上下文信息 ==========
    prev_context = ""
    if prev_sales_msg and prev_customer_msg:
        prev_context = f"""【上一轮对话（第{turn_count - 1}轮）参考】
销售说："{prev_sales_msg[:200]}"
客户回复："{prev_customer_msg[:200]}"
上一轮判定阶段：{prev_stage}

"""

    # ========== LLM 判定阶段 ==========
    tracker_prompt = f"""你是对话状态跟踪器。一轮完整对话刚刚结束，请判定当前所处的阶段。

{prev_context}【本轮完整对话（第{turn_count}轮）】
销售说："{sales_msg[:300]}"
客户回复（⭐ 核心判定依据）："{customer_msg[:300]}"

上一轮判定阶段为：{prev_stage}
请结合上下文的对话趋势进行判定。注意阶段应该有连贯性，如果上一轮已判定为某个决策阶段，本轮客户仍在配合推进（如进行健康告知、确认方案细节），则应维持或升级该决策阶段，而非回退。

可选阶段（严格输出英文标识之一）：

1. INTRODUCTION (沟通介绍)：
   双方正在寒暄、收集基础信息、或者刚开始介绍产品。

2. OBJECTION (异议处理) - ⚔️ 核心阶段，优先考虑！
   客户还在提出疑问（问条款、问理赔）、嫌贵、觉得麻烦。
   ⚠️注意：如果客户说"我再考虑考虑"，但紧接着又问了问题或抱怨了价格，这属于伪装成拖延的异议，必须判定为本状态！只要话语中包含转折（"但是..."）或抛出新问题，就是异议！

3. DECISION_FOLLOW_UP (待跟进/拖延考虑 - 中性结局)：
   客户没有死磕具体问题，而是明确要求结束当下的对话，给出需要时间或外力的理由。
   触发特征："今天先这样吧，我得跟老婆商量"、"你发资料我周末看"。

4. DECISION_PENDING (同意核保/体检 - 成功结局)：🏆 最高优先级
   只要客户明确答应去体检、提供病历、或同意提交预核保（就算带条件），立刻判定！
   ⛔️ 拦截：仅回答健康问题（如"我血压150"）属于提供信息，不属于同意核保！

5. DECISION_SIGN (明确签单 - 成功结局)：
   客户没有任何遗留疑问，明确表示现在就买、直接交钱签合同。
   ⚠️ 重要：如果上一轮已经判定为 DECISION_SIGN，本轮客户继续配合（如进行健康告知、确认投保资料），应维持 DECISION_SIGN，不应降级。

6. DECISION_REJECT (明确拒绝 - 失败结局)：
   客户明确表示坚决不买、不需要保险、或态度恶劣要求不要再联系。

7. DECISION_ABANDON (放弃投保 - 客观终止)：
   因客观原因（如健康问题导致无法通过核保、年龄超限等）客户无法购买本重疾险产品，转向介绍其他险种。
   触发特征：销售已明确告知客户不符合投保条件，客户接受现实并放弃投保；或双方已转向讨论其他替代方案。
   ⚠️ 注意：这不是客户的主观拒绝，而是客观条件不允许。

输出 JSON：
{{
  "current_stage": "填入上述七个英文阶段之一",
  "reasoning": "结合客户回复，一句话说明判定理由"
}}"""

    structured_llm = llm.with_structured_output(DialogueStateUpdate, method="json_mode")
    result: DialogueStateUpdate = structured_llm.invoke(tracker_prompt)

    detected_stage = result.current_stage
    detected_stage_raw = detected_stage  # 保存原始判定
    reasoning = result.reasoning
    force_objection = False

    print(f"📌 [状态判定] LLM 判定为: {detected_stage} (理由: {reasoning})")

    # ========== 核心：强制 ≥5 轮防线 ==========
    is_decision = detected_stage in [
        DialogueStage.DECISION_SIGN, DialogueStage.DECISION_REJECT,
        DialogueStage.DECISION_PENDING, DialogueStage.DECISION_FOLLOW_UP,
        DialogueStage.DECISION_ABANDON,
    ] 
    if is_decision and turn_count < MIN_TURNS_BEFORE_DECISION:
        print(f"🛡️ [防线触发] 第 {turn_count} 轮就想进入决策？强制拖回 OBJECTION！(需要至少 {MIN_TURNS_BEFORE_DECISION} 轮)")
        detected_stage = DialogueStage.OBJECTION
        force_objection = True
        reasoning += f" [防线触发: 第{turn_count}轮 < {MIN_TURNS_BEFORE_DECISION}轮]"
        is_decision = False

    # ========== 连续 N 轮确诊防线 ==========
    decision_strike = state.get("decision_strike", 0)
    if is_decision:
        decision_strike += 1
        print(f"⚖️ [决策观察期] 当前连续进入决策状态 {decision_strike}/{DECISION_STRIKES_REQUIRED} 轮")
        if decision_strike < DECISION_STRIKES_REQUIRED:
            print(f"🛡️ [防线触发] 尚未连续 {DECISION_STRIKES_REQUIRED} 轮确认，继续保持 OBJECTION！")
            detected_stage = DialogueStage.OBJECTION
            reasoning += f" [观察期: {decision_strike}/{DECISION_STRIKES_REQUIRED}]"
    else:
        if decision_strike > 0:
            print(f"♻️ [决策观察期] 意愿发生动摇，清零计数器")
        decision_strike = 0

    print(f"📌 [最终阶段] → {detected_stage} (第 {turn_count} 轮结束)")
    print(f"{'='*50}")

    return {
        "current_stage": detected_stage,
        "detected_stage_raw": detected_stage_raw,
        "force_objection": force_objection,
        "tool_calls_log": [],
        "stage_reasoning": reasoning,
        "decision_strike": decision_strike,
    }


# ==========================================
# 客户节点的阶段行为指令
# ==========================================
def _build_stage_instructions(stage: str, turn_count: int, force_objection: bool, persona: dict, pending_shutdown: bool = False) -> str:
    """根据当前阶段和状态构建行为指令"""

    if pending_shutdown:
        return """【⚠️ 强制指令：最后告别阶段】
销售正在与你进行最后的礼貌告别。
你必须只用依据简短、礼貌的话进行回应（如“好的，再见”，“谢谢，拜拜”）。
绝对不可以提出任何新的问题、新的异议或者开启新话题！"""

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
# 路由：客户思考完后去哪里
# ==========================================
def route_customer(state: AgentState) -> str:
    """客户回复后路由：有工具调用 → tools，否则 → DM 判定阶段"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("🔀 [路由] → 客户需要查资料 → 工具节点")
        return "tools"
    print("🔀 [路由] → 客户回复完毕 → 状态判定")
    return "dialogue_manager"


# ==========================================
# 编译图（核心：先客户回复，后状态判定）
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("customer", customer_node)
workflow.add_node("tools", tools_with_logging)
workflow.add_node("dialogue_manager", dialogue_manager_node)

# 图结构: START → customer → (tools 循环 | DM) → END
workflow.add_edge(START, "customer")
workflow.add_conditional_edges("customer", route_customer)
workflow.add_edge("tools", "customer")       # 工具结果返回给客户继续思考
workflow.add_edge("dialogue_manager", END)   # DM 判定完毕 → 本轮结束

memory = MemorySaver()
customer_graph = workflow.compile(checkpointer=memory)

print("✅ 客户专用 LangGraph 图编译完成！(流程: 客户回复 → 状态判定 → 结束)")
