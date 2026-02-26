# 文件位置：routers/chat.py
import json

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from services.agent_service import agent_executor
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/ai", tags=["智能体对话"])


# 接收前端传来的消息
class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """把用户的话丢给 LangGraph 处理，并返回结果"""

    # 1. 构造发给 LangGraph 的消息体
    inputs = {"messages": [HumanMessage(content=request.message)]}

    # 2. 运行图 (Graph)！
    # invoke 会让 AI 开始思考，如果需要算乘法，它会自动停下来调用 multiply_calculator，
    # 把结果拿回来后，再继续思考，直到得出最终结论。
    result = agent_executor.invoke(inputs)

    # 3. 提取 AI 的最终回答 (在 messages 列表的最后一个)
    final_reply = result["messages"][-1].content

    return {"reply": final_reply}


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    黑盒终结者：不仅流式输出文字，还实时直播 AI 的心理活动和工具调用！
    """

    # 这是一个异步生成器函数
    async def event_generator():
        inputs = {"messages": [HumanMessage(content=request.message)]}

        # astream_events(version="v2") 是 LangChain 最强大的内部监听器！
        # 它会把整个黑盒子里发生的所有事情，像广播一样实时发出来。
        async for event in agent_executor.astream_events(inputs, version="v2"):
            kind = event["event"]

            # 1. 监听工具调用的时刻 (AI 决定用计算器了)
            if kind == "on_tool_start":
                tool_name = event["name"]
                tool_args = event["data"].get("input")
                # 往前端推送系统消息
                msg = {"type": "system", "content": f"\n[⚙️ 正在调用工具: {tool_name}, 参数: {tool_args}]...\n"}
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

            # 2. 监听工具返回结果的时刻
            elif kind == "on_tool_end":
                tool_result = event["data"].get("output")
                msg = {"type": "system", "content": f"[✅ 工具返回结果: {tool_result}]\n"}
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

            # 3. 监听大模型打字的时刻 (真正实现打字机效果)
            elif kind == "on_chat_model_stream":
                # 提取出每一个字 (Token)
                chunk = event["data"]["chunk"].content
                if chunk:
                    msg = {"type": "text", "content": chunk}
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

    # 使用 StreamingResponse 返回，指定媒体类型为 event-stream
    return StreamingResponse(event_generator(), media_type="text/event-stream")