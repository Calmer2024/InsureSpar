# 文件：app/services/dashboard_service.py
"""Dashboard 数据聚合服务 — 从数据库中提取用户训练统计数据"""
import json
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from openai import AsyncOpenAI

from app.core.config import LLM_MODEL, LLM_BASE_URL, LLM_API_KEY
from app.models.models import SessionRecord, EvaluationRecord, FinalReportRecord


# ==========================================
# 1. Dashboard Overview — 个人概览
# ==========================================
def get_overview(db: Session) -> dict:
    """
    聚合用户训练总览：会话数、总训练时长、成交数、历史平均分。
    当前为单用户模式，查询全库。
    """
    # 会话统计
    total_sessions = db.query(func.count(SessionRecord.session_id)).scalar() or 0

    # 总训练时长（分钟）：Python 侧计算避免 SQL 方言兼容问题
    sessions_with_time = (
        db.query(SessionRecord.start_time, SessionRecord.end_time)
        .filter(SessionRecord.end_time.isnot(None), SessionRecord.start_time.isnot(None))
        .all()
    )
    total_duration_minutes = 0
    for s in sessions_with_time:
        delta = s.end_time - s.start_time
        total_duration_minutes += int(delta.total_seconds() / 60)

    # 成交次数：final_stage 包含 "成交" 或 "签单"
    deal_closed_count = (
        db.query(func.count(SessionRecord.session_id))
        .filter(SessionRecord.final_stage.like("%成交%"))
        .scalar()
    ) or 0

    # 历史平均分：所有有效评分的三维平均
    avg_scores = (
        db.query(
            func.avg(
                (EvaluationRecord.professionalism_score
                 + EvaluationRecord.compliance_score
                 + EvaluationRecord.strategy_score) / 3.0
            )
        )
        .filter(EvaluationRecord.professionalism_score >= 0)
        .scalar()
    )
    avg_score_all_time = round(float(avg_scores), 1) if avg_scores else 0.0

    # 用户信息（单用户模式硬编码，后续接入用户系统可替换）
    user_info = {
        "name": "学员",
        "rank": "销售代表",
        "avatar_url": "",
        "join_date": "2024-06-15",
    }

    # 如果有会话记录，用最早的会话时间作为 join_date
    earliest_session = (
        db.query(SessionRecord.start_time)
        .filter(SessionRecord.start_time.isnot(None))
        .order_by(SessionRecord.start_time)
        .first()
    )
    if earliest_session and earliest_session[0]:
        user_info["join_date"] = earliest_session[0].strftime("%Y-%m-%d")

    return {
        "user_info": user_info,
        "stats": {
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration_minutes,
            "deal_closed_count": deal_closed_count,
            "avg_score_all_time": avg_score_all_time,
        },
    }


# ==========================================
# 2. Dashboard Capabilities — 能力雷达 & 弱点诊断
# ==========================================
def get_capabilities(db: Session) -> dict:
    """
    聚合能力雷达图（最近的 final_reports 中 radar_data 平均）+ 弱点 Top3。
    """
    # 取最近 20 次有报告的会话的 radar_data
    reports = (
        db.query(FinalReportRecord)
        .join(SessionRecord, FinalReportRecord.session_id == SessionRecord.session_id)
        .filter(SessionRecord.is_finished == True)
        .order_by(desc(SessionRecord.end_time))
        .limit(20)
        .all()
    )

    # 默认雷达标签（与 evaluator.py 中 generate_final_report 对齐）
    default_labels = ["沟通技巧", "产品熟悉度", "合规意识", "异议处理", "需求挖掘", "促成能力"]
    default_keys = ["communication", "product_knowledge", "compliance", "objection_handling", "needs_analysis", "closing"]

    if not reports:
        return {
            "radar": {"labels": default_labels, "scores": [0] * 6},
            "weaknesses": [],
            "ai_general_review": "暂无训练数据，请先完成至少一次对练。",
        }

    # 解析 radar_data 并按维度求平均
    dim_scores = {k: [] for k in default_keys}
    for report in reports:
        radar_data = report.radar_data
        if not radar_data:
            continue
        # radar_data 可能为 dict 或 JSON 字符串
        if isinstance(radar_data, str):
            try:
                radar_data = json.loads(radar_data)
            except json.JSONDecodeError:
                continue

        # 支持两种格式：
        # 格式1: {"labels": [...], "keys": [...], "scores": [...]}
        # 格式2: {"communication": 8, "product_knowledge": 7, ...}
        if "keys" in radar_data and "scores" in radar_data:
            keys = radar_data["keys"]
            scores = radar_data["scores"]
            for k, s in zip(keys, scores):
                if k in dim_scores:
                    dim_scores[k].append(float(s))
        else:
            for k in default_keys:
                if k in radar_data:
                    dim_scores[k].append(float(radar_data[k]))

    # 计算各维度平均分
    avg_by_dim = {}
    for k in default_keys:
        vals = dim_scores[k]
        avg_by_dim[k] = round(sum(vals) / len(vals), 1) if vals else 0.0

    radar_scores = [avg_by_dim[k] for k in default_keys]

    # 弱点 Top3：取最低的 3 个维度
    sorted_dims = sorted(avg_by_dim.items(), key=lambda x: x[1])
    key_to_label = dict(zip(default_keys, default_labels))

    # 统计各维度的低分次数（低于6分视为低分）
    dim_low_freq = {k: 0 for k in default_keys}
    for report in reports:
        radar_data = report.radar_data
        if not radar_data:
            continue
        if isinstance(radar_data, str):
            try:
                radar_data = json.loads(radar_data)
            except json.JSONDecodeError:
                continue
        if "keys" in radar_data and "scores" in radar_data:
            for k, s in zip(radar_data["keys"], radar_data["scores"]):
                if k in dim_low_freq and float(s) < 6:
                    dim_low_freq[k] += 1
        else:
            for k in default_keys:
                if k in radar_data and float(radar_data[k]) < 6:
                    dim_low_freq[k] += 1

    weaknesses = []
    for k, score in sorted_dims[:3]:
        weaknesses.append({
            "dimension": key_to_label.get(k, k),
            "frequency": dim_low_freq.get(k, 0),
            "advice": "",  # 将由 LLM 生成综合点评覆盖
        })

    return {
        "radar": {"labels": default_labels, "scores": radar_scores},
        "weaknesses": weaknesses,
        "ai_general_review": "",  # 由 API 层异步填充
        # 内部传递给 LLM 的上下文
        "_avg_by_dim": avg_by_dim,
        "_key_to_label": key_to_label,
        "_reports_count": len(reports),
    }


# ==========================================
# 3. AI 综合点评 — LLM 调用
# ==========================================
async def generate_ai_general_review(
    capabilities_data: dict,
    overview_stats: dict,
) -> str:
    """
    调用 LLM 对用户近期训练表现做综合分析点评。
    """
    avg_by_dim = capabilities_data.get("_avg_by_dim", {})
    key_to_label = capabilities_data.get("_key_to_label", {})
    reports_count = capabilities_data.get("_reports_count", 0)
    weaknesses = capabilities_data.get("weaknesses", [])

    if not avg_by_dim:
        return "暂无足够数据生成综合分析。"

    # 构造能力摘要
    dim_summary = "\n".join([
        f"  - {key_to_label.get(k, k)}: {v}分"
        for k, v in avg_by_dim.items()
    ])
    weakness_summary = "\n".join([
        f"  - {w['dimension']}（低分出现{w['frequency']}次）"
        for w in weaknesses
    ]) if weaknesses else "  暂无明显弱项"

    prompt = f"""你是一位资深保险销售培训总监。请根据以下学员的训练数据，生成一段 100-150 字的综合诊断点评。

【训练概况】
- 已完成 {overview_stats.get('total_sessions', 0)} 次对练
- 分析基于最近 {reports_count} 次对练的评分数据
- 历史平均分: {overview_stats.get('avg_score_all_time', 0)}
- 成交次数: {overview_stats.get('deal_closed_count', 0)}

【各维度平均分】
{dim_summary}

【薄弱环节 Top3】
{weakness_summary}

要求：
1. 先用一句话总结整体水平
2. 指出最突出的优势（1个）
3. 指出最需改进的方面（1-2个），并给出具体练习建议
4. 语气专业但鼓励性，100-150字即可，不要使用 markdown 格式"""

    try:
        client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        review = response.choices[0].message.content.strip()
        print(f"✅ [Dashboard] AI 综合点评生成完成 ({len(review)}字)")
        return review
    except Exception as e:
        print(f"⚠️ [Dashboard] AI 综合点评生成失败: {e}")
        traceback.print_exc()
        return "AI 综合分析暂时不可用，请稍后重试。"


# ==========================================
# 4. Dashboard Growth — 成长趋势
# ==========================================
def get_growth_trend(db: Session, limit: int = 10) -> dict:
    """
    聚合最近 N 次已结束会话的分数趋势。
    x_axis: 会话完成日期
    series: total / professionalism / compliance / strategy
    """
    # 查询最近 N 次已结束、有评分的会话
    finished_sessions = (
        db.query(SessionRecord)
        .filter(SessionRecord.is_finished == True, SessionRecord.end_time.isnot(None))
        .order_by(desc(SessionRecord.end_time))
        .limit(limit)
        .all()
    )

    if not finished_sessions:
        return {"x_axis": [], "series": {"total": [], "professionalism": [], "compliance": [], "strategy": []}}

    # 倒序取出后反转为时间正序
    finished_sessions.reverse()

    x_axis = []
    total_scores = []
    prof_scores = []
    comp_scores = []
    strat_scores = []

    for session in finished_sessions:
        # 获取该会话的所有有效评分
        evals = (
            db.query(EvaluationRecord)
            .filter(
                EvaluationRecord.session_id == session.session_id,
                EvaluationRecord.professionalism_score >= 0,
            )
            .all()
        )
        if not evals:
            continue

        avg_prof = sum(e.professionalism_score for e in evals) / len(evals)
        avg_comp = sum(e.compliance_score for e in evals) / len(evals)
        avg_strat = sum(e.strategy_score for e in evals) / len(evals)
        avg_total = (avg_prof + avg_comp + avg_strat) / 3.0

        # 日期标签
        date_label = session.end_time.strftime("%m-%d") if session.end_time else "?"
        x_axis.append(date_label)
        total_scores.append(round(avg_total, 1))
        prof_scores.append(round(avg_prof, 1))
        comp_scores.append(round(avg_comp, 1))
        strat_scores.append(round(avg_strat, 1))

    return {
        "x_axis": x_axis,
        "series": {
            "total": total_scores,
            "professionalism": prof_scores,
            "compliance": comp_scores,
            "strategy": strat_scores,
        },
    }
