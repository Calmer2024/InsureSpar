# 文件位置：tools/calculator.py
from langchain_core.tools import tool

# @tool 装饰器是核心！它会自动提取函数的注释（Docstring）和参数类型
# 喂给大模型，让大模型知道什么情况下该调用这个工具。
@tool
def multiply_calculator(a: float, b: float) -> float:
    """
    当你需要计算两个数字的乘积时，请调用此工具。
    参数 a: 第一个乘数
    参数 b: 第二个乘数
    """
    print(f"🔧 [系统日志] AI 正在悄悄调用计算器工具: {a} * {b}")
    return a * b