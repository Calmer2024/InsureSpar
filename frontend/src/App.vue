<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { AppStatus, ChatMessage, Evaluation, FinalReport, Persona, Strategy } from './types'
import type { SSEEvent } from './services/api'
import {
  fetchPersonas,
  fetchStrategies,
  createAutoSession,
  streamChat,
  autoStep as apiAutoStep,
  pollEvaluations,
  fetchFinalReport,
} from './services/api'

import TopBar from './components/layout/TopBar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import EvalPanel from './components/evaluation/EvalPanel.vue'
import SessionSetupModal from './components/modal/SessionSetupModal.vue'
import HistoryDrawer from './components/history/HistoryDrawer.vue'

// ── 状态 ──
const appStatus = ref<AppStatus>('idle')
const statusText = ref('等待启动')
const turnCount = ref(0)
const stageLabel = ref('等待启动')
const sessionId = ref<string | null>(null)
const isProcessing = ref(false)
const isFinished = ref(false)
const isPendingShutdown = ref(false)
const autoTimerActive = ref(false)

// ── 数据 ──
const personas = ref<Persona[]>([])
const strategies = ref<Strategy[]>([])
const messages = ref<ChatMessage[]>([])
const evaluations = ref<Evaluation[]>([])
const finalReport = ref<FinalReport | null>(null)
const reportLoading = ref(false)

// ── 弹窗 / 抽屉 ──
const showSetupModal = ref(false)
const showHistory = ref(false)
const isHistoryView = ref(false)

// ── 标题 ──
const chatTitle = ref('对话面板')
const chatSubtitle = ref('点击"新对练"开始')

// ── 评分轮询 ──
let evalPollTimer: ReturnType<typeof setInterval> | null = null
let lastPolledTurn = 0
const renderedEvalTurns = new Set<number>()

// ── 自动推进 ──
let autoTimer: ReturnType<typeof setInterval> | null = null

// ── ID 生成 ──
let _id = 0
const mid = () => `m${++_id}-${Date.now()}`

/* ========================================
 * 初始化
 * ======================================== */
onMounted(async () => {
  try {
    const [p, s] = await Promise.all([fetchPersonas(), fetchStrategies()])
    personas.value = p
    strategies.value = s
  } catch (e) {
    console.error('加载初始数据失败', e)
  }
  showSetupModal.value = true
})

onUnmounted(() => {
  if (evalPollTimer) clearInterval(evalPollTimer)
  stopAutoTimer()
})

/* ========================================
 * 会话管理
 * ======================================== */
function resetSession() {
  sessionId.value = null
  messages.value = []
  evaluations.value = []
  turnCount.value = 0
  stageLabel.value = '等待启动'
  isFinished.value = false
  isPendingShutdown.value = false
  isProcessing.value = false
  appStatus.value = 'idle'
  statusText.value = '等待启动'
  lastPolledTurn = 0
  renderedEvalTurns.clear()
  finalReport.value = null
  reportLoading.value = false
  chatTitle.value = '对话面板'
  chatSubtitle.value = '点击"新对练"开始'
  if (evalPollTimer) { clearInterval(evalPollTimer); evalPollTimer = null }
  stopAutoTimer()
}

function handleNewSession() {
  resetSession()
  showSetupModal.value = true
}

async function onStart(personaId: string, strategyId: string) {
  showSetupModal.value = false
  try {
    const r = await createAutoSession(personaId, strategyId)
    sessionId.value = r.session_id
    chatTitle.value = `${r.persona_name} × ${r.strategy_name}`
    chatSubtitle.value = `${r.persona_description}`
    appStatus.value = 'ready'
    statusText.value = '就绪 — 输入话术或点击 AI 推进'
    addSys('会话已创建，可手动输入或 AI 推进', 0, 'status')
    startEvalPolling()
  } catch (e: any) {
    console.error('创建会话失败', e)
    addSys(`创建会话失败: ${e.message}`, 0, 'force_guard')
  }
}

/* ========================================
 * 手动发送
 * ======================================== */
async function handleSend(message: string) {
  if (!sessionId.value || isProcessing.value) return
  isProcessing.value = true
  appStatus.value = 'processing'
  statusText.value = '客户思考中…'

  const turn = turnCount.value + 1

  // 销售消息上屏
  messages.value.push({ id: mid(), role: 'sales', content: message, turn })

  // 客户占位
  const cid = mid()
  messages.value.push({ id: cid, role: 'customer', content: '', turn, isStreaming: true })

  await streamChat(sessionId.value, message, (ev) => {
    handleManualSSE(ev, cid, turn)
  }, (err) => {
    const m = findMsg(cid)
    if (m) { m.content = `[错误: ${err.message}]`; m.isStreaming = false }
  })

  isProcessing.value = false
  if (!isFinished.value) { appStatus.value = 'ready'; statusText.value = '就绪' }
}

function handleManualSSE(ev: SSEEvent, cid: string, turn: number) {
  const cm = findMsg(cid)
  switch (ev.type) {
    // 状态 → 仅更新顶栏，不写入聊天
    case 'status':
      statusText.value = ev.content || ''
      break
    // 打字机
    case 'token':
      if (cm) { cm.isStreaming = false; cm.content += ev.content || '' }
      break
    // 工具
    case 'tool_call':
      addSys(`调用 ${ev.tool}…`, turn, 'tool_call', ev.tool)
      break
    case 'tool_result':
      addSys(`${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    // 阶段
    case 'stage_update':
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      addSys(`${ev.stage_label}（第${ev.turn_count}轮）`, turn, 'stage_update')
      break
    case 'force_guard':
      addSys(ev.content || '', turn, 'force_guard')
      break
    // 完成
    case 'done':
      if (cm) { cm.isStreaming = false; if (!cm.content && ev.customer_reply) cm.content = ev.customer_reply }
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      if (ev.is_finished) finishConversation(ev.stage_label || '', turn)
      else if (ev.is_pending_shutdown) { isPendingShutdown.value = true; addSys('客户已做出决定，这是最后一轮', turn, 'force_guard') }
      break
    case 'error':
      addSys(ev.content || '', turn, 'force_guard')
      if (cm) { cm.content = `[错误] ${ev.content}`; cm.isStreaming = false }
      break
  }
}

/* ========================================
 * AI 推进
 * ======================================== */
async function handleStep() {
  if (!sessionId.value || isProcessing.value || isFinished.value) return
  isProcessing.value = true
  appStatus.value = 'processing'
  statusText.value = '销售Agent思考中…'

  const turn = turnCount.value + 1
  const sid = mid()
  const cid = mid()
  messages.value.push({ id: sid, role: 'sales', content: '', turn, isStreaming: true })
  messages.value.push({ id: cid, role: 'customer', content: '', turn, isStreaming: true })

  await apiAutoStep(sessionId.value, (ev) => {
    handleAutoSSE(ev, sid, cid, turn)
  }, (err) => {
    addSys(`推进失败: ${err.message}`, turn, 'force_guard')
  })

  isProcessing.value = false
  if (!isFinished.value) { appStatus.value = 'ready'; statusText.value = '就绪' }
}

function handleAutoSSE(ev: SSEEvent, sid: string, cid: string, turn: number) {
  const sm = findMsg(sid)
  const cm = findMsg(cid)
  switch (ev.type) {
    // 状态 → 仅顶栏，不写入聊天
    case 'phase':
    case 'customer_status':
    case 'sales_thinking':
      statusText.value = ev.content || ''
      break
    // 销售打字机
    case 'sales_token':
      if (sm) { sm.isStreaming = false; sm.content += ev.content || '' }
      break
    case 'sales_message_done':
      if (sm) { sm.isStreaming = false; if (!sm.content && ev.content) sm.content = ev.content }
      statusText.value = '客户思考中…'
      break
    // 销售工具
    case 'sales_tool_call':
      addSys(`销售工具 ${ev.tool}`, turn, 'tool_call', ev.tool)
      break
    case 'sales_tool_result':
      addSys(`${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    // 客户打字机
    case 'customer_token':
      if (cm) { cm.isStreaming = false; cm.content += ev.content || '' }
      break
    case 'customer_tool_result':
      addSys(`${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    // 阶段
    case 'stage_update':
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      addSys(`${ev.stage_label}（第${ev.turn_count}轮）`, turn, 'stage_update')
      break
    case 'force_guard':
      addSys(ev.content || '', turn, 'force_guard')
      break
    // 完成
    case 'step_done':
      if (cm) { cm.isStreaming = false; if (!cm.content && ev.customer_reply) cm.content = ev.customer_reply }
      if (sm) { sm.isStreaming = false; if (!sm.content && ev.sales_message) sm.content = ev.sales_message }
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      if (ev.is_finished) { finishConversation(ev.stage_label || '', turn); stopAutoTimer() }
      else if (ev.is_pending_shutdown) { isPendingShutdown.value = true; addSys('客户已做出决定，下一轮将是最后告别', turn, 'force_guard') }
      break
    case 'error':
      addSys(ev.content || '', turn, 'force_guard')
      break
  }
}

/* ========================================
 * 恢复继续对练
 * ======================================== */
async function handleResumeSession() {
  if (!sessionId.value) return
  isHistoryView.value = false
  isFinished.value = false
  appStatus.value = 'ready'
  statusText.value = '会话已恢复，可继续输入或推进'
  
  // 恢复最新的拉取回合记录，以防重复获取
  lastPolledTurn = evaluations.value.length > 0 ? Math.max(...evaluations.value.map(e => e.turn)) : 0
  evaluations.value.forEach(e => renderedEvalTurns.add(e.turn))
  startEvalPolling()
}

/* ========================================
 * 对话结束
 * ======================================== */
function finishConversation(label: string, turn: number) {
  isFinished.value = true
  appStatus.value = 'finished'
  statusText.value = `对话结束 — ${label}`
  addSys(`对话结束 — ${label}`, turn, 'stage_update')
  // 自动获取终极报告
  loadFinalReport()
}

async function loadFinalReport() {
  if (!sessionId.value) return
  reportLoading.value = true
  try {
    finalReport.value = await fetchFinalReport(sessionId.value)
  } catch (e) {
    console.error('获取报告失败', e)
  } finally {
    reportLoading.value = false
  }
}

/* ========================================
 * 自动推进
 * ======================================== */
function toggleAutoTimer() {
  if (autoTimer) {
    stopAutoTimer()
  } else {
    autoTimerActive.value = true
    // 立即执行一次
    if (!isProcessing.value && sessionId.value && !isFinished.value) handleStep()
    autoTimer = setInterval(() => {
      if (!isProcessing.value && sessionId.value && !isFinished.value) handleStep()
    }, 5000)
  }
}

function stopAutoTimer() {
  if (autoTimer) { clearInterval(autoTimer); autoTimer = null }
  autoTimerActive.value = false
}

/* ========================================
 * 评分轮询
 * ======================================== */
function startEvalPolling() {
  if (evalPollTimer) clearInterval(evalPollTimer)
  lastPolledTurn = 0
  renderedEvalTurns.clear()
  evalPollTimer = setInterval(doPoll, 3500)
}

async function doPoll() {
  if (!sessionId.value) return
  try {
    const d = await pollEvaluations(sessionId.value, lastPolledTurn)
    for (const ev of d.new_evaluations || []) {
      if (renderedEvalTurns.has(ev.turn)) continue
      renderedEvalTurns.add(ev.turn)
      evaluations.value.push(ev)
      lastPolledTurn = Math.max(lastPolledTurn, ev.turn)
    }
  } catch { /* 静默 */ }
}

/* ========================================
 * 历史回放与恢复
 * ======================================== */
function viewHistorySession(data: {
  messages: ChatMessage[]
  evaluations: Evaluation[]
  finalReport: FinalReport | null
  info: any
}) {
  resetSession()
  showHistory.value = false
  isHistoryView.value = true
  isFinished.value = data.info.is_finished
  messages.value = data.messages
  evaluations.value = data.evaluations
  finalReport.value = data.finalReport
  turnCount.value = data.info.turn_count || 0
  stageLabel.value = data.info.final_stage || 'INTRODUCTION'
  sessionId.value = data.info.session_id

  appStatus.value = 'finished'
  statusText.value = '历史回放（只读）'
  chatTitle.value = `📚 ${data.info.persona_id}${data.info.strategy_id ? ' × ' + data.info.strategy_id : ''}`
  chatSubtitle.value = `历史记录 · ${data.info.turn_count} 轮 · ${data.info.final_stage || '未结束'}`
}

/* ========================================
 * 辅助
 * ======================================== */
function addSys(content: string, turn: number, logType: string, toolName?: string) {
  messages.value.push({ id: mid(), role: 'system', content, turn, logType: logType as any, toolName })
}
function findMsg(id: string) { return messages.value.find(m => m.id === id) }
</script>

<template>
  <div class="h-screen flex flex-col bg-surface">
    <TopBar
      :status="appStatus"
      :status-text="statusText"
      :turn-count="turnCount"
      :stage-label="stageLabel"
      :session-id="sessionId"
      @new-session="handleNewSession"
      @show-history="showHistory = true"
    />

    <div class="flex flex-1 min-h-0">
      <!-- 聊天面板 -->
      <div class="flex-1 min-w-0 border-r border-border">
        <ChatPanel
          :messages="messages"
          :title="chatTitle"
          :subtitle="chatSubtitle"
          :disabled="appStatus === 'loading'"
          :is-finished="isFinished"
          :is-history-view="isHistoryView"
          :auto-timer-active="autoTimerActive"
          @send="handleSend"
          @step="handleStep"
          @toggle-auto-timer="toggleAutoTimer"
          @resume-session="handleResumeSession"
        />
      </div>

      <!-- 右侧：考官评分面板 -->
      <div class="w-[380px] shrink-0">
        <EvalPanel
          :evaluations="evaluations"
          :final-report="finalReport"
          :report-loading="reportLoading"
          :is-finished="isFinished"
        />
      </div>
    </div>

    <!-- 弹窗 -->
    <SessionSetupModal
      :visible="showSetupModal"
      :personas="personas"
      :strategies="strategies"
      @start="onStart"
      @close="showSetupModal = false"
    />

    <!-- 历史抽屉 -->
    <HistoryDrawer
      :visible="showHistory"
      @close="showHistory = false"
      @view-session="viewHistorySession"
    />
  </div>
</template>
