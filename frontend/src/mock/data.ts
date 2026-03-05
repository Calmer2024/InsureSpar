import type { Persona, Strategy, ChatMessage, Evaluation, FinalReport } from '../types'

/* ========================================
 * Mock 数据 — 静态 UI 阶段使用
 * ======================================== */

/** 客户画像列表 */
export const mockPersonas: Persona[] = [
    {
        persona_id: 'hard_boss',
        name: '王总 — 企业高管',
        description: '45岁，某上市公司副总裁。风险意识极强，对保险持负面态度，反感推销。',
        difficulty: 'hard',
    },
    {
        persona_id: 'tech_savvy',
        name: '李工 — IT工程师',
        description: '32岁，互联网公司资深工程师。逻辑思维强，喜欢对比数据，关注性价比。',
        difficulty: 'medium',
    },
    {
        persona_id: 'young_mother',
        name: '张女士 — 年轻宝妈',
        description: '28岁，全职妈妈。关心孩子教育和家庭保障，愿意掏钱但预算有限。',
        difficulty: 'easy',
    },
]

/** 销售策略列表 */
export const mockStrategies: Strategy[] = [
    {
        strategy_id: 'consultant',
        name: '顾问咨询型',
        description: '以专业顾问角色切入，先了解需求再推荐方案，注重建立信任。',
        strengths: '信任建立快、客户满意度高',
        tags: ['专业', '温和', '信任导向'],
    },
    {
        strategy_id: 'data_driven',
        name: '数据驱动型',
        description: '以数据和案例说服，用数字讲故事，针对理性客户效果显著。',
        strengths: '逻辑严密、数据有力',
        tags: ['数据', '理性', '案例分析'],
    },
    {
        strategy_id: 'emotional',
        name: '情感共鸣型',
        description: '从家庭责任和情感需求出发，打动客户心理防线。',
        strengths: '感染力强、促成率高',
        tags: ['情感', '故事', '家庭'],
    },
]

/** 模拟对话数据 — 包含3轮对话，含系统日志 */
export const mockMessages: ChatMessage[] = [
    // ── 第 1 轮 ──
    {
        id: 'm1',
        role: 'sales',
        content: '王总您好！感谢您百忙之中抽出时间。我了解到您管理着上市公司的核心业务，这方面的压力一定不小。不知道您平时有没有考虑过企业高管的个人保障问题？',
        turn: 1,
    },
    {
        id: 's1-phase',
        role: 'system',
        content: '🤖 客户Agent 正在思考回应...',
        turn: 1,
        logType: 'phase',
    },
    {
        id: 's1-tool',
        role: 'system',
        content: '🔍 正在查询健康告知条件...',
        turn: 1,
        logType: 'tool_call',
        toolName: 'check_health_notice',
    },
    {
        id: 's1-tool-result',
        role: 'system',
        content: '✅ 健康告知查询完成：标准体，无特殊告知项',
        turn: 1,
        logType: 'tool_result',
        toolName: 'check_health_notice',
    },
    {
        id: 'm2',
        role: 'customer',
        content: '嗯，你好。说实话我每天都有各种推销电话，保险的事我不太感兴趣。公司已经给我上了团险，我不觉得还需要额外买什么保险。你有什么具体的想法可以说，但说不上来我就要挂了。',
        turn: 1,
    },
    {
        id: 's1-stage',
        role: 'system',
        content: '📍 阶段判定：💬 破冰与探寻（第1轮）',
        turn: 1,
        logType: 'stage_update',
    },

    // ── 第 2 轮 ──
    {
        id: 'm3',
        role: 'sales',
        content: '理解您的时间很宝贵，我尽量说重点。团体险确实是基础保障，但坦白说，团险通常有几个局限：一是保额偏低，高管的收入和责任需要更高的保障；二是离开公司后团险就失效了。我这边可以帮您做一个保障缺口分析，您觉得怎么样？',
        turn: 2,
    },
    {
        id: 's2-phase',
        role: 'system',
        content: '🤖 客户Agent 正在思考回应...',
        turn: 2,
        logType: 'phase',
    },
    {
        id: 's2-tool',
        role: 'system',
        content: '🔍 正在查询产品费率（尊享百万医疗/重疾险）...',
        turn: 2,
        logType: 'tool_call',
        toolName: 'query_premium',
    },
    {
        id: 's2-tool-result',
        role: 'system',
        content: '✅ 费率查询完成：男性45岁，尊享百万医疗年缴 ¥2,350，重疾险50万保额年缴 ¥18,600',
        turn: 2,
        logType: 'tool_result',
        toolName: 'query_premium',
    },
    {
        id: 'm4',
        role: 'customer',
        content: '你说的这个团险离职后失效的问题倒是让我想到了一些……确实，我在这家公司不一定做到退休。不过保险产品这么多，说实话我不太信任保险公司，总觉得理赔的时候各种麻烦。你先说说你们的产品具体怎么回事？',
        turn: 2,
    },
    {
        id: 's2-stage',
        role: 'system',
        content: '📍 阶段判定：⚡ 异议处理（第2轮）',
        turn: 2,
        logType: 'stage_update',
    },

    // ── 第 3 轮 ──
    {
        id: 'm5',
        role: 'sales',
        content: '您担心理赔问题完全可以理解，我给您看一组数据：我们公司去年的理赔率是98.7%，平均理赔时效1.2天，远高于行业平均水平。另外我们有专门的VIP高端客户理赔通道，像您这样的企业高管客户可以享受1对1理赔专员服务。我可以给您看几个同类客户的理赔案例，您看方便吗？',
        turn: 3,
    },
    {
        id: 's3-phase',
        role: 'system',
        content: '🤖 客户Agent 正在思考回应...',
        turn: 3,
        logType: 'phase',
    },
    {
        id: 'm6',
        role: 'customer',
        content: '嗯……98.7%的理赔率确实不错。VIP通道这个我倒是第一次听说。你说的这个高端医疗险，保障范围具体包括什么？有没有在公立医院特需部和私立医院看病的保障？另外年交保费大概多少？',
        turn: 3,
    },
    {
        id: 's3-stage',
        role: 'system',
        content: '📍 阶段判定：⚡ 异议处理（第3轮）',
        turn: 3,
        logType: 'stage_update',
    },
]

/** 模拟考官评价 */
export const mockEvaluations: Evaluation[] = [
    {
        turn: 1,
        professionalism_score: 7,
        compliance_score: 9,
        strategy_score: 6,
        professionalism_comment: '开场白自然，但未充分介绍自身身份和来意，可以先自报家门增加正式感。',
        compliance_comment: '话术无合规风险，未使用虚假宣传或误导性语言。',
        strategy_comment: '直接切入话题的方式对于高压客户可能过于急切，建议先从轻松话题暖场。',
        overall_advice: '建议在开场时先建立信任与亲和力，不要急于切入产品话题。对于高端客户，可以先聊聊行业趋势作为切入点。',
    },
    {
        turn: 2,
        professionalism_score: 8,
        compliance_score: 9,
        strategy_score: 8,
        professionalism_comment: '非常好地利用了团险的局限性来建立专业形象，保障缺口分析的提议很专业。',
        compliance_comment: '对团险局限性的陈述基本准确，未严重歪曲事实。',
        strategy_comment: '精准把握了客户离职后团险失效的痛点，提出保障缺口分析的提案展现了顾问式销售思维。',
        overall_advice: '这一轮应对非常出色。后续可以准备好具体的保障缺口分析报告模板，让客户感受到被尊重。',
    },
    {
        turn: 3,
        professionalism_score: 9,
        compliance_score: 8,
        strategy_score: 9,
        professionalism_comment: '理赔数据的引用非常有说服力，VIP服务的介绍增加了差异化竞争力。',
        compliance_comment: '理赔率数据需要注意来源可追溯性，建议在实际销售中附上官方报告链接。',
        strategy_comment: '从数据驱动到个案说服，层层递进的论证方式非常高明。客户已经开始主动询问产品细节，说明策略奏效。',
        overall_advice: '绝佳表现！客户已经从抗拒转为主动询问，说明信任已初步建立。下一步应重点回答客户关于保障范围和费率的具体问题。',
    },
]

/** 模拟终极评估报告 */
export const mockFinalReport: FinalReport = {
    persona_name: '王总 — 企业高管',
    strategy_id: 'consultant',
    final_stage: '需要跟进',
    turn_count: 8,
    avg_scores: {
        total: 8.2,
        professionalism: 8.0,
        compliance: 8.7,
        strategy: 7.7,
    },
    radar: {
        labels: ['专业知识', '沟通技巧', '需求洞察', '异议处理', '合规意识', '成交能力'],
        scores: [8.5, 7.8, 8.2, 7.5, 9.0, 6.8],
    },
    review: `这位销售人员在本次对练中表现出了较高的专业素养和良好的沟通能力。

【优势】
1. 专业知识扎实：能够准确引用理赔数据和产品特性，展现了深厚的行业功底。
2. 异议处理得当：面对客户的抗拒，没有急于反驳，而是承认客户顾虑后再引导，体现了成熟的销售心态。
3. 合规意识强：全程未出现虚假宣传或误导话术，始终在合规框架内推进对话。

【待改进】
1. 开场阶段略显仓促，可以投入更多时间了解客户的真实需求和生活场景。
2. 缺少数字化辅助工具的使用（如当场生成保障方案对比报告），削弱了专业感。
3. 逼单意识偏弱，在客户已经出现积极信号时没有及时推动下一步行动。

【总评】
整体表现优良，得分 8.2/10。建议继续精进需求洞察能力和成交节奏把控。`,
    per_turn_scores: [
        { turn: 1, professionalism: 7, compliance: 9, strategy: 6, advice: '开场需要更多信任建立' },
        { turn: 2, professionalism: 8, compliance: 9, strategy: 8, advice: '保障缺口分析的提议很好' },
        { turn: 3, professionalism: 9, compliance: 8, strategy: 9, advice: '数据驱动论证非常有效' },
        { turn: 4, professionalism: 8, compliance: 9, strategy: 7, advice: '需要更深入的需求挖掘' },
        { turn: 5, professionalism: 8, compliance: 8, strategy: 8, advice: '方案定制化程度可提高' },
        { turn: 6, professionalism: 8, compliance: 9, strategy: 8, advice: '客户信号识别准确' },
        { turn: 7, professionalism: 8, compliance: 9, strategy: 7, advice: '可以尝试试探性成交' },
        { turn: 8, professionalism: 8, compliance: 8, strategy: 8, advice: '约定跟进计划很好' },
    ],
}

/* ========================================
 * Dashboard Mock 数据
 * ======================================== */

/** 个人概览 */
export const mockDashboardOverview = {
    user_info: {
        name: '张明远',
        rank: '高级销售代表',
        avatar_url: '',
        join_date: '2024-06-15',
    },
    stats: {
        total_sessions: 42,
        total_duration_minutes: 512,
        deal_closed_count: 15,
        avg_score_all_time: 7.8,
    },
}

/** 能力雷达 & 弱点诊断 */
export const mockDashboardCapabilities = {
    radar: {
        labels: ['专业深度', '合规红线', '破冰能力', '异议处理', '促单缔结', '同理心'],
        scores: [8.2, 9.5, 7.0, 6.5, 7.5, 8.0],
    },
    weaknesses: [
        { dimension: '异议处理', frequency: 12, advice: '在面对"保费太贵"时，过早进行降价妥协，缺乏价值塑造。建议多使用利益量化法。' },
        { dimension: '破冰能力', frequency: 8, advice: '开场生硬，未充分了解客户家庭背景即推销产品。建议先聊家庭话题暖场。' },
        { dimension: '促单缔结', frequency: 6, advice: '在客户释放购买信号时犹豫不决，错过最佳促单时机。建议学习试探性成交法。' },
    ],
    ai_general_review: '近期合规性表现优异，无违规情况。异议处理能力处于瓶颈期，建议专项练习「价格抗拒」和「信任危机」剧本。破冰环节有明显进步，继续保持对客户背景的主动探寻。',
}

/** 能力成长曲线 */
export const mockDashboardGrowth = {
    x_axis: ['02-25', '02-26', '02-27', '02-28', '03-01', '03-02', '03-03', '03-04'],
    series: {
        total: [6.2, 6.8, 6.5, 7.1, 7.5, 7.3, 8.0, 8.1],
        professionalism: [7.0, 7.5, 7.5, 7.8, 8.0, 8.2, 8.5, 8.5],
        compliance: [8.0, 8.5, 9.0, 9.0, 9.5, 9.5, 9.5, 9.8],
        strategy: [5.0, 5.5, 5.0, 6.0, 6.5, 6.0, 7.0, 7.0],
    },
}
