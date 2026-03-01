# 文件：app/agents/evaluator.py
"""独立考官 Agent — 异步三维度评分，不阻塞主流程"""
import json
import traceback
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from app.core.config import LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, PERSONAS
from app.services.session_manager import session_manager


# ==========================================
# 评分结构化模型
# ==========================================
class EvaluationResult(BaseModel):
    professionalism_score: int = Field(description="专业性得分 (0-10分)")
    compliance_score: int = Field(description="合规性得分 (0-10分)")
    strategy_score: int = Field(description="销售策略得分 (0-10分)")
    professionalism_comment: str = Field(description="专业性点评")
    compliance_comment: str = Field(description="合规性点评")
    strategy_comment: str = Field(description="销售策略点评")
    overall_advice: str = Field(description="一句话改进建议")


# ==========================================
# 考官 LLM（独立实例，不和客户Agent共享）
# ==========================================
evaluator_llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)


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
    对一轮对话进行三维度评分，并将结果存入 SessionManager。
    此函数由 FastAPI BackgroundTasks 在后台异步执行。
    """
    persona = PERSONAS.get(persona_id, {})
    max_retries = 3

    print(f"\n⚖️ [考官] 开始后台评分: 会话={session_id}, 第{turn_count}轮")

    evaluator_prompt = f"""你是一位资深的保险销售总监兼合规审查员。
请对以下这轮【保险代理人（销售）】与【客户】的对话进行严格打分。

【客户背景画像】
身份：{persona.get('demographics', '未知')}
性格与痛点：{persona.get('insurance_awareness', '未知')}，最关心{persona.get('core_focus', '未知')}。
隐藏机密：{persona.get('hidden_secrets', '无')}

【当前一轮对话记录】
销售（代理人）说：{sales_msg}
客户的反应是：{customer_reply}

【判卷标准】
1. 专业性 (0-10分)：销售有没有胡编乱造产品规则？是否准确解释了保险条款？
2. 合规性 (0-10分)：销售有没有违规承诺（如"什么病都能赔"、"隐瞒没事"）？如果有，直接低分！
3. 销售策略 (0-10分)：面对这个客户画像，销售话术是否精准切入痛点？是否生硬推销？

请严格按以下 JSON 格式输出，不要用 markdown 包裹：
{{
  "professionalism_score": 8,
  "compliance_score": 9,
  "strategy_score": 5,
  "professionalism_comment": "具体评价",
  "compliance_comment": "具体评价",
  "strategy_comment": "具体评价",
  "overall_advice": "一句话建议"
}}"""

    for attempt in range(max_retries):
        try:
            structured_llm = evaluator_llm.with_structured_output(
                EvaluationResult, method="json_mode"
            )
            result: EvaluationResult = structured_llm.invoke(evaluator_prompt)

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
            return

        except Exception as e:
            print(f"⚠️ [考官] 第{attempt + 1}次评分失败: {e}")
            if attempt < max_retries - 1:
                print(f"   🔄 重试中...")
            else:
                print(f"❌ [考官] 第{turn_count}轮评分彻底失败，放弃。")
                traceback.print_exc()
                # 存储一个错误记录
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
