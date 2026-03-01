# 文件：routers/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
# 引入我们刚刚编译好的图！
from services.agent_service import app_graph

router = APIRouter(prefix="/api/ai", tags=["智能体对话"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat_dual")
async def chat_with_dual_agent(request: ChatRequest):
    """测试双 Agent 骨架的接口 (带有上下文记忆)"""

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "current_stage": "需求分析阶段",
        "latest_evaluation": ""
    }

    # 核心魔法：加上 thread_id！只要这个 ID 不变，它就会去记忆体里捞历史记录
    config = {"configurable": {"thread_id": "boss_battle_001"}}

    # 把 config 传进去
    result = app_graph.invoke(initial_state, config=config)

    print(f"🧠 当前记忆库里的消息总数: {len(result['messages'])}")

    return {
        "customer_reply": result["messages"][-1].content,
        "evaluator_score": result["latest_evaluation"]
    }