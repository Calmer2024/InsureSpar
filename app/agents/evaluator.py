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
class PremiumClaim(BaseModel):
    age: int = Field(description="年龄", default=0)
    gender: str = Field(description="性别", default="")
    pay_period: int = Field(description="交费期", default=0)
    base_amount: int = Field(description="保额", default=0)
    claimed_premium: str = Field(description="声称的保费金额", default="")
    target_insured: str = Field(description="被保人身份，如'本人'、'丈夫'、'孩子'")
    description: str = Field(description="完整陈述，如 '45岁男性，20年交，100万保额，声称每年保费43500元'")


class CashValueClaim(BaseModel):
    gender: str = Field(description="性别", default="")
    age: int = Field(description="年龄", default=0)
    pay_period: int = Field(description="交费期", default=0)
    year: int = Field(description="保单年度", default=0)
    base_amount: int = Field(description="保额", default=0)
    claimed_cash_value: str = Field(description="声称的金额", default="")
    description: str = Field(description="完整陈述，如 '第10年退保能拿回3万'")

class FactClaimsExtraction(BaseModel):
    """从销售话术中提取的事实性声明"""
    premium_claims: list[PremiumClaim] = Field(default_factory=list, description="提取到的所有保费声明")
    cash_value_claims: list[CashValueClaim] = Field(default_factory=list, description="提取到的所有现金价值/退保声明")
    has_rule_claim: bool = Field(description="销售是否提到了保险条款、核保规则、理赔门槛等")
    rule_query: str = Field(default="", description="如有规则声明，提取需核实的核心搜索词")
    summary: str = Field(description="简要概括销售本轮话术中的核心事实性声明")

def _build_mega_persona_anchor(persona: dict) -> str:
    """构建绝对静态的全家桶画像基座，用于 Prompt Caching 首部锚定"""
    import json
    # 只提取不会随对话轮数变化的静态信息
    static_info = {
        "Name": persona.get("name", "未知"),
        "Demographics": persona.get("demographics", "未知"),
        "Health_Status": persona.get("health_status", "未知"),
        "Financial_Status": persona.get("financial_status", "未知"),
        "Insurance_Awareness": persona.get("insurance_awareness", "未知"),
        "Risk_Preference": persona.get("risk_preference", "未知"),
        "Hidden_Secrets_DO_NOT_DISCLOSE": persona.get("hidden_secrets", "无")
    }
    return f"【客户绝对静态画像基座】\n```json\n{json.dumps(static_info, ensure_ascii=False, indent=2)}\n```\n⚠️该基座包含客户本人及潜在涉及家庭成员的全局设定，提取事实或打分时，务必从此处读取固定属性以填补缺失信息。"


class EvaluationResult(BaseModel):
    professionalism_score: int = Field(description="专业性得分 (0-10分)")
    compliance_score: int = Field(description="合规性得分 (0-10分)")
    strategy_score: int = Field(description="销售策略得分 (0-10分)")
    professionalism_comment: str = Field(description="专业性点评")
    compliance_comment: str = Field(description="合规性点评")
    strategy_comment: str = Field(description="销售策略点评")
    overall_advice: str = Field(
        description="给销售的下一步改进建议。要求：1. 必须限制在50字以内；2. 一针见血，直接指出下一步行动点，不要写长篇示范话术。")


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
async def _extract_fact_claims(sales_msg: str, customer_reply: str, recent_context: str = "", persona: dict = None) -> FactClaimsExtraction:
    """让 LLM 从销售话术中提取所有事实性声明，结合最近的上下文和Mega-Persona"""
    import json
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    persona_anchor = _build_mega_persona_anchor(persona or {})

    # [静态系统Prompt区] 高阶复杂Schema预热
    system_prompt = f"""你是一个严谨的事实核查助手。
    
{persona_anchor}

请仔细阅读【对话历史】以及本轮的话术，提取销售话语中所有可以被数据核实的事实性声明。
支持提取家庭组合方案，即如果销售同时给丈夫和妻子报价，你需要提取多个 premium_claims。

请严格按以下 JSON 格式输出：
{{
  "premium_claims": [
    {{
      "age": 45,
      "gender": "男",
      "pay_period": 20,
      "base_amount": 1000000,
      "claimed_premium": "43500元",
      "description": "45岁男性，20年交，100万保额，声称每年保费43500元"
    }}
  ],
  "cash_value_claims": [],
  "has_rule_claim": true,
  "rule_query": "高血压能否投保",
  "summary": "为45岁男性报价100万重疾险保费43500元，并解释高血压投保规则"
}}
如果保额、年龄、性别等要素本轮未提及，**必须**从上方的【客户绝对静态画像基座】或下方的【对话历史】中推断并坚决填入数字，不要填null。"""

    # [动态尾部隔离] 增量对话与本轮话术放在 User Prompt 尾部
    user_prompt = f"""【对话历史】
{recent_context}

【本轮待核单词】
销售说："{sales_msg}"
客户回应："{customer_reply}"

请提取事实性声明。"""

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
async def _verify_facts(claims: FactClaimsExtraction) -> str:
    """根据提取的声明，直接调用底层工具进行计算，无需再次经过LLM解析参数"""
    evidence_parts = []

    # 1. 核查保费声明 (List)
    for claim in claims.premium_claims:
        print(f"🔧 [考官取证] 正在核查保费声明: {claim.description}")
        try:
            if not all([claim.age, claim.gender, claim.pay_period, claim.base_amount]):
                evidence_parts.append(f"⚠️ 【保费核查失败】由于缺少年龄、性别、缴费期或保额中的某项参数，无法验证保费：{claim.description}。请提醒销售必须明确这些前提。")
                continue
            
            # 由于Schema Pre-warming，直接提取强类型参数调用工具
            actual_result = query_premium_rate.invoke({
                "age": claim.age,
                "gender": claim.gender,
                "pay_period": claim.pay_period,
                "base_amount": claim.base_amount
            })
            evidence_parts.append(
                f"📊 【保费核查】\n"
                f"  销售声称：{claim.description}\n"
                f"  考官查得的实际数据：{actual_result}\n"
                f"  ⚠️ 如果销售报价与实际数据不一致，说明严重算错数！"
            )
            print(f"  ✅ 保费核查完成")
        except Exception as e:
            print(f"  ⚠️ 保费核查异常: {e}")

    # 2. 核查现金价值声明 (List)
    for cv_claim in claims.cash_value_claims:
        print(f"🔧 [考官取证] 正在核查现金价值声明: {cv_claim.description}")
        try:
            if not all([cv_claim.age, cv_claim.gender, cv_claim.pay_period, cv_claim.year, cv_claim.base_amount]):
                evidence_parts.append(f"⚠️ 【现金价值核查失败】由于缺少参数，无法验证：{cv_claim.description}。")
                continue

            actual_result = query_cash_value.invoke({
                "gender": cv_claim.gender,
                "age": cv_claim.age,
                "pay_period": cv_claim.pay_period,
                "year": cv_claim.year,
                "base_amount": cv_claim.base_amount
            })
            evidence_parts.append(
                f"📊 【现金价值核查】\n"
                f"  销售声称：{cv_claim.description}\n"
                f"  考官查得的实际数据：{actual_result}\n"
                f"  ⚠️ 如果缺口过大或数字对不上，说明销售虚假演示！"
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


# 移除 _parse_premium_params 和 _parse_cash_value_params 
# 因为 Schema Pre-warming 已经让我们在提取 Claims 的时候就拿到了强类型数字。


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
    claims = await _extract_fact_claims(sales_msg, customer_reply, recent_context, persona)

    # ---- 阶段二：工具核查 ----
    evidence = await _verify_facts(claims)

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
    
    # 构建静态画像基座
    persona_anchor = _build_mega_persona_anchor(persona)

    # 构造历史对话日志，其中包含教练过往的旁白建议 (Feedback Ledger)
    ledger_parts = []
    if conversation_history:
        for msg in conversation_history:
            r = msg.get("role", "")
            if r == "sales":
                ledger_parts.append(f"销售：{msg.get('content')}")
            elif r == "customer":
                ledger_parts.append(f"客户：{msg.get('content')}")
            elif r == "coach":
                ledger_parts.append(f"🎯 [教练旁白指导销售]：{msg.get('content')}")
    history_ledger = "\n".join(ledger_parts)

    # 【动态尾部隔离】将静态的画像与跨维度连坐惩罚矩阵 (Cross-Penalty Matrix) 放在 System Prompt，
    # 动态的文本 (RAG Evidence / 本轮话术 / 上下文) 放于 User Prompt 尾部。
    
    system_prompt = f"""你是绝对严苛且逻辑自洽的保险销售考官。
    
{persona_anchor}

【跨维度连坐惩罚矩阵 (Cross-Penalty Matrix)】
1. 熔断法则 1（数字造假）：如果在比较“考官独立事实核查报告”与“销售发言”时，发现销售给出的保费、现金价值计算出错，导致专业性得分(professionalism_score) ≤ 3，则必须严惩误导行为，强制令合规性得分(compliance_score) ≤ 5。
2. 熔断法则 2（虚假承诺）：如果销售为了促单凭空编造核保/理赔通过率（如“哪怕患重病也包赔”），合规性必须 ≤ 3。
3. 动态宽限期：如果处于【破冰与探寻】阶段，未做深度需求挖掘不扣合规分。如果在【异议处理/核保】阶段回避客户对于条款的直接疑问，专业分扣除 3 分。

【判卷维度 (0-10)】
1. 专业性：用语是否准确专业。数据事实（保费等）与工具核查是否一致？造假≤3分。
2. 合规性：是否存在违背常理、误导、隐瞒的陈述？
3. 策略性：结合当前阶段，话术或破局策略是否得当？

输出必须包含以下7个JSON字段，分数必须是纯数字：
{{"professionalism_score":8,"compliance_score":9,"strategy_score":5,"professionalism_comment":"评价","compliance_comment":"评价","strategy_comment":"评价","overall_advice":"具体、一针见血的建议，告诉销售下一句应该怎么改"}}"""

    user_prompt = f"""【阶段信息】
目前所处环节：【{current_stage}】

【增长式对话台账 (含教练历史旁白)】
{history_ledger}

【动态尾部：核心核查对象】
本轮最新的销售执行动作：
销售说：{sales_msg[:500]}
客户反应：{customer_reply[:300]}
{sales_tool_evidence}

【🔍 考官独立事实核查报告】
{evidence}

【策略灵活性原则】
[教练旁白] 仅作为参考建议。你需要评估销售真实的发言是否有效地推进了当前阶段（如：是否安抚了情绪、是否用数据化解了异议、是否自然过渡到下个阶段）。
如果销售没有采用教练的建议，但使用了自己合理且有效的沟通策略，**不得扣减策略分**。只有当销售完全回避客户核心痛点、或者话术逻辑混乱时才扣分。"""

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
