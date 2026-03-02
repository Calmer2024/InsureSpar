# 文件：app/agents/evaluator.py
"""独立考官 Agent — 先取证再评分，异步三维度评分，不阻塞主流程"""
import re
import traceback
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.core.config import LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, PERSONAS
from app.services.session_manager import session_manager

# 导入工具函数（直接调用底层函数，不经过 LangChain 的 @tool 包装）
from app.tools.rag_tool import search_insurance_rules
from app.tools.calculators import query_premium_rate, query_cash_value


# ==========================================
# 结构化输出模型
# ==========================================
class FactClaimsExtraction(BaseModel):
    """从销售话术中提取的事实性声明"""
    has_premium_claim: bool = Field(description="销售是否提到了具体保费金额")
    premium_details: str = Field(default="", description="如有保费声明，提取：年龄、性别、交费期、保额、声称的保费金额")
    has_cash_value_claim: bool = Field(description="销售是否提到了现金价值或退保金额")
    cash_value_details: str = Field(default="", description="如有现金价值声明，提取：性别、年龄、交费期、年度、声称的金额")
    has_rule_claim: bool = Field(description="销售是否提到了保险条款、核保规则、理赔条件等")
    rule_query: str = Field(default="", description="如有规则声明，提取需要核实的关键内容作为查询词")
    summary: str = Field(description="简要概括销售本轮话术中的核心事实性声明")


class EvaluationResult(BaseModel):
    professionalism_score: int = Field(description="专业性得分 (0-10分)")
    compliance_score: int = Field(description="合规性得分 (0-10分)")
    strategy_score: int = Field(description="销售策略得分 (0-10分)")
    professionalism_comment: str = Field(description="专业性点评")
    compliance_comment: str = Field(description="合规性点评")
    strategy_comment: str = Field(description="销售策略点评")
    overall_advice: str = Field(description="一句话改进建议")


# ==========================================
# 考官 LLM（独立实例）
# ==========================================
evaluator_llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)


# ==========================================
# 阶段一：事实提取（从销售话术中抽取可核查的声明）
# ==========================================
async def _extract_fact_claims(sales_msg: str, customer_reply: str, recent_context: str = "") -> FactClaimsExtraction:
    """让 LLM 从销售话术中提取所有事实性声明，结合最近的上下文"""
    import json
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    system_prompt = """你是一个事实核查助手。请仔细阅读【对话上下文】以及本轮【销售说】的话术，提取销售话语中可以被数据核实的事实性声明。
请严格按以下 JSON 格式输出（必须包含所有字段）：

EXAMPLE JSON OUTPUT:
{
  "has_premium_claim": true,
  "premium_details": "45岁男性，20年交，100万保额，声称每年保费43500元",
  "has_cash_value_claim": false,
  "cash_value_details": "",
  "has_rule_claim": true,
  "rule_query": "高血压能否投保",
  "summary": "销售声称45岁男性20年交100万保额每年43500元，并说高血压可以正常投保"
}"""

    user_prompt = f"""【最近对话上下文】
{recent_context}

【本轮待核单词】
销售说："{sales_msg}"
客户回应："{customer_reply}"

请判断本轮【销售说】的内容中：
1. 是否提到了具体的保费金额？（如"每年交43500元"）
   - 如果有，提取涉及的年龄、性别、交费期、保额和声称的金额。如果保额未直接提及，请从【对话上下文】中寻找客户或销售之前确认过的保额。
2. 是否提到了现金价值/退保金额？（如"第10年退保能拿回3万"）
   - 如果有，同上提取关键要素，缺失的要素从上下文中推断。
3. 是否提到了保险条款、核保规则、理赔条件等？
   - 如果有，提取核心声明作为查询关键词"""

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={'type': 'json_object'},
            temperature=0.1
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        result = FactClaimsExtraction(**data)
        print(f"🔎 [考官取证] 事实提取完成: {result.summary}")
        return result
    except Exception as e:
        print(f"⚠️ [考官取证] 事实提取失败: {e}")
        return FactClaimsExtraction(
            has_premium_claim=False, has_cash_value_claim=False,
            has_rule_claim=False, summary="提取失败"
        )


# ==========================================
# 阶段二：工具核查（用工具检验事实是否属实）
# ==========================================
async def _verify_facts(claims: FactClaimsExtraction, recent_context: str = "") -> str:
    """根据提取的声明，调用工具获取真实数据作为铁证"""
    evidence_parts = []

    # 1. 核查保费声明
    if claims.has_premium_claim and claims.premium_details:
        print(f"🔧 [考官取证] 正在核查保费声明...")
        try:
            # 尝试从描述和上下文中解析参数
            params = await _parse_premium_params(claims.premium_details, recent_context)
            if params:
                actual_result = query_premium_rate.invoke(params)
                evidence_parts.append(
                    f"📊 【保费核查】\n"
                    f"  销售声称：{claims.premium_details}\n"
                    f"  实际数据：{actual_result}\n"
                    f"  ⚠️ 如果两者数字不一致，说明销售报价不准确！"
                )
                print(f"  ✅ 保费核查完成")
        except Exception as e:
            print(f"  ⚠️ 保费核查异常: {e}")

    # 2. 核查现金价值声明
    if claims.has_cash_value_claim and claims.cash_value_details:
        print(f"🔧 [考官取证] 正在核查现金价值声明...")
        try:
            params = await _parse_cash_value_params(claims.cash_value_details, recent_context)
            if params:
                actual_result = query_cash_value.invoke(params)
                evidence_parts.append(
                    f"📊 【现金价值核查】\n"
                    f"  销售声称：{claims.cash_value_details}\n"
                    f"  实际数据：{actual_result}\n"
                    f"  ⚠️ 如果两者差距超过10%，说明销售给出的现金价值不准确！"
                )
                print(f"  ✅ 现金价值核查完成")
        except Exception as e:
            print(f"  ⚠️ 现金价值核查异常: {e}")

    # 3. 核查规则条款声明
    if claims.has_rule_claim and claims.rule_query:
        print(f"🔧 [考官取证] 正在核查规则声明: '{claims.rule_query}'")
        try:
            actual_rules = search_insurance_rules.invoke({"query": claims.rule_query})
            evidence_parts.append(
                f"📊 【规则条款核查】\n"
                f"  销售说法涉及：{claims.rule_query}\n"
                f"  知识库权威依据：\n{actual_rules}\n"
                f"  ⚠️ 请对照知识库判断销售的说法是否准确。如有曲解、遗漏或错误，专业性必须大幅扣分！"
            )
            print(f"  ✅ 规则核查完成")
        except Exception as e:
            print(f"  ⚠️ 规则核查异常: {e}")

    if not evidence_parts:
        return "（本轮销售话术未涉及可核查的事实性声明，请根据话术技巧和合规性进行评判）"

    return "\n\n".join(evidence_parts)


# ==========================================
# 辅助：参数解析（用LLM从自然语言中提取工具参数）
# ==========================================
class PremiumParams(BaseModel):
    age: int = Field(description="投保年龄")
    gender: str = Field(description="性别，'男' 或 '女'")
    pay_period: int = Field(description="交费期")
    base_amount: int = Field(default=10000, description="基本保额")


class CashValueParams(BaseModel):
    gender: str = Field(description="性别，'男' 或 '女'")
    age: int = Field(description="投保年龄")
    pay_period: int = Field(description="交费期")
    year: int = Field(description="保单年度")
    base_amount: int = Field(default=10000, description="基本保额")


async def _parse_premium_params(details: str, recent_context: str = "") -> dict | None:
    """用 LLM 从自然语言描述和最近上下文中提取保费查询参数"""
    try:
        prompt = f"""从以下核查对象和对话上下文中提取精准的保费查询参数，严格输出 JSON：

【核查对象】"{details}"

【对话上下文】
{recent_context}

特别规则：
1. 重疾险常规保额一般在 10万~100万之间（如 300000 相当于30万，1000000 相当于100万）。
2. 如果【核查对象】中没有明确提到保额金额，请务必仔细阅读【对话上下文】寻找客户或销售之前敲定的保额金额。
3. base_amount 必须是确切的数字格式（如有）。请确保它与上下文中的数字完全匹配。如果不确定，尝试寻找上下文最可能的合理保额。
4. 年龄、性别、交费期也需要补齐，默认可以参考画像。

输出格式：
{{"age": 45, "gender": "男", "pay_period": 20, "base_amount": 1000000}}"""

        structured = evaluator_llm.with_structured_output(PremiumParams, method="json_mode")
        result = structured.invoke(prompt)
        return {"age": result.age, "gender": result.gender,
                "pay_period": result.pay_period, "base_amount": result.base_amount}
    except Exception as e:
        print(f"    ⚠️ 保费参数解析失败: {e}")
        return None


async def _parse_cash_value_params(details: str, recent_context: str = "") -> dict | None:
    """用 LLM 从自然语言描述中提取现金价值查询参数"""
    try:
        prompt = f"""从以下核查对象和对话上下文中提取现金价值查询参数，严格输出 JSON：

【核查对象】"{details}"

【对话上下文】
{recent_context}

特别规则：
1. 重疾险常规保额一般在 10万~100万之间。
2. 同保费查询一样，务必结合【对话上下文】明确准确的保额 (base_amount) 提取。
3. base_amount 必须是数字格式。

输出格式：
{{"gender": "男", "age": 45, "pay_period": 20, "year": 10, "base_amount": 1000000}}"""

        structured = evaluator_llm.with_structured_output(CashValueParams, method="json_mode")
        result = structured.invoke(prompt)
        return {"gender": result.gender, "age": result.age,
                "pay_period": result.pay_period, "year": result.year,
                "base_amount": result.base_amount}
    except Exception as e:
        print(f"    ⚠️ 现金价值参数解析失败: {e}")
        return None


# ==========================================
# 核心评分函数（异步，供 BackgroundTasks 调用）
# ==========================================
async def evaluate_turn(
    session_id: str,
    turn_count: int,
    sales_msg: str,
    customer_reply: str,
    persona_id: str,
    current_stage: str = "未知阶段",
    conversation_history: list = None,
    sales_tool_calls: list = None,
    prev_scores: dict = None,
):
    """
    升级版考官：先取证，再评分。
    加入了阶段感知和防循环机制。
    """
    import json
    from openai import AsyncOpenAI
    
    persona = PERSONAS.get(persona_id, {})
    max_retries = 3

    print(f"\n{'='*50}")
    print(f"⚖️ [考官] 开始后台评分: 会话={session_id}, 第{turn_count}轮")
    print(f"{'='*50}")

    # 提取最近几轮对话上下文（取最近 6 条）
    recent_context = ""
    if conversation_history:
        recent_msgs = conversation_history[-6:]
        context_parts = []
        for msg in recent_msgs:
            role = "销售" if msg.get("role") == "sales" else "客户"
            context_parts.append(f"{role}: {msg.get('content')}")
        recent_context = "\n".join(context_parts)

    # ---- 阶段一：事实提取 ----
    claims = await _extract_fact_claims(sales_msg, customer_reply, recent_context)

    # ---- 阶段二：工具核查 ----
    evidence = await _verify_facts(claims, recent_context)

    # ---- 阶段2.5：合并销售的工具调用日志 ----
    sales_tool_evidence = ""
    if sales_tool_calls:
        parts = []
        for tc in sales_tool_calls:
            parts.append(f"  工具: {tc.get('tool', '?')} | 参数: {tc.get('args', '?')} | 结果: {tc.get('result', '?')[:200]}")
        sales_tool_evidence = "\n【📋 销售Agent本轮的工具调用记录（销售自己查到的数据）】\n" + "\n".join(parts)
        print(f"📋 [考官] 收到销售工具日志 {len(sales_tool_calls)} 条，将作为铁证参考")

    # ---- 阶段三：带证据评分 ----
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    # 移除上一轮建议的注入，仅保留分数作为参考，防止复读机
    prev_score_str = ""
    if prev_scores and prev_scores.get("professionalism_score", -1) >= 0:
        prev_score_str = f"上一轮得分参考：专业={prev_scores.get('professionalism_score')} 合规={prev_scores.get('compliance_score')} 策略={prev_scores.get('strategy_score')}"

    system_prompt = f"""你是保险销售对练考官。目前的会话阶段是：【{current_stage}】。
请针对**本轮**表现，依据事实核查报告和销售的话术，严格独立打分。不要机械重复之前的建议。

【阶段判卷重点】
- 破冰与探寻：重点看是否建立基础信任、是否挖掘隐患。没查户口不扣分。
- 异议处理：重点看是否针对客户问题对答如流、数据准确、有效化解顾虑。
- 方案报价与核保/促成：严查数字准确性，若出现虚假数据和违规承诺，请严厉惩罚。

【判卷维度 (0-10)】
1. 专业性：数据事实（保费等）与工具核查是否一致？造假≤3分。若未涉及数据可根据专业表达给分。
2. 合规性：是否存在误导或隐瞒？（例如无根据承诺“肯定能理赔”、“收益极高”，该项请≤5分）。
3. 策略性：结合当前【{current_stage}】阶段，策略是否得当？

⚠️ 独立评估本轮。不要重复上一轮的评语或建议。提供针对当下的具体指导！

输出必须包含以下7个JSON字段，分数必须是纯数字：
{{"professionalism_score":8,"compliance_score":9,"strategy_score":5,"professionalism_comment":"评价","compliance_comment":"评价","strategy_comment":"评价","overall_advice":"具体的建议，不要重复"}}"""

    user_prompt = f"""【客户画像】{persona.get('demographics', '未知')} | 态度: {persona.get('insurance_awareness', '未知')} | 关注: {persona.get('core_focus', '未知')}
隐藏机密：{persona.get('hidden_secrets', '无')}

【对话上下文参考】
{recent_context}

【本轮待打分内容】
{prev_score_str}
销售说：{sales_msg[:500]}
客户反应：{customer_reply[:300]}
{sales_tool_evidence}

【🔍 考官独立事实核查报告】
{evidence}
"""

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={'type': 'json_object'},
                temperature=0.2
            )
            content = response.choices[0].message.content
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            data = json.loads(content)
            result = EvaluationResult(**data)

            evaluation_dict = {
                "turn": turn_count,
                "professionalism_score": result.professionalism_score,
                "compliance_score": result.compliance_score,
                "strategy_score": result.strategy_score,
                "professionalism_comment": result.professionalism_comment,
                "compliance_comment": result.compliance_comment,
                "strategy_comment": result.strategy_comment,
                "overall_advice": result.overall_advice,
            }

            session_manager.add_evaluation(session_id, evaluation_dict)
            print(f"✅ [考官] 第{turn_count}轮评分完成: "
                  f"专业={result.professionalism_score} "
                  f"合规={result.compliance_score} "
                  f"策略={result.strategy_score}")
            print(f"   💬 建议: {result.overall_advice}")
            return

        except Exception as e:
            print(f"⚠️ [考官] 第{attempt + 1}次评分失败: {e}")
            if attempt < max_retries - 1:
                print(f"   🔄 重试中...")
            else:
                print(f"❌ [考官] 第{turn_count}轮评分彻底失败，放弃。")
                traceback.print_exc()
                session_manager.add_evaluation(session_id, {
                    "turn": turn_count,
                    "professionalism_score": -1,
                    "compliance_score": -1,
                    "strategy_score": -1,
                    "professionalism_comment": "评分失败",
                    "compliance_comment": "评分失败",
                    "strategy_comment": "评分失败",
                    "overall_advice": f"评分异常: {str(e)}",
                })


# ==========================================
# 终极评估报告生成
# ==========================================
async def generate_final_report(
    session_id: str,
    persona_id: str,
    conversation_history: list,
    evaluations: list,
    final_stage: str,
    turn_count: int,
    strategy_id: str = None,
) -> dict:
    """
    生成终极评估报告，包含底线惩罚机制和更长对话回溯。
    """
    import json
    from openai import AsyncOpenAI

    persona = PERSONAS.get(persona_id, {})

    # ---- 1. 汇总评分与惩罚逻辑 ----
    valid_evals = [e for e in evaluations if e.get("professionalism_score", -1) >= 0]
    if not valid_evals:
        return {"error": "没有有效的评分数据"}

    avg_prof = sum(e["professionalism_score"] for e in valid_evals) / len(valid_evals)
    avg_comp = sum(e["compliance_score"] for e in valid_evals) / len(valid_evals)
    avg_strat = sum(e["strategy_score"] for e in valid_evals) / len(valid_evals)
    
    # 致命错误“一票否决”机制：如果有任何一轮合规低于5分，最终平均分和合规分将被重罚
    critical_compliance_fails = [e for e in valid_evals if e["compliance_score"] <= 5]
    critical_prof_fails = [e for e in valid_evals if e["professionalism_score"] <= 5]
    
    if critical_compliance_fails:
        avg_comp = min(avg_comp, 5.0)  # 合规均分封顶 5.0
    if critical_prof_fails:
        avg_prof = min(avg_prof, 6.0)

    avg_total = round((avg_prof + avg_comp + avg_strat) / 3, 1)
    
    avg_prof = round(avg_prof, 1)
    avg_comp = round(avg_comp, 1)
    avg_strat = round(avg_strat, 1)

    # 收集每轮评语
    turn_comments = []
    for e in valid_evals:
        turn_comments.append(
            f"第{e.get('turn', '?')}轮: 专业{e['professionalism_score']}分({e.get('professionalism_comment', '')[:40]}) "
            f"合规{e['compliance_score']}分({e.get('compliance_comment', '')[:40]}) "
            f"策略{e['strategy_score']}分({e.get('strategy_comment', '')[:40]})"
        )

    # 构建更长的对话摘要（最多50条，确保能看到破冰期的核心破茧）
    dialogue_summary = []
    for i, msg in enumerate(conversation_history):
        role_label = "销售" if msg.get("role") == "sales" else "客户"
        content = msg.get("content", "")[:200]
        dialogue_summary.append(f"{role_label}: {content}")

    # ---- 2. LLM 生成总监点评 + 雷达图数据 ----
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    fatal_warning = ""
    if critical_compliance_fails or critical_prof_fails:
         fatal_warning = "\n⚠️【重要提醒】这位销售在过程中出现了严重的“合规短板（造假/违规承诺等）”或“数据事实错误”。最终评价中必须对此类致命错误提出极其严厉的批评和降级！不能仅仅简单看平均分！"

    prompt = f"""你是保险销售总监。请结合每轮考官评分明细，对这位销售的一整局对练表现做出专业的终极评估。

【客户画像】
{persona.get('name', '未知')} | {persona.get('demographics', '未知')}
态度: {persona.get('insurance_awareness', '未知')} | 关注: {persona.get('core_focus', '未知')}

【对话结局】{final_stage} | 共{turn_count}轮

【各轮考官评分汇总】
{chr(10).join(turn_comments)}

平均分: 专业{avg_prof} | 合规{avg_comp} | 策略{avg_strat} | 综合{avg_total}
{fatal_warning}

【对话全文摘要】
{chr(10).join(dialogue_summary[-50:])}

请输出以下 JSON，包含两部分：

1. "review": 一段400-500字的总监综合点评，要求：
   - 开头总结本局表现的整体评价（优秀/良好/及格/需改进）
   - 分析3个做得好的亮点
   - 指出3个需要改进的问题（具体到哪一轮、说了什么话）
   - 给出2-3条可操作的改进建议
   - 结尾给出一句总结性的鼓励或鞭策

2. "radar": 6个维度的评分（0-10），基于整局表现综合判断：
   - communication: 沟通技巧（表达清晰度、倾听能力、共情力）
   - product_knowledge: 产品熟悉度（保费/条款/核保规则的准确性）
   - compliance: 合规意识（健康告知、不违规承诺）
   - objection_handling: 异议处理能力（面对质疑的应对水平）
   - needs_analysis: 需求挖掘（是否精准抓到客户痛点）
   - closing: 促成能力（推动决策的节奏和技巧）

输出格式：
{{
  "review": "400-500字的总监综合点评...",
  "radar": {{
    "communication": 8,
    "product_knowledge": 7,
    "compliance": 9,
    "objection_handling": 6,
    "needs_analysis": 7,
    "closing": 5
  }}
}}"""

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={'type': 'json_object'},
            temperature=0.3,
        )
        content = response.choices[0].message.content
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        llm_result = json.loads(content)
    except Exception as e:
        print(f"❌ [终极报告] LLM 生成失败: {e}")
        traceback.print_exc()
        llm_result = {
            "review": f"报告生成失败: {str(e)}",
            "radar": {
                "communication": avg_strat,
                "product_knowledge": avg_prof,
                "compliance": avg_comp,
                "objection_handling": avg_strat,
                "needs_analysis": avg_strat,
                "closing": avg_strat,
            }
        }

    # ---- 3. 组装最终报告 ----
    radar = llm_result.get("radar", {})
    radar_labels = {
        "communication": "沟通技巧",
        "product_knowledge": "产品熟悉度",
        "compliance": "合规意识",
        "objection_handling": "异议处理",
        "needs_analysis": "需求挖掘",
        "closing": "促成能力",
    }

    report = {
        "session_id": session_id,
        "persona_name": persona.get("name", "未知"),
        "final_stage": final_stage,
        "turn_count": turn_count,
        "strategy_id": strategy_id,
        # 汇总分数
        "avg_scores": {
            "professionalism": avg_prof,
            "compliance": avg_comp,
            "strategy": avg_strat,
            "total": avg_total,
        },
        # 各轮明细
        "per_turn_scores": [
            {
                "turn": e.get("turn", "?"),
                "professionalism": e["professionalism_score"],
                "compliance": e["compliance_score"],
                "strategy": e["strategy_score"],
                "advice": e.get("overall_advice", ""),
            }
            for e in valid_evals
        ],
        # 总监点评
        "review": llm_result.get("review", ""),
        # 雷达图数据
        "radar": {
            "labels": list(radar_labels.values()),
            "keys": list(radar_labels.keys()),
            "scores": [radar.get(k, 5) for k in radar_labels.keys()],
        },
    }

    print(f"✅ [终极报告] 生成完成: 综合{avg_total}分, 6维雷达图已输出")
    return report
