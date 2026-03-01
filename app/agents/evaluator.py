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
async def _extract_fact_claims(sales_msg: str) -> FactClaimsExtraction:
    """让 LLM 从销售话术中提取所有事实性声明"""
    import json
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    system_prompt = """你是一个事实核查助手。请分析销售话术，提取其中可以被数据核实的事实性声明。
请严格按以下 JSON 格式输出（必须包含所有字段）：

EXAMPLE JSON OUTPUT:
{
  "has_premium_claim": true,
  "premium_details": "45岁男性，20年交，10万保额，声称每年保费4800元",
  "has_cash_value_claim": false,
  "cash_value_details": "",
  "has_rule_claim": true,
  "rule_query": "高血压能否投保",
  "summary": "销售声称45岁男性20年交10万保额每年4800元，并说高血压可以正常投保"
}"""

    user_prompt = f"""销售说："{sales_msg}"

请判断：
1. 销售是否提到了具体的保费金额？（如"每年交4800元"）
   - 如果有，提取涉及的年龄、性别、交费期、保额和声称的金额
2. 销售是否提到了现金价值/退保金额？（如"第10年退保能拿回3万"）
   - 如果有，提取涉及的性别、年龄、交费期、保单年度和声称的金额
3. 销售是否提到了保险条款、核保规则、理赔条件等？（如"高血压可以投保"、"等待期内也能赔"）
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
async def _verify_facts(claims: FactClaimsExtraction) -> str:
    """根据提取的声明，调用工具获取真实数据作为铁证"""
    evidence_parts = []

    # 1. 核查保费声明
    if claims.has_premium_claim and claims.premium_details:
        print(f"🔧 [考官取证] 正在核查保费声明...")
        try:
            # 尝试从描述中解析参数（用 LLM 辅助解析更可靠，这里用简单正则做 fallback）
            params = await _parse_premium_params(claims.premium_details)
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
            params = await _parse_cash_value_params(claims.cash_value_details)
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


async def _parse_premium_params(details: str) -> dict | None:
    """用 LLM 从自然语言描述中提取保费查询参数"""
    try:
        prompt = f"""从以下描述中提取保费查询参数，严格输出 JSON：
"{details}"

输出格式：
{{"age": 45, "gender": "男", "pay_period": 20, "base_amount": 100000}}"""

        structured = evaluator_llm.with_structured_output(PremiumParams, method="json_mode")
        result = structured.invoke(prompt)
        return {"age": result.age, "gender": result.gender,
                "pay_period": result.pay_period, "base_amount": result.base_amount}
    except Exception as e:
        print(f"    ⚠️ 保费参数解析失败: {e}")
        return None


async def _parse_cash_value_params(details: str) -> dict | None:
    """用 LLM 从自然语言描述中提取现金价值查询参数"""
    try:
        prompt = f"""从以下描述中提取现金价值查询参数，严格输出 JSON：
"{details}"

输出格式：
{{"gender": "男", "age": 45, "pay_period": 20, "year": 10, "base_amount": 100000}}"""

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
    persona_id: str
):
    """
    升级版考官：先取证，再评分。
    流程：提取事实声明 → 调用工具核查 → 带着铁证打分
    """
    persona = PERSONAS.get(persona_id, {})
    max_retries = 3

    print(f"\n{'='*50}")
    print(f"⚖️ [考官] 开始后台评分: 会话={session_id}, 第{turn_count}轮")
    print(f"{'='*50}")

    # ---- 阶段一：事实提取 ----
    claims = await _extract_fact_claims(sales_msg)

    # ---- 阶段二：工具核查 ----
    evidence = await _verify_facts(claims)

    # ---- 阶段三：带证据评分 ----
    import json
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    system_prompt = f"""你是一位资深的保险销售总监兼合规审查员。
请对【保险代理人（销售）】与【客户】的对话进行严格打分。

【判卷标准（务必结合下方事实核查报告！）】
1. 专业性 (0-10分)：
   - 如果「事实核查报告」显示销售报价/声明与实际数据不符，专业性最高不超过3分！
   - 如果销售曲解了保险条款或规则，专业性最高不超过2分！
   - 如果销售的说法与工具核查结果一致，给予肯定。
2. 合规性 (0-10分)：
   - 销售有没有违规承诺（如"什么病都能赔"、"隐瞒没事"）？如果有，直接低分！
   - 是否按照合规流程推进（如应询问健康告知却跳过）？
3. 销售策略 (0-10分)：
   - 面对这个客户画像，销售话术是否精准切入痛点？是否生硬推销？

请严格按以下 JSON 格式输出，**必须且只能**包含以下 7 个字段：
- professionalism_score (整数，0-10)
- compliance_score (整数，0-10)
- strategy_score (整数，0-10)
- professionalism_comment (字符串，专业性具体评价)
- compliance_comment (字符串，合规性具体评价)
- strategy_comment (字符串，销售策略具体评价，**绝不能遗漏此字段！**)
- overall_advice (字符串，一句话改进建议)

EXAMPLE JSON OUTPUT:
{{
  "professionalism_score": 8,
  "compliance_score": 9,
  "strategy_score": 5,
  "professionalism_comment": "具体评价（必须引用事实核查结果作为判分依据）",
  "compliance_comment": "未进行充分的健康告知",
  "strategy_comment": "话术生硬，未切中痛点。本评价必须存在。",
  "overall_advice": "下次注意询问病史"
}}"""

    user_prompt = f"""【客户背景画像】
身份：{persona.get('demographics', '未知')}
性格与痛点：{persona.get('insurance_awareness', '未知')}，最关心{persona.get('core_focus', '未知')}。
隐藏机密：{persona.get('hidden_secrets', '无')}

【当前一轮对话记录】
销售（代理人）说：{sales_msg}
客户的反应是：{customer_reply}

═══════════════════════════════════════
【🔍 事实核查报告（以下为系统自动调用工具取证的结果，是唯一的事实标准）】
{evidence}
═══════════════════════════════════════"""

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
            # 处理可能的 markdown code block
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
