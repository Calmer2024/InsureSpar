/**
 * InsureSpar API 服务层
 * 封装所有后端 API 调用
 */
import type { Persona, Strategy, Evaluation, FinalReport } from '../types'

const BASE = '' // 通过 Vite proxy 转发

/* ========================================
 * 画像 & 策略
 * ======================================== */

export async function fetchPersonas(): Promise<Persona[]> {
    const res = await fetch(`${BASE}/api/personas`)
    if (!res.ok) throw new Error(`获取画像失败: ${res.status}`)
    return res.json()
}

export async function fetchStrategies(): Promise<Strategy[]> {
    const res = await fetch(`${BASE}/api/auto/strategies`)
    if (!res.ok) throw new Error(`获取策略失败: ${res.status}`)
    return res.json()
}

/* ========================================
 * 会话管理
 * ======================================== */

export interface CreateSessionResult {
    session_id: string
    persona_id: string
    persona_name: string
    persona_description: string
    difficulty: string
}

export async function createManualSession(personaId: string): Promise<CreateSessionResult> {
    const res = await fetch(`${BASE}/api/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_id: personaId }),
    })
    if (!res.ok) throw new Error(`创建会话失败: ${res.status}`)
    return res.json()
}

export interface CreateAutoSessionResult extends CreateSessionResult {
    strategy_id: string
    strategy_name: string
    strategy_description: string
    mode: string
}

export async function createAutoSession(
    personaId: string,
    strategyId: string
): Promise<CreateAutoSessionResult> {
    const res = await fetch(`${BASE}/api/auto/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_id: personaId, strategy_id: strategyId }),
    })
    if (!res.ok) throw new Error(`创建自动会话失败: ${res.status}`)
    return res.json()
}

/* ========================================
 * SSE 流式接口
 * ======================================== */

export type SSEEvent = {
    type: string
    content?: string
    stage?: string
    stage_label?: string
    turn_count?: number
    reasoning?: string
    tool?: string
    args?: string
    customer_reply?: string
    sales_message?: string
    current_stage?: string
    is_finished?: boolean
    is_pending_shutdown?: boolean
    tool_calls_log?: any[]
}

/**
 * 手动模式：发送消息并流式接收 SSE 事件
 */
export async function streamChat(
    sessionId: string,
    message: string,
    onEvent: (event: SSEEvent) => void,
    onError?: (err: Error) => void
): Promise<void> {
    try {
        const response = await fetch(`${BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message }),
        })
        if (!response.ok) {
            const err = await response.json().catch(() => ({}))
            throw new Error(err.detail || `HTTP ${response.status}`)
        }
        await parseSSEStream(response, onEvent)
    } catch (e) {
        onError?.(e instanceof Error ? e : new Error(String(e)))
    }
}

/**
 * 自动模式：推进一步并流式接收 SSE 事件
 */
export async function autoStep(
    sessionId: string,
    onEvent: (event: SSEEvent) => void,
    onError?: (err: Error) => void
): Promise<void> {
    try {
        const response = await fetch(`${BASE}/api/auto/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        })
        if (!response.ok) {
            const err = await response.json().catch(() => ({}))
            throw new Error(err.detail || `HTTP ${response.status}`)
        }
        await parseSSEStream(response, onEvent)
    } catch (e) {
        onError?.(e instanceof Error ? e : new Error(String(e)))
    }
}

/**
 * 通用 SSE 流解析器
 */
async function parseSSEStream(
    response: Response,
    onEvent: (event: SSEEvent) => void
): Promise<void> {
    const reader = response.body!.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop()! // 最后一个可能不完整

        for (const event of events) {
            if (!event.startsWith('data: ')) continue
            try {
                const data = JSON.parse(event.substring(6))
                onEvent(data)
            } catch {
                // 静默跳过解析错误
            }
        }
    }
}

/* ========================================
 * 评分轮询
 * ======================================== */

export interface EvalPollResult {
    session_id: string
    new_evaluations: Evaluation[]
}

export async function pollEvaluations(
    sessionId: string,
    sinceurn: number
): Promise<EvalPollResult> {
    const res = await fetch(
        `${BASE}/api/session/${sessionId}/evaluation/latest?turn=${sinceurn}`
    )
    if (!res.ok) throw new Error(`轮询评分失败: ${res.status}`)
    return res.json()
}

/* ========================================
 * 终极报告
 * ======================================== */

export async function fetchFinalReport(sessionId: string): Promise<FinalReport> {
    const res = await fetch(`${BASE}/api/auto/session/${sessionId}/final-report`)
    if (!res.ok) throw new Error(`获取报告失败: ${res.status}`)
    const data = await res.json()
    if (data.error) throw new Error(data.error)
    return data
}

/**
 * 手动模式的终极报告（路径不同）
 */
export async function fetchManualFinalReport(sessionId: string): Promise<FinalReport> {
    const res = await fetch(`${BASE}/api/session/${sessionId}/final-report`)
    if (!res.ok) throw new Error(`获取报告失败: ${res.status}`)
    const data = await res.json()
    if (data.error) throw new Error(data.error)
    return data
}

/* ========================================
 * 历史记录
 * ======================================== */

export interface HistorySession {
    session_id: string
    persona_id: string
    strategy_id: string | null
    start_time: string | null
    end_time: string | null
    final_stage: string | null
    turn_count: number
    is_finished: boolean
}

export interface HistoryDetail {
    session_info: HistorySession
    conversation_logs: Array<{
        id: number
        turn: number
        role: string
        content: string
        stage: string | null
        created_at: string | null
    }>
    evaluations: Array<{
        id: number
        turn: number
        scores: { professionalism: number; compliance: number; strategy: number }
        comments: { professionalism: string; compliance: string; strategy: string }
        overall_advice: string
        created_at: string | null
    }>
    final_report: {
        avg_scores: { total: number; professionalism: number; compliance: number; strategy: number }
        radar_data: string | null
        review_content: string | null
        created_at: string | null
    } | null
}

export async function fetchHistorySessions(skip = 0, limit = 50): Promise<HistorySession[]> {
    const res = await fetch(`${BASE}/api/history/sessions?skip=${skip}&limit=${limit}`)
    if (!res.ok) throw new Error(`获取历史失败: ${res.status}`)
    return res.json()
}

export async function fetchHistoryDetail(sessionId: string): Promise<HistoryDetail> {
    const res = await fetch(`${BASE}/api/history/sessions/${sessionId}`)
    if (!res.ok) throw new Error(`获取详情失败: ${res.status}`)
    return res.json()
}
