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
import AppSidebar from './components/layout/AppSidebar.vue'
import HomeView from './components/home/HomeView.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import EvalPanel from './components/evaluation/EvalPanel.vue'
import SessionSetupModal from './components/modal/SessionSetupModal.vue'
import HistoryDrawer from './components/history/HistoryDrawer.vue'
import DashboardView from './components/dashboard/DashboardView.vue'

// ── 状态 ──
const currentView = ref<'home' | 'practice' | 'dashboard'>('home')
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
const isEvalCollapsed = ref(true)

// ── 标题 ──
const chatTitle = ref('对话面板')
const chatSubtitle = ref('点击"新对练"开始')
const activePersona = ref<Persona | null>(null)

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
  isHistoryView.value = false
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
  activePersona.value = null
  if (evalPollTimer) { clearInterval(evalPollTimer); evalPollTimer = null }
  stopAutoTimer()
}

function handleNewSession() {
  currentView.value = 'practice'
  showSetupModal.value = true
}

function navigateTo(view: 'home' | 'practice' | 'dashboard') {
  if (view !== 'practice') {
    showHistory.value = false
    isEvalCollapsed.value = true
  }
  currentView.value = view
}

function openHistory() {
  if (currentView.value !== 'practice') {
    currentView.value = 'practice'
    showHistory.value = true
  } else {
    showHistory.value = !showHistory.value
  }
  isEvalCollapsed.value = true
}

function toggleEvaluation() {
  isEvalCollapsed.value = !isEvalCollapsed.value
  if (!isEvalCollapsed.value) showHistory.value = false
}

async function onStart(personaId: string, strategyId: string) {
  showSetupModal.value = false
  resetSession()
  try {
    const r = await createAutoSession(personaId, strategyId)
    sessionId.value = r.session_id
    chatTitle.value = `${r.persona_name} × ${r.strategy_name}`
    chatSubtitle.value = `${r.persona_description}`
    activePersona.value = personas.value.find(p => p.persona_id === r.persona_id) || null
    appStatus.value = 'ready'
    statusText.value = '就绪，请输入话术或点击 AI 推进'
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

  // 延迟创建客户占位，让工具调用排在前面
  const cid = mid()
  let customerPushed = false
  const ensureCustomer = () => {
    if (!customerPushed) {
      messages.value.push({ id: cid, role: 'customer', content: '', turn, isStreaming: true })
      customerPushed = true
    }
  }

  await streamChat(sessionId.value, message, (ev) => {
    handleManualSSE(ev, cid, turn, ensureCustomer)
  }, (err) => {
    ensureCustomer()
    const m = findMsg(cid)
    if (m) { m.content = `[错误: ${err.message}]`; m.isStreaming = false }
  })

  isProcessing.value = false
  if (!isFinished.value) { appStatus.value = 'ready'; statusText.value = '就绪' }
}

function handleManualSSE(ev: SSEEvent, cid: string, turn: number, ensureCustomer: () => void) {
  switch (ev.type) {
    case 'status':
      statusText.value = ev.content || ''
      break
    case 'tool_call':
      addSys(`调用 ${ev.tool}…`, turn, 'tool_call', ev.tool)
      break
    case 'tool_result':
      addSys(`${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    case 'token': {
      ensureCustomer()
      const cm = findMsg(cid)
      if (cm) { cm.isStreaming = false; cm.content += ev.content || '' }
      break
    }
    case 'stage_update': {
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.detected_stage_label || ev.stage_label || stageLabel.value
      ensureCustomer()
      addSys(buildStageText(ev), turn, 'stage_update')
      break
    }
    case 'force_guard':
      addSys(ev.content || '', turn, 'force_guard')
      break
    case 'done': {
      ensureCustomer()
      const cm = findMsg(cid)
      if (cm) { cm.isStreaming = false; if (!cm.content && ev.customer_reply) cm.content = ev.customer_reply }
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      if (ev.is_finished) finishConversation(ev.stage_label || '', turn)
      else if (ev.is_pending_shutdown) { isPendingShutdown.value = true; addSys('客户已做出决定，这是最后一轮', turn, 'force_guard') }
      break
    }
    case 'error': {
      addSys(ev.content || '', turn, 'force_guard')
      ensureCustomer()
      const cm = findMsg(cid)
      if (cm) { cm.content = `[错误] ${ev.content}`; cm.isStreaming = false }
      break
    }
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

  let salesPushed = false
  let customerPushed = false
  const ensureSales = () => {
    if (!salesPushed) {
      messages.value.push({ id: sid, role: 'sales', content: '', turn, isStreaming: true })
      salesPushed = true
    }
  }
  const ensureCustomer = () => {
    if (!customerPushed) {
      ensureSales() 
      messages.value.push({ id: cid, role: 'customer', content: '', turn, isStreaming: true })
      customerPushed = true
    }
  }

  ensureSales()

  await apiAutoStep(sessionId.value, (ev) => {
    handleAutoSSE(ev, sid, cid, turn, ensureSales, ensureCustomer)
  }, (err) => {
    addSys(`推进失败: ${err.message}`, turn, 'force_guard')
  })

  isProcessing.value = false
  if (!isFinished.value) { appStatus.value = 'ready'; statusText.value = '就绪' }
}

function handleAutoSSE(ev: SSEEvent, sid: string, cid: string, turn: number, ensureSales: () => void, ensureCustomer: () => void) {
  switch (ev.type) {
    case 'phase':
    case 'customer_status':
    case 'sales_thinking':
      statusText.value = ev.content || ''
      break
    case 'sales_tool_call':
      insertSysBefore(sid, `销售工具 ${ev.tool}`, turn, 'tool_call', ev.tool)
      break
    case 'sales_tool_result':
      insertSysBefore(sid, `${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    case 'sales_token': {
      ensureSales()
      const sm = findMsg(sid)
      if (sm) { sm.isStreaming = false; sm.content += ev.content || '' }
      break
    }
    case 'sales_message_done': {
      ensureSales()
      const sm = findMsg(sid)
      if (sm) { sm.isStreaming = false; if (!sm.content && ev.content) sm.content = ev.content }
      statusText.value = '客户思考中…'
      ensureCustomer() 
      break
    }
    case 'customer_tool_call':
      ensureSales()
      insertSysBefore(cid, `【客户】工具 ${ev.tool}`, turn, 'tool_call', ev.tool)
      break
    case 'customer_tool_result':
      ensureSales()
      insertSysBefore(cid, `【客户】${ev.tool}: ${(ev.content || '').substring(0, 100)}`, turn, 'tool_result', ev.tool)
      break
    case 'customer_token': {
      ensureCustomer()
      const cm = findMsg(cid)
      if (cm) { cm.isStreaming = false; cm.content += ev.content || '' }
      break
    }
    case 'stage_update': {
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.detected_stage_label || ev.stage_label || stageLabel.value
      ensureCustomer()
      addSys(buildStageText(ev), turn, 'stage_update')
      break
    }
    case 'force_guard':
      addSys(ev.content || '', turn, 'force_guard')
      break
    case 'step_done': {
      ensureSales()
      ensureCustomer()
      const cm = findMsg(cid)
      const sm = findMsg(sid)
      if (cm) { cm.isStreaming = false; if (!cm.content && ev.customer_reply) cm.content = ev.customer_reply }
      if (sm) { sm.isStreaming = false; if (!sm.content && ev.sales_message) sm.content = ev.sales_message }
      turnCount.value = ev.turn_count || turnCount.value
      stageLabel.value = ev.stage_label || stageLabel.value
      if (ev.is_finished) { finishConversation(ev.stage_label || '', turn); stopAutoTimer() }
      else if (ev.is_pending_shutdown) { isPendingShutdown.value = true; addSys('客户已做出决定，下一轮将是最后告别', turn, 'force_guard') }
      break
    }
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
  
  startEvalPolling()
}

/* ========================================
 * 对话结束
 * ======================================== */
function finishConversation(label: string, turn: number) {
  isFinished.value = true
  appStatus.value = 'finished'
  statusText.value = `对话结束：${label}`
  addSys(`训练完成，客户最终状态为「${label}」`, turn, 'stage_update')
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
  evalPollTimer = setInterval(async () => {
    if (!sessionId.value || isFinished.value) return
    try {
      const res = await pollEvaluations(sessionId.value, lastPolledTurn)
      if (res && res.new_evaluations && res.new_evaluations.length > 0) {
        for (const ev of res.new_evaluations) {
          if (!renderedEvalTurns.has(ev.turn)) {
            evaluations.value.push(ev)
            renderedEvalTurns.add(ev.turn)
            lastPolledTurn = Math.max(lastPolledTurn, ev.turn)
          }
        }
      }
    } catch (e) {
      console.error('拉取评分失败', e)
    }
  }, 3000)
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
  isFinished.value = Boolean(data.info.is_finished)
  isHistoryView.value = isFinished.value
  messages.value = data.messages
  evaluations.value = data.evaluations
  finalReport.value = data.finalReport
  turnCount.value = data.info.turn_count || 0
  stageLabel.value = data.info.final_stage || 'INTRODUCTION'
  sessionId.value = data.info.session_id

  lastPolledTurn = evaluations.value.length > 0 ? Math.max(...evaluations.value.map(e => e.turn)) : 0
  renderedEvalTurns.clear()
  evaluations.value.forEach(e => renderedEvalTurns.add(e.turn))

  if (isFinished.value) {
    appStatus.value = 'finished'
    statusText.value = '历史回放（只读）'
  } else {
    appStatus.value = 'ready'
    statusText.value = '会话已恢复，可继续输入或推进'
    startEvalPolling()
  }

  const p = personas.value.find(p => p.name === data.info.persona_id || p.persona_id === data.info.persona_id)
  activePersona.value = p || null

  const pName = p ? p.name : data.info.persona_id
  const sName = strategies.value.find(s => s.strategy_id === data.info.strategy_id)?.name || data.info.strategy_id

  chatTitle.value = `${pName}${sName ? ' × ' + sName : ''}`
  chatSubtitle.value = `历史记录 · ${data.info.turn_count} 轮 · ${data.info.final_stage || '未结束'}`
}

/* ========================================
 * 辅助
 * ======================================== */
function addSys(content: string, turn: number, logType: string, toolName?: string) {
  messages.value.push({ id: mid(), role: 'system', content, turn, logType: logType as any, toolName })
}
function insertSysBefore(beforeId: string, content: string, turn: number, logType: string, toolName?: string) {
  const msg = { id: mid(), role: 'system' as const, content, turn, logType: logType as any, toolName }
  const idx = messages.value.findIndex(m => m.id === beforeId)
  if (idx !== -1) {
    messages.value.splice(idx, 0, msg)
  } else {
    messages.value.push(msg)
  }
}
function findMsg(id: string) { return messages.value.find(m => m.id === id) }

function buildStageText(ev: SSEEvent): string {
  const rawStage = ev.detected_stage_raw || ev.stage || ''
  const finalStage = ev.stage || ''
  const finalLabel = ev.stage_label || ''
  const strike = ev.decision_strike || 0
  const required = ev.decision_strikes_required || 2
  const turn = ev.turn_count || 0

  if (rawStage === finalStage) {
    return `第 ${turn} 轮：客户当前处于「${finalLabel}」阶段`
  }
  
  if (strike === 0) {
     return `客户仍有顾虑，建议先确认需求并回应异议，再尝试推进决定`
  }

  return `客户意向正在确认（${strike}/${required}），下一轮请用开放式问题核实真实决定`
}
</script>

<template>
  <div class="flex h-[100dvh] w-full flex-col overflow-hidden bg-[var(--color-shell)] text-[var(--color-text-primary)] font-sans selection:bg-emerald-100 lg:flex-row lg:py-5 lg:pl-5">
    <AppSidebar
      :current-view="currentView"
      @navigate="navigateTo"
      @new-session="handleNewSession"
      @show-history="openHistory"
    />

    <div
      class="flex min-h-0 min-w-0 w-full flex-1 flex-col pb-16 lg:overflow-hidden lg:pb-0"
    >
      <main v-if="currentView === 'home'" class="min-h-0 flex-1 overflow-y-auto">
        <HomeView
          @start-practice="handleNewSession"
          @navigate-dashboard="currentView = 'dashboard'"
          @show-history="openHistory"
        />
      </main>

      <template v-else-if="currentView === 'practice'">
        <main class="min-h-0 flex-1 overflow-hidden">
          <section class="practice-panel relative flex h-full w-full flex-col overflow-hidden bg-white">
            <div class="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row">
              <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden transition-[flex-basis,width] duration-300 ease-out">
                <header class="z-20 shrink-0 bg-white px-4 pb-3 pt-5 sm:px-6 sm:pt-6 xl:px-8">
                  <TopBar
                    :status="appStatus"
                    :status-text="statusText"
                    :turn-count="turnCount"
                    :stage-label="stageLabel"
                    :session-id="sessionId"
                    :active-persona="activePersona"
                    :eval-open="!isEvalCollapsed"
                    @new-session="handleNewSession"
                    @show-history="openHistory"
                    @show-dashboard="currentView = 'dashboard'"
                    @toggle-evaluation="toggleEvaluation"
                    @back="currentView = 'home'"
                  />
                </header>
                <ChatPanel
                  class="min-h-0 flex-1"
                  :messages="messages"
                  :title="chatTitle"
                  :subtitle="chatSubtitle"
                  :active-persona="activePersona"
                  :disabled="appStatus === 'processing'"
                  :is-finished="isFinished"
                  :is-history-view="isHistoryView"
                  :auto-timer-active="autoTimerActive"
                  @send="handleSend"
                  @step="handleStep"
                  @toggle-auto-timer="toggleAutoTimer"
                  @resume-session="handleResumeSession"
                />
              </div>

              <Transition name="eval-push">
                <aside
                  v-if="!isEvalCollapsed"
                  class="relative min-w-0 shrink-0 bg-white w-full sm:w-[420px]"
                >
                  <EvalPanel
                    :evaluations="evaluations"
                    :final-report="finalReport"
                    :report-loading="reportLoading"
                    :is-finished="isFinished"
                    @close="isEvalCollapsed = true"
                  />
                </aside>
              </Transition>

              <HistoryDrawer
                :visible="showHistory"
                :embedded="true"
                :current-session-id="sessionId"
                :personas="personas"
                :strategies="strategies"
                @close="showHistory = false"
                @view-session="viewHistorySession"
              />
            </div>
          </section>
        </main>
      </template>

      <template v-else>
        <main class="min-h-0 flex-1 overflow-hidden">
          <section class="practice-panel flex h-full w-full flex-col overflow-hidden bg-white">
            <DashboardView />
          </section>
        </main>
      </template>

    </div>

    <SessionSetupModal
      :visible="showSetupModal"
      :personas="personas"
      :strategies="strategies"
      @start="onStart"
      @close="showSetupModal = false"
    />

  </div>
</template>
