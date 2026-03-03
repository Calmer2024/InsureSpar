<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { AppMode, AppStatus, ChatMessage, Evaluation, FinalReport, Persona, Strategy } from './types'
import type { SSEEvent } from './services/api'
import {
  fetchPersonas,
  fetchStrategies,
  createManualSession,
  createAutoSession,
  streamChat,
  autoStep as apiAutoStep,
  pollEvaluations,
  fetchFinalReport,
  fetchManualFinalReport,
} from './services/api'

import TopBar from './components/layout/TopBar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import EvalPanel from './components/evaluation/EvalPanel.vue'
import PersonaModal from './components/modal/PersonaModal.vue'
import StrategyModal from './components/modal/StrategyModal.vue'
import ReportModal from './components/modal/ReportModal.vue'

// ── 全局状态 ──
const appMode = ref<AppMode>('manual')
const appStatus = ref<AppStatus>('idle')
const statusText = ref('等待启动')
const turnCount = ref(0)
const stageLabel = ref('等待启动')
const sessionId = ref<string | null>(null)
const isProcessing = ref(false)
const isFinished = ref(false)
const isPendingShutdown = ref(false)

// ── 数据 ──
const personas = ref<Persona[]>([])
const strategies = ref<Strategy[]>([])
const messages = ref<ChatMessage[]>([])
const evaluations = ref<Evaluation[]>([])
const finalReport = ref<FinalReport | null>(null)
const reportLoading = ref(false)

// ── 弹窗 ──
const showPersonaModal = ref(false)
const showStrategyModal = ref(false)
const showReportModal = ref(false)

// ── 标题 ──
const chatTitle = ref('💬 对话面板')
const chatSubtitle = ref('选择客户画像开始对练')

// ── 评分轮询 ──
let evalPollTimer: ReturnType<typeof setInterval> | null = null
let lastPolledTurn = 0
const renderedEvalTurns = new Set<number>()

// ── 自动推进计时器 ──
let autoTimerInterval: ReturnType<typeof setInterval> | null = null

// ── 消息计数器 ──
let msgCounter = 0
function nextMsgId(): string {
  return `msg-${++msgCounter}-${Date.now()}`
}

/* ========================================
 * 初始化
 * ======================================== */
onMounted(async () => {
  try {
    personas.value = await fetchPersonas()
  } catch (e) {
    console.error('加载画像失败', e)
  }
  // 默认弹出画像选择
  showPersonaModal.value = true
})

onUnmounted(() => {
  if (evalPollTimer) clearInterval(evalPollTimer)
  if (autoTimerInterval) clearInterval(autoTimerInterval)
})

/* ========================================
 * 模式切换
 * ======================================== */
function switchMode(mode: AppMode) {
  if (mode === appMode.value) return
  appMode.value = mode
  // 重置状态
  resetSession()
  if (mode === 'auto') {
    showStrategyModal.value = true
    loadStrategies()
  } else {
    showPersonaModal.value = true
  }
}

async function loadStrategies() {
  if (strategies.value.length) return
  try {
    strategies.value = await fetchStrategies()
  } catch (e) {
    console.error('加载策略失败', e)
  }
}

function resetSession() {
  sessionId.value = null
  messages.value = []
  evaluations.value = []
  turnCount.value = 0
  stageLabel.value = '等待启动'
  isFinished.value = false
  isPendingShutdown.value = false
  appStatus.value = 'idle'
  statusText.value = '等待启动'
  lastPolledTurn = 0
  renderedEvalTurns.clear()
  finalReport.value = null
  chatTitle.value = appMode.value === 'auto' ? '🤖 自动对战' : '💬 对话面板'
  chatSubtitle.value = appMode.value === 'auto' ? '选择客户与策略，开始自动对战' : '选择客户画像开始对练'
  if (evalPollTimer) { clearInterval(evalPollTimer); evalPollTimer = null }
  stopAutoTimer()
}

/* ========================================
 * 手动模式：选择画像 → 创建会话
 * ======================================== */
async function onSelectPersona(personaId: string) {
  showPersonaModal.value = false
  try {
    const result = await createManualSession(personaId)
    sessionId.value = result.session_id
    chatTitle.value = `💬 ${result.persona_name}`
    chatSubtitle.value = `${result.persona_description} | 难度: ${result.difficulty}`
    appStatus.value = 'ready'
    statusText.value = '就绪'
    addSystemMessage('✅ 会话已创建，请开始销售对话', 0, 'status')
    startEvalPolling()
  } catch (e) {
    console.error('创建会话失败', e)
  }
}

/* ========================================
 * 自动模式：选择画像+策略 → 创建会话
 * ======================================== */
async function onStartAuto(personaId: string, strategyId: string) {
  showStrategyModal.value = false
  try {
    const result = await createAutoSession(personaId, strategyId)
    sessionId.value = result.session_id
    chatTitle.value = `🤖 ${result.persona_name} × ${result.strategy_name}`
    chatSubtitle.value = `${result.persona_description} | ${result.strategy_description}`
    appStatus.value = 'ready'
    statusText.value = '就绪'
    addSystemMessage(`✅ 自动对战会话已创建 | 策略: ${result.strategy_name}`, 0, 'status')
    startEvalPolling()
  } catch (e) {
    console.error('创建自动会话失败', e)
  }
}

/* ========================================
 * 手动模式：发送消息
 * ======================================== */
async function handleSend(message: string) {
  if (!sessionId.value || isProcessing.value) return

  isProcessing.value = true
  appStatus.value = 'processing'
  statusText.value = '处理中...'

  const currentTurn = turnCount.value + 1

  // 1. 销售消息上屏
  messages.value.push({
    id: nextMsgId(),
    role: 'sales',
    content: message,
    turn: currentTurn,
  })

  // 2. 创建客户回复占位
  const customerMsgId = nextMsgId()
  messages.value.push({
    id: customerMsgId,
    role: 'customer',
    content: '',
    turn: currentTurn,
    isStreaming: true,
  })

  // 3. SSE 流式接收
  await streamChat(sessionId.value, message, (event: SSEEvent) => {
    handleManualSSE(event, customerMsgId, currentTurn)
  }, (err) => {
    const msg = findMessage(customerMsgId)
    if (msg) {
      msg.content = `[连接错误: ${err.message}]`
      msg.isStreaming = false
    }
  })

  isProcessing.value = false
  if (!isFinished.value) {
    appStatus.value = 'ready'
    statusText.value = '就绪'
  }
}

/* ========================================
 * 手动模式 SSE 事件处理
 * ======================================== */
function handleManualSSE(event: SSEEvent, customerMsgId: string, currentTurn: number) {
  const customerMsg = findMessage(customerMsgId)

  switch (event.type) {
    case 'status':
      addSystemMessage(event.content || '', currentTurn, 'status')
      statusText.value = event.content || ''
      break

    case 'token':
      if (customerMsg) {
        customerMsg.isStreaming = false
        customerMsg.content += event.content || ''
      }
      break

    case 'tool_call':
      addSystemMessage(`🔍 正在调用: ${event.tool}`, currentTurn, 'tool_call', event.tool)
      break

    case 'tool_result':
      addSystemMessage(`✅ ${event.tool}: ${(event.content || '').substring(0, 120)}`, currentTurn, 'tool_result', event.tool)
      break

    case 'stage_update':
      turnCount.value = event.turn_count || turnCount.value
      stageLabel.value = event.stage_label || stageLabel.value
      addSystemMessage(`📍 阶段: ${event.stage_label}（第${event.turn_count}轮）`, currentTurn, 'stage_update')
      break

    case 'force_guard':
      addSystemMessage(event.content || '', currentTurn, 'force_guard')
      break

    case 'done':
      if (customerMsg) {
        customerMsg.isStreaming = false
        if (!customerMsg.content && event.customer_reply) {
          customerMsg.content = event.customer_reply
        }
      }
      turnCount.value = event.turn_count || turnCount.value
      stageLabel.value = event.stage_label || stageLabel.value

      if (event.is_finished) {
        isFinished.value = true
        appStatus.value = 'finished'
        statusText.value = `对话结束 — ${event.stage_label}`
        addSystemMessage(`🏁 对话结束 — ${event.stage_label}`, currentTurn, 'stage_update')
      } else if (event.is_pending_shutdown) {
        isPendingShutdown.value = true
        addSystemMessage('⏳ 客户已做出决定，这是最后一轮对话机会', currentTurn, 'force_guard')
      }
      break

    case 'error':
      addSystemMessage(`❌ ${event.content}`, currentTurn, 'force_guard')
      if (customerMsg) {
        customerMsg.content = `[错误] ${event.content}`
        customerMsg.isStreaming = false
      }
      break
  }
}

/* ========================================
 * 自动模式：推进一步
 * ======================================== */
async function handleStep() {
  if (!sessionId.value || isProcessing.value || isFinished.value) return

  isProcessing.value = true
  appStatus.value = 'processing'
  statusText.value = '自动推进中...'

  const currentTurn = turnCount.value + 1

  // 创建销售和客户占位消息
  const salesMsgId = nextMsgId()
  const customerMsgId = nextMsgId()

  messages.value.push({
    id: salesMsgId,
    role: 'sales',
    content: '',
    turn: currentTurn,
    isStreaming: true,
  })
  messages.value.push({
    id: customerMsgId,
    role: 'customer',
    content: '',
    turn: currentTurn,
    isStreaming: true,
  })

  await apiAutoStep(sessionId.value, (event: SSEEvent) => {
    handleAutoSSE(event, salesMsgId, customerMsgId, currentTurn)
  }, (err) => {
    addSystemMessage(`❌ 推进失败: ${err.message}`, currentTurn, 'force_guard')
  })

  isProcessing.value = false
  if (!isFinished.value) {
    appStatus.value = 'ready'
    statusText.value = '就绪'
  }
}

/* ========================================
 * 自动模式 SSE 事件处理
 * ======================================== */
function handleAutoSSE(event: SSEEvent, salesMsgId: string, customerMsgId: string, currentTurn: number) {
  const salesMsg = findMessage(salesMsgId)
  const customerMsg = findMessage(customerMsgId)

  switch (event.type) {
    case 'phase':
    case 'customer_status':
    case 'sales_thinking':
      addSystemMessage(event.content || '', currentTurn, 'phase')
      statusText.value = event.content || ''
      break

    case 'sales_token':
      if (salesMsg) {
        salesMsg.isStreaming = false
        salesMsg.content += event.content || ''
      }
      break

    case 'sales_message_done':
      if (salesMsg) {
        salesMsg.isStreaming = false
        if (!salesMsg.content && event.content) {
          salesMsg.content = event.content
        }
      }
      break

    case 'sales_tool_call':
      addSystemMessage(`🔧 销售工具: ${event.tool}`, currentTurn, 'tool_call', event.tool)
      break

    case 'sales_tool_result':
      addSystemMessage(`✅ ${event.tool}: ${(event.content || '').substring(0, 120)}`, currentTurn, 'tool_result', event.tool)
      break

    case 'customer_token':
      if (customerMsg) {
        customerMsg.isStreaming = false
        customerMsg.content += event.content || ''
      }
      break

    case 'customer_tool_result':
      addSystemMessage(`✅ 客户端 ${event.tool}: ${(event.content || '').substring(0, 120)}`, currentTurn, 'tool_result', event.tool)
      break

    case 'stage_update':
      turnCount.value = event.turn_count || turnCount.value
      stageLabel.value = event.stage_label || stageLabel.value
      addSystemMessage(`📍 阶段: ${event.stage_label}（第${event.turn_count}轮）`, currentTurn, 'stage_update')
      if (event.reasoning) {
        addSystemMessage(`🧠 判定: ${event.reasoning.substring(0, 100)}`, currentTurn, 'status')
      }
      break

    case 'force_guard':
      addSystemMessage(event.content || '', currentTurn, 'force_guard')
      break

    case 'step_done':
      if (customerMsg) {
        customerMsg.isStreaming = false
        if (!customerMsg.content && event.customer_reply) {
          customerMsg.content = event.customer_reply
        }
      }
      if (salesMsg) {
        salesMsg.isStreaming = false
        if (!salesMsg.content && event.sales_message) {
          salesMsg.content = event.sales_message
        }
      }
      turnCount.value = event.turn_count || turnCount.value
      stageLabel.value = event.stage_label || stageLabel.value

      if (event.is_finished) {
        isFinished.value = true
        appStatus.value = 'finished'
        statusText.value = `对话结束 — ${event.stage_label}`
        addSystemMessage(`🏁 对话结束 — ${event.stage_label}`, currentTurn, 'stage_update')
        stopAutoTimer()
      } else if (event.is_pending_shutdown) {
        isPendingShutdown.value = true
        addSystemMessage('⏳ 客户已做出决定，下一轮将是最后告别', currentTurn, 'force_guard')
      }
      break

    case 'error':
      addSystemMessage(`❌ ${event.content}`, currentTurn, 'force_guard')
      break
  }
}

/* ========================================
 * 自动推进计时器
 * ======================================== */
function toggleAutoTimer() {
  if (autoTimerInterval) {
    stopAutoTimer()
  } else {
    autoTimerInterval = setInterval(() => {
      if (!isProcessing.value && sessionId.value && !isFinished.value) {
        handleStep()
      }
    }, 6000)
  }
}

function stopAutoTimer() {
  if (autoTimerInterval) {
    clearInterval(autoTimerInterval)
    autoTimerInterval = null
  }
}

/* ========================================
 * 评分轮询
 * ======================================== */
function startEvalPolling() {
  if (evalPollTimer) clearInterval(evalPollTimer)
  lastPolledTurn = 0
  renderedEvalTurns.clear()
  evalPollTimer = setInterval(doPollEvaluations, 3500)
}

async function doPollEvaluations() {
  if (!sessionId.value) return
  try {
    const data = await pollEvaluations(sessionId.value, lastPolledTurn)
    if (data.new_evaluations?.length) {
      for (const ev of data.new_evaluations) {
        if (renderedEvalTurns.has(ev.turn)) continue
        renderedEvalTurns.add(ev.turn)
        evaluations.value.push(ev)
        lastPolledTurn = Math.max(lastPolledTurn, ev.turn)
      }
    }
  } catch {
    // 静默处理
  }
}

/* ========================================
 * 终极报告
 * ======================================== */
async function handleShowReport() {
  if (!sessionId.value) return
  showReportModal.value = true
  reportLoading.value = true
  finalReport.value = null
  try {
    const fetchFn = appMode.value === 'auto' ? fetchFinalReport : fetchManualFinalReport
    finalReport.value = await fetchFn(sessionId.value)
  } catch (e) {
    console.error('获取报告失败', e)
  } finally {
    reportLoading.value = false
  }
}

/* ========================================
 * 辅助方法
 * ======================================== */
function addSystemMessage(content: string, turn: number, logType: string, toolName?: string) {
  messages.value.push({
    id: nextMsgId(),
    role: 'system',
    content,
    turn,
    logType: logType as any,
    toolName,
  })
}

function findMessage(id: string): ChatMessage | undefined {
  return messages.value.find(m => m.id === id)
}
</script>

<template>
  <div class="h-screen flex flex-col bg-surface">
    <!-- 顶部导航 -->
    <TopBar
      :mode="appMode"
      :status="appStatus"
      :status-text="statusText"
      :turn-count="turnCount"
      :stage-label="stageLabel"
      :session-id="sessionId"
      @switch-mode="switchMode"
      @new-session="() => { resetSession(); appMode === 'auto' ? (loadStrategies(), showStrategyModal = true) : showPersonaModal = true }"
    />

    <!-- 主内容区 -->
    <div class="flex flex-1 min-h-0">
      <!-- 左侧：对话面板 -->
      <div class="flex-1 min-w-0 border-r border-border">
        <ChatPanel
          :messages="messages"
          :mode="appMode"
          :title="chatTitle"
          :subtitle="chatSubtitle"
          :disabled="isProcessing || !sessionId"
          :is-finished="isFinished"
          @send="handleSend"
          @step="handleStep"
          @toggle-auto-timer="toggleAutoTimer"
          @show-report="handleShowReport"
        />
      </div>

      <!-- 右侧：考官评分面板 -->
      <div class="w-[380px] shrink-0">
        <EvalPanel :evaluations="evaluations" />
      </div>
    </div>

    <!-- 弹窗 -->
    <PersonaModal
      :visible="showPersonaModal"
      :personas="personas"
      @select="onSelectPersona"
      @close="showPersonaModal = false"
    />

    <StrategyModal
      :visible="showStrategyModal"
      :personas="personas"
      :strategies="strategies"
      @start="onStartAuto"
      @close="showStrategyModal = false"
    />

    <ReportModal
      :visible="showReportModal"
      :report="finalReport"
      :loading="reportLoading"
      @close="showReportModal = false"
    />
  </div>
</template>
