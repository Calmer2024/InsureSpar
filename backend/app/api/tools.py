# 文件：app/api/tools.py
"""用户工具箱 API — 将 AI 使用的工具开放给前端用户"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.tools.rag_tool import search_insurance_knowledge
from app.tools.calculators import query_premium_rate, query_cash_value

router = APIRouter(prefix="/api/tools", tags=["🧰 用户工具箱"])


# ==========================================
# 请求模型
# ==========================================
class SearchRulesRequest(BaseModel):
    query: str = Field(..., description="自然语言查询，例如'收缩压150能投保吗'")

class PremiumRateRequest(BaseModel):
    age: int = Field(..., description="投保年龄 (0-70)")
    gender: str = Field(..., description="性别: '男' 或 '女'")
    pay_period: int = Field(..., description="交费期: 1, 3, 5, 10, 15, 20, 25, 30")
    base_amount: int = Field(500000, description="基本保额，默认50万")

class CashValueRequest(BaseModel):
    gender: str = Field(..., description="性别: '男' 或 '女'")
    age: int = Field(..., description="投保时年龄 (0-70)")
    pay_period: int = Field(..., description="交费期: 1, 3, 5, 10, 15, 20, 25, 30")
    year: int = Field(..., description="保单年度，如第15年退保填15")
    base_amount: int = Field(500000, description="基本保额，默认50万")


# ==========================================
# 接口
# ==========================================
@router.post("/search-rules", summary="条款规则检索", description="使用 RAG 混合检索查询保险条款和规则")
async def api_search_rules(req: SearchRulesRequest):
    result = search_insurance_knowledge.invoke({"query": req.query})
    return {"result": result}


@router.post("/premium-rate", summary="保费费率查询", description="根据年龄、性别、交费期和保额查询保费")
async def api_premium_rate(req: PremiumRateRequest):
    result = query_premium_rate.invoke({
        "age": req.age,
        "gender": req.gender,
        "pay_period": req.pay_period,
        "base_amount": req.base_amount,
    })
    return {"result": result}


@router.post("/cash-value", summary="现金价值查询", description="查询指定年度的退保现金价值")
async def api_cash_value(req: CashValueRequest):
    result = query_cash_value.invoke({
        "gender": req.gender,
        "age": req.age,
        "pay_period": req.pay_period,
        "year": req.year,
        "base_amount": req.base_amount,
    })
    return {"result": result}
