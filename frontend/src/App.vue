<script setup lang="ts">
import { ref } from 'vue'
import type { AppMode, AppStatus, ChatMessage, Evaluation } from './types'
import { mockPersonas, mockStrategies, mockMessages, mockEvaluations, mockFinalReport } from './mock/data'

import TopBar from './components/layout/TopBar.vue'
import ChatPanel from './components/chat/ChatPanel.vue'
import EvalPanel from './components/evaluation/EvalPanel.vue'
import PersonaModal from './components/modal/PersonaModal.vue'
import StrategyModal from './components/modal/StrategyModal.vue'
import ReportModal from './components/modal/ReportModal.vue'

// ── 全局状态 ──
const appMode = ref<AppMode>('auto')
const appStatus = ref<AppStatus>('ready')
const statusText = ref('就绪')
const turnCount = ref(3)
const stageLabel = ref('⚡ 异议处理')
const sessionId = ref<string | null>('a1b2c3d4-e5f6-7890-abcd-ef1234567890')

// ── 对话数据（Mock 填充） ──
const messages = ref<ChatMessage[]>(mockMessages)
const evaluations = ref<Evaluation[]>(mockEvaluations)

// ── 弹窗状态 ──
const showPersonaModal = ref(false)
const showStrategyModal = ref(false)
const showReportModal = ref(false)

// ── 标题 ──
const chatTitle = ref('🤖 王总 — 企业高管 × 顾问咨询型')
const chatSubtitle = ref('45岁，某上市公司副总裁。反感推销 | 难度: 困难')

// ── 事件处理 ──
function switchMode(mode: AppMode) {
  appMode.value = mode
  if (mode === 'auto') {
    // 在实际应用中，这里会打开策略弹窗
    // showStrategyModal.value = true
  }
}

function handleSend(message: string) {
  // Mock: 添加一条销售消息
  const turn = turnCount.value + 1
  turnCount.value = turn
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'sales',
    content: message,
    turn,
  })
  // Mock: 添加系统提示
  messages.value.push({
    id: `sys-${Date.now()}`,
    role: 'system',
    content: '🤖 客户Agent 正在思考回应...',
    turn,
    logType: 'phase',
  })
  // Mock: 模拟延迟后的客户回复
  setTimeout(() => {
    messages.value.push({
      id: `cust-${Date.now()}`,
      role: 'customer',
      content: '嗯，你说的有些道理，我再想想……',
      turn,
    })
  }, 800)
}

function handleStep() {
  handleSend('[自动销售话术] 根据您的情况，我为您推荐一款高端医疗险...')
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
          :disabled="false"
          :is-finished="false"
          @send="handleSend"
          @step="handleStep"
          @show-report="showReportModal = true"
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
      :personas="mockPersonas"
      @select="(id) => { showPersonaModal = false; sessionId = 'mock-' + id }"
      @close="showPersonaModal = false"
    />

    <StrategyModal
      :visible="showStrategyModal"
      :personas="mockPersonas"
      :strategies="mockStrategies"
      @start="(pid, sid) => { showStrategyModal = false }"
      @close="showStrategyModal = false"
    />

    <ReportModal
      :visible="showReportModal"
      :report="mockFinalReport"
      :loading="false"
      @close="showReportModal = false"
    />
  </div>
</template>
