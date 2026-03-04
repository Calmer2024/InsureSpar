/* ========================================
 * InsureSpar 前端类型定义
 * ======================================== */

/** 客户画像 */
export interface Persona {
    persona_id: string
    name: string
    description: string
    difficulty: string
    tags?: string[]
    demographics?: string
    health_status?: string
    financial_status?: string
    insurance_awareness?: string
    risk_preference?: string
    core_focus?: string
    communication_style?: string
}

/** 销售策略 */
export interface Strategy {
    strategy_id: string
    name: string
    description: string
    difficulty?: string
    strengths?: string
    weaknesses?: string
    tags?: string[]
}

/** 对话消息类型 */
export type MessageRole = 'sales' | 'customer' | 'system'

/** 系统日志类型 */
export type SystemLogType =
    | 'phase'
    | 'status'
    | 'tool_call'
    | 'tool_result'
    | 'stage_update'
    | 'force_guard'

/** 聊天消息 */
export interface ChatMessage {
    id: string
    role: MessageRole
    content: string
    turn: number
    /** 系统日志类型（仅 role='system' 时有效） */
    logType?: SystemLogType
    /** 工具名称（tool_call/tool_result 时有效） */
    toolName?: string
    /** 附加参数 */
    toolArgs?: string
    /** 是否正在打字中 */
    isStreaming?: boolean
}

/** 单轮考官评价 */
export interface Evaluation {
    turn: number
    professionalism_score: number
    compliance_score: number
    strategy_score: number
    professionalism_comment: string
    compliance_comment: string
    strategy_comment: string
    overall_advice: string
}

/** 终极评估报告 */
export interface FinalReport {
    persona_name?: string
    strategy_id?: string
    final_stage?: string
    turn_count?: number
    avg_scores: {
        total: number
        professionalism: number
        compliance: number
        strategy: number
    }
    radar: {
        labels: string[]
        scores: number[]
    }
    review: string
    per_turn_scores: Array<{
        turn: number
        professionalism: number
        compliance: number
        strategy: number
        advice: string
    }>
}

/** 对话阶段标签 */
export type DialogueStage =
    | 'INTRODUCTION'
    | 'OBJECTION'
    | 'DECISION_SIGN'
    | 'DECISION_PENDING'
    | 'DECISION_FOLLOW_UP'
    | 'DECISION_REJECT'

/** 应用模式 */
export type AppMode = 'manual' | 'auto'

/** 应用状态 */
export type AppStatus = 'idle' | 'ready' | 'processing' | 'error' | 'finished'

/** 对话轮次数据（用于聊天面板按轮次分组） */
export interface ChatRound {
    turn: number
    messages: ChatMessage[]
}
