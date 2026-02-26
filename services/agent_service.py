# 文件位置：services/agent_service.py
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator import multiply_calculator
import os

# 1. 初始化大模型 (指向 DeepSeek)
# 注意：DeepSeek-Chat (V3) 原生支持强大的 Tool Calling 能力！
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-e6a0efee40b14d7a84dc2b6af048bd7d"),
    base_url="https://api.deepseek.com",
    max_tokens=1024
)

# 2. 把我们写好的工具打包成列表
tools = [multiply_calculator]

# 3. 创建 LangGraph 智能体 (它内置了完整的状态机、循环推理和工具调用逻辑)
# 相当于封装好了一个具备“思考->行动->观察->回答”能力的机器人
agent_executor = create_react_agent(llm, tools)