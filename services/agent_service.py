# 文件：services/agent_service.py
import os
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# 引入我们刚刚写的假工具
from tools.insurance_tools import search_insurance_rules, query_cash_value, query_premium_rate
from langgraph.prebuilt import ToolNode

from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver


# ==========================================
# 新增：定义对话状态跟踪器
# ==========================================
class DialogueStateUpdate(BaseModel):
    current_stage: str = Field(
        description="当前对话所处的阶段，必须严格输出以下四个之一：'破冰与探寻', '产品介绍', '异议处理', '促成决策'"
    )
    reasoning: str = Field(description="判断该阶段的理由，简短说明即可")


# ==========================================
# 新增：定义考官的“判卷答题卡”结构
# ==========================================
class EvaluationResult(BaseModel):
    professionalism_score: int = Field(description="专业性得分 (0-10分)，评估销售是否准确解释了产品规则、健康告知等。")
    compliance_score: int = Field(description="合规性得分 (0-10分)，评估销售是否有误导、隐瞒或违规承诺（如乱说都能赔）。")
    strategy_score: int = Field(description="销售策略得分 (0-10分)，评估销售是否挖掘了客户痛点，是否命中客户关注点。")

    professionalism_comment: str = Field(alias="professional_comment",
                                         description="专业性点评，指出哪里说对了，哪里说错了。")
    compliance_comment: str = Field(description="合规性点评，如果发现违规行为，严厉指出！如果没有，给予肯定。")
    strategy_comment: str = Field(description="销售策略点评，评价其应对客户异议或探寻需求的话术技巧。")

    overall_advice: str = Field(description="给销售代理人的一句话综合改进建议。")


# ==========================================
# 1. 定义系统共享状态 (黑板)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_stage: str
    latest_evaluation: str


# ==========================================
# 2. 初始化大模型与工具
# ==========================================
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-e6a0efee40b14d7a84dc2b6af048bd7d")  # 记得换秘钥
)
tools = [search_insurance_rules, query_premium_rate, query_cash_value]
llm_with_tools = llm.bind_tools(tools)

# 把你设计的画像定义在上面
HARD_BOSS_PERSONA = {
    "demographics": "45岁，男，私企老板，年收入100万",
    "health_status": "有3年高血压史（收缩压150），轻度脂肪肝。近期经常头晕。",
    "financial_status": "有500万企业贷款，现金流紧张",
    "insurance_awareness": "极度不信任保险，觉得保险'这不赔那不赔，全都是骗人的文字游戏'。",
    "risk_preference": "激进，觉得钱在自己手里投资赚得更多。",
    "core_focus": "理赔门槛（能不能赔）、资金灵活性（中途能不能退保取钱）。",
    "communication_style": "喜欢反问弄清楚所有东西。回复字数尽量简短，不要长篇大论。",
    "hidden_secrets": "【绝对机密】你绝对不会主动说出自己有高血压和经常头晕的事情！除非销售极其专业地、反复地询问既往病史，你才会含糊其辞地透露一点点。如果销售不问，你就一直隐瞒。"
}

TECH_SAVVY_CLIENT_PERSONA = {
    "demographics": "38岁，男，IT公司技术总监，年收入120万",
    "health_status": "轻度腰椎间盘突出，偶尔熬夜后心悸，体检显示血脂略偏高",
    "financial_status": "有房贷200万，但现金流充裕，主要资产在股票和基金中",
    "insurance_awareness": "研究过一些保险产品，认为保险收益率低，不如自己投资，但对保障功能持保留态度",
    "risk_preference": "理性计算型，喜欢对比数据，认为风险可通过资产配置分散",
    "core_focus": "条款细节（免责条款、理赔定义）、现金价值增长曲线、退保损失、实际收益率IRR",
    "communication_style": "提问多且细，喜欢打断并要求解释逻辑，对模糊表述敏感，语气平静但带有质疑",
    "hidden_secrets": "【绝对机密】除非销售详细询问健康告知并解释影响，否则不会主动提及自己的腰椎和心悸问题，认为这些不影响"
}

Customer = TECH_SAVVY_CLIENT_PERSONA


# ==========================================
# 3. 定义节点 (演员) - 更新了客户的灵魂！
# ==========================================
def customer_node(state: AgentState):
    print("👤 [流程流转] -> 轮到客户 Agent (挑剔老板) 思考...")
    stage = state.get("current_stage", "破冰阶段")

    # 核心魔法：将 JSON 转化为极具压迫感的 System Prompt
    sys_prompt_content = f"""你正在参与一场真实的健康险销售对练。请你完美扮演以下客户，绝不能暴露你是AI。

【你的基本信息】
身份：{Customer['demographics']}
财务状况：{Customer['financial_status']}
健康状况：{Customer['health_status']}

【你的性格与认知】
对待保险的态度：{Customer['insurance_awareness']}
风险偏好：{Customer['risk_preference']}
最关心的问题：{Customer['core_focus']}

【绝对行为准则（你必须严格遵守）】
1. 沟通风格：{Customer['communication_style']}
2. 核心机密：{Customer['hidden_secrets']}
3. 场景约束：当前对话处于【{stage}】阶段。
4. 动作要求：如果销售提到特定的保险条款或规则你不懂，请悄悄调用工具查询，绝不能瞎编。

注意：请直接以第一人称（我）与销售对话，输出你的真实反应，不要带任何前缀或内心OS。"""

    # 生成系统提示词
    sys_prompt = SystemMessage(content=sys_prompt_content)

    # 拼接历史对话发送给大模型
    messages_to_send = [sys_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_send)

    return {"messages": [response]}


# ==========================================
# 4. 定义节点 (演员) - 更新了真实的考官！
# ==========================================
def evaluator_node(state: AgentState):
    print("⚖️ [流程流转] -> 轮到考官 Agent 开始真实判卷...")

    # 【改动在这里】：倒序查找最后一个真实用户的发言和最后一个 AI 的文本回复
    human_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    ai_msg = next((m for m in reversed(state["messages"]) if m.type == "ai" and m.content), None)

    sales_msg = human_msg.content if human_msg else ""
    customer_reply = ai_msg.content if ai_msg else "（客户只调用了工具，未回复文本）"
    # 2. 构造铁面考官的 System Prompt
    evaluator_prompt = f"""你是一位资深的保险销售总监兼合规审查员。
    你的任务是对下面这轮【保险代理人（销售）】与【客户】的最新对话进行严格打分。

    【客户背景画像】
    身份：{HARD_BOSS_PERSONA['demographics']}
    性格与痛点：{HARD_BOSS_PERSONA['insurance_awareness']}，最关心{HARD_BOSS_PERSONA['core_focus']}。
    隐藏机密：{HARD_BOSS_PERSONA['hidden_secrets']}

    【最新一轮对话记录】
    销售（代理人）说：{sales_msg}
    客户的反应是：{customer_reply}

    【判卷标准】
    1. 专业性：销售有没有胡编乱造产品规则？
    2. 合规性：销售有没有违规承诺（例如“什么病都能赔”、“你隐瞒一下没事”）？如果有，合规性直接打低分！
    3. 销售策略：面对这个极其挑剔且有贷款压力的老板，销售的话术有没有切中要害？是不是在生硬推销？

⚠️ 警告：请严格按照以下 JSON 格式输出，必须使用指定的英文 Key，且 value 的数据类型必须与示例完全一致！绝对不要有任何多余的 Markdown 标记（不要用 ```json 包裹）：
    {{
      "professionalism_score": 8,
      "compliance_score": 9,
      "strategy_score": 5,
      "professionalism_comment": "这里填写对专业性的具体评价文字",
      "compliance_comment": "这里填写对合规性的具体评价文字",
      "strategy_comment": "这里填写对销售策略的具体评价文字",
      "overall_advice": "这里填写总监给销售的一句话最终建议"
    }}"""

    # 3. 让大模型强制输出 JSON 结构！
    # 强制告诉 LangChain 使用 json_mode，而不是默认的 json_schema 或函数调用
    structured_llm = llm.with_structured_output(EvaluationResult, method="json_mode")
    # 4. 调用大模型进行判卷
    # 注意：这里我们单独发一个请求给大模型，不要和客户Agent的对话历史混在一起
    result: EvaluationResult = structured_llm.invoke(evaluator_prompt)

    # 5. 把结构化的对象转换成好看的 Markdown 文本存入黑板
    final_score_text = f"""
### 📊 实时考评结果
- **专业性**: {result.professionalism_score}/10  | 💬 {result.professionalism_comment}
- **合规性**: {result.compliance_score}/10  | 💬 {result.compliance_comment}
- **销售策略**: {result.strategy_score}/10  | 💬 {result.strategy_comment}

💡 **总监建议**: {result.overall_advice}
"""
    print(f"✅ 判卷完成！总监建议: {result.overall_advice}")
    return {"latest_evaluation": final_score_text}


# ==========================================
# 3.0 定义节点：对话管理员 (状态跟踪)
# ==========================================
def dialogue_manager_node(state: AgentState):
    print("🚦 [状态跟踪] -> 正在分析当前对话处于哪个阶段...")

    # 获取最新的销售发言
    human_msg = next((m for m in reversed(state["messages"]) if m.type == "human"), None)
    sales_msg = human_msg.content if human_msg else ""

    # 构造意图识别 Prompt，必须包含 "json" 字样和输出样例！
    tracker_prompt = f"""你是一个智能对话状态跟踪器。请分析保险销售刚刚说的这句话，判断当前的销售环节。
    销售说："{sales_msg}"

    可选阶段：
    1. 破冰与探寻：销售在寒暄、拉家常、询问健康/财务状况。
    2. 产品介绍：销售开始明确提到具体保险产品、保障范围、价格等。
    3. 异议处理：销售在试图解答客户此前提出的质疑（如太贵、不赔等）。
    4. 促成决策：销售在催促签单、要求支付、逼单。

    请严格按照以下 JSON 格式输出结果：
    {{
      "current_stage": "填入上述四个阶段之一",
      "reasoning": "简短说明判断理由"
    }}
    """

    # 强制输出结构化状态
    structured_llm = llm.with_structured_output(DialogueStateUpdate, method="json_mode")
    result: DialogueStateUpdate = structured_llm.invoke(tracker_prompt)

    print(f"📌 [状态更新] -> 对话已切入：【{result.current_stage}】 (理由: {result.reasoning})")

    # 把最新的状态写入黑板，覆盖之前的状态
    return {"current_stage": result.current_stage}


# ==========================================
# 4. 编排图并导出 (供 Controller 调用)
# ==========================================
workflow = StateGraph(AgentState)

# 1. 添加所有节点（加入官方的 ToolNode 来自动执行工具）
tool_node = ToolNode(tools)
workflow.add_node("dialogue_manager", dialogue_manager_node)
workflow.add_node("customer", customer_node)
workflow.add_node("tools", tool_node)
workflow.add_node("evaluator", evaluator_node)


# 2. 定义路由逻辑：客户思考完后，是去执行工具，还是去考官那里打分？
def route_customer(state: AgentState):
    last_message = state["messages"][-1]
    # 如果大模型返回了 tool_calls，说明它想用工具，必须把流程导向 tools 节点
    if last_message.tool_calls:
        print("🔀 [路由判定] -> 客户想查资料，导向 ToolNode...")
        return "tools"
    # 如果没调用工具（输出的是文本），就导向考官打分
    print("🔀 [路由判定] -> 客户回复完毕，导向考官打分...")
    return "evaluator"


# 3. 连接边
workflow.add_edge(START, "dialogue_manager")  # 流程从管理员开始
workflow.add_edge("dialogue_manager", "customer")  # 判定完状态后，交给客户思考

# 客户思考完后，进入条件路由分支
workflow.add_conditional_edges("customer", route_customer)

# 如果去了 tools 节点，工具执行完必须回到 customer 继续思考（客户拿到资料后要组织语言回话）
workflow.add_edge("tools", "customer")

workflow.add_edge("evaluator", END)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
