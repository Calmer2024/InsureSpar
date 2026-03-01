# 文件：app/agents/sales_agent.py
"""销售 Agent — 可调用工具的专业销售 AI，用于 Auto-Agent 自动对战模式"""
import asyncio
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.core.config import LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, SALES_STRATEGIES, PERSONAS
from app.agents.state import DialogueStage
from app.tools.rag_tool import search_insurance_rules
from app.tools.calculators import query_premium_rate, query_cash_value


# ==========================================
# LLM + 工具绑定
# ==========================================
sales_llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    streaming=True,
)

TOOLS = [search_insurance_rules, query_premium_rate, query_cash_value]
sales_llm_with_tools = sales_llm.bind_tools(TOOLS)

# 工具名 → 可调用函数 的映射（供手动执行工具）
TOOL_EXECUTOR = {
    "search_insurance_rules": search_insurance_rules,
    "query_premium_rate": query_premium_rate,
    "query_cash_value": query_cash_value,
}

# 阶段中文标签
STAGE_LABELS = {
    DialogueStage.INTRODUCTION:       "💬 破冰与探寻",
    DialogueStage.OBJECTION:          "⚡ 异议处理",
    DialogueStage.DECISION_SIGN:      "✅ 签单成功",
    DialogueStage.DECISION_PENDING:   "📋 同意核保",
    DialogueStage.DECISION_FOLLOW_UP: "📞 需要跟进",
    DialogueStage.DECISION_REJECT:    "❌ 客户拒绝",
}


# ==========================================
# 核心：销售 Agent 推进一步（流式生成器）
# ==========================================
async def sales_agent_step(
    session_id: str,
    strategy_id: str,
    persona_id: str,
    current_stage: str,
    turn_count: int,
    conversation_history: list,  # [{"role": "sales"|"customer", "content": "..."}]
):
    """
    销售 Agent 推进一步：
    1. 构建 System Prompt（含策略风格 + 阶段指令）
    2. 调用 LLM，若有工具调用则执行并继续
    3. 逐 token 流式生成销售最终发言

    为异步生成器，yield 各种事件字典供 SSE 端点使用。
    """
    strategy = SALES_STRATEGIES.get(strategy_id, {})
    persona = PERSONAS.get(persona_id, {})

    # ---- 构建 System Prompt ----
    stage_instruction = _build_sales_stage_instruction(current_stage, turn_count, persona)
    system_content = f"""你是一名保险销售顾问，正在与客户进行真实的销售对话，你正在销售。

【你的销售风格：{strategy.get('name', '专业顾问型')}】
{strategy.get('prompt_instructions', '')}

【客户基本信息（你掌握的已知情况）】
姓名/身份：{persona.get('demographics', '未知')}
财务背景：{persona.get('financial_status', '未知')}
对保险的态度：{persona.get('insurance_awareness', '未知')}
最关心的问题：{persona.get('core_focus', '未知')}

【销售保险信息】
现在需要销售的产品是“泰康乐享健康2026重大疾病保险”。该产品为终身重大疾病保险，仅提供终身保障，不存在任何定期版本。被保险人投保年龄必须在0至70周岁（含）之间，超出范围必须明确拒绝投保，不得承诺特殊通融。
产品支持趸交和年交两种缴费方式。年交可选1年、3年、5年、10年、15年、20年、25年、30年，但必须满足“投保年龄＋缴费年期≤75”的规则，否则不能承保。例如55岁客户最长只能选择20年交。面对客户关于缴费年期的提问，必须主动进行年龄与缴费期的合规计算并解释逻辑。
本产品等待期为90天，
理赔金额与出险时被保险人年龄相关
产品实行严格的责任互斥原则。重大疾病保险金、全残保险金、疾病终末期保险金和身故保险金仅赔付其中一项，一旦任何一项完成赔付，合同即终止，其余责任失效。不得暗示或承诺可叠加理赔。

【当前对话状态】
阶段：{current_stage} — {STAGE_LABELS.get(current_stage, '')}
回合数：第 {turn_count} 轮
{stage_instruction}

【工具使用强制规范】
- 报任何保费数字前：必须先调用 query_premium_rate 工具查实际费率
- 提到现金价值或退保金额前：必须先调用 query_cash_value 查询
- 引用任何保险条款/核保规则前：必须先调用 search_insurance_rules 验证

直接输出你要对客户说的话，不要有任何内心OS或前缀说明，不要使用任何MD格式标记。"""

    # ---- 构建消息历史 ----
    messages = [SystemMessage(content=system_content)]
    for turn in conversation_history:
        if turn["role"] == "sales":
            messages.append(AIMessage(content=turn["content"]))
        elif turn["role"] == "customer":
            messages.append(HumanMessage(content=turn["content"]))

    # 如果是第一轮且没有历史，添加开场提示
    if not conversation_history:
        messages.append(HumanMessage(content="[开始销售对话]"))

    yield {"type": "sales_thinking", "content": f"🧠 销售({strategy.get('name', '')})正在制定策略..."}

    # ---- 工具调用循环 ----
    final_response = ""
    tool_round = 0
    max_tool_rounds = 5  # 防止无限循环

    while tool_round < max_tool_rounds:
        tool_round += 1
        response = await sales_llm_with_tools.ainvoke(messages)

        # 检查是否有工具调用
        if response.tool_calls:
            messages.append(response)  # 把含 tool_calls 的 AI 消息加入历史

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_call_id = tc["id"]

                yield {
                    "type": "sales_tool_call",
                    "tool": tool_name,
                    "args": str(tool_args),
                }

                # 执行工具
                try:
                    tool_fn = TOOL_EXECUTOR.get(tool_name)
                    if tool_fn:
                        tool_result = tool_fn.invoke(tool_args)
                    else:
                        tool_result = f"工具 {tool_name} 不存在"
                except Exception as e:
                    tool_result = f"工具执行错误: {str(e)}"

                yield {
                    "type": "sales_tool_result",
                    "tool": tool_name,
                    "content": str(tool_result)[:500],
                }

                # 把工具结果加入消息
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id,
                ))

        else:
            # 无工具调用 → 输出最终销售话术（流式）
            final_response = response.content if response.content else ""
            break

    # ---- 如果工具循环结束后还没有文本输出，用最后一次的 content ----
    if not final_response and hasattr(response, "content") and response.content:
        final_response = response.content

    # 逐字符模拟流式推送（实际 LangChain 不支持在 ainvoke 后再 stream，这里做 chunk 分割推送）
    chunk_size = 3
    for i in range(0, len(final_response), chunk_size):
        chunk = final_response[i:i + chunk_size]
        yield {"type": "sales_token", "content": chunk}
        await asyncio.sleep(0.02)  # 模拟打字机延迟

    yield {"type": "sales_message_done", "content": final_response}


# ==========================================
# 阶段指令构建
# ==========================================
def _build_sales_stage_instruction(stage: str, turn_count: int, persona: dict) -> str:
    """根据阶段返回销售的行为指令"""
    if stage == DialogueStage.INTRODUCTION:
        return f"""【阶段任务 - 破冰探寻】
本阶段目标：建立信任 + 了解需求 + 引出产品话题
- 询问客户的家庭保障现状（是否已有保险）
- 了解客户最担心的风险（健康/意外/财务）
- 适当引导客户意识到保障缺口
- 根据客户的 "{persona.get('core_focus', '保障需求')}" 找切入点"""

    elif stage == DialogueStage.OBJECTION:
        return f"""【阶段任务 - 异议处理】
客户已提出质疑，这是关键考验。你的任务：
- 认同客户情绪，不要正面对抗
- 用工具查到的真实数据化解疑虑
- 针对客户核心关注点 "{persona.get('core_focus', '').split('、')[0]}" 重点击穿
- 如果客户关心费率，当场查询给出精确数字
- 回合数已达 {turn_count} 轮，可以开始试探性引导决策"""

    elif stage == DialogueStage.DECISION_SIGN:
        return """【阶段任务 - 临门一脚】
客户已有购买意向，此刻最忌拖泥带水。
- 确认产品/保额/交费期
- 告知下一步投保流程
- 不要再引入新话题"""

    elif stage == DialogueStage.DECISION_PENDING:
        return """【阶段任务 - 促成核保】
客户愿意推进但需要核保流程：
- 确认客户需要提交的材料（体检报告/病历）
- 解释预核保流程和时间
- 强调核保通过后可再做最终决定，降低客户心理压力"""

    elif stage == DialogueStage.DECISION_FOLLOW_UP:
        return """【阶段任务 - 争取跟进】
客户态度不错但想拖延：
- 理解客户的考虑，不要逼迫
- 约定具体的跟进时间（不要留模糊的"改天"）
- 留下关键资料或计算结果供客户回去参考"""

    elif stage == DialogueStage.DECISION_REJECT:
        return """【阶段任务 - 挽回或收场】
客户已拒绝：
- 如有机会：抛出最后一个有力论点
- 如态度坚决：优雅收场，留好印象"""

    return ""
