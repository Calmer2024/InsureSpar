<script setup lang="ts">
import type { ChatMessage } from '../../types'
import { computed, nextTick, ref, watch } from 'vue'
import ChatBubble from './ChatBubble.vue'
import RoundDivider from './RoundDivider.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  messages: ChatMessage[]
  title: string
  subtitle: string
  disabled?: boolean
  isFinished?: boolean
  isHistoryView?: boolean
  autoTimerActive?: boolean
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
  (e: 'resume-session'): void
}>()

const chatContainer = ref<HTMLElement>()

/** 按轮次分组消息 */
const groupedMessages = computed(() => {
  const groups: { turn: number; messages: ChatMessage[] }[] = []
  let currentTurn = -1

  for (const msg of props.messages) {
    if (msg.turn !== currentTurn) {
      currentTurn = msg.turn
      groups.push({ turn: currentTurn, messages: [] })
    }
    groups[groups.length - 1].messages.push(msg)
  }
  return groups
})

/** 自动滚动到底部 */
watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: 'smooth',
      })
    }
  }
)
</script>

<template>
  <div class="flex flex-col h-full min-w-0">
    <!-- 对话头部 -->
    <div class="px-5 py-3 border-b border-border bg-surface-card shrink-0">
      <h2 class="text-sm font-semibold text-text-primary">{{ title }}</h2>
      <p class="text-xs text-text-secondary mt-0.5">{{ subtitle }}</p>
    </div>

    <!-- 消息区域 -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto px-5 py-4 space-y-1">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-4">
          <span class="text-3xl">💬</span>
        </div>
        <p class="text-sm text-text-secondary">选择客户画像与销售策略开始对练</p>
        <p class="text-xs text-text-muted mt-1">支持手动输入和 AI 自动推进</p>
      </div>

      <!-- 按轮次渲染消息 -->
      <template v-for="group in groupedMessages" :key="group.turn">
        <RoundDivider v-if="group.turn > 0" :turn="group.turn" />
        <div class="space-y-2">
          <ChatBubble
            v-for="msg in group.messages"
            :key="msg.id"
            :message="msg"
          />
        </div>
      </template>
    </div>

    <!-- 历史记录未结束状态下的恢复按钮 -->
    <div v-if="isHistoryView && !isFinished" class="px-5 py-4 border-t border-border bg-surface-card flex flex-col items-center justify-center shrink-0">
      <p class="text-xs text-text-secondary mb-3">本次对练未正常结束，你可以随时从此处恢复对话</p>
      <button
        class="px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.97] transition-all shadow-md"
        @click="$emit('resume-session')"
      >
        恢复继续对练
      </button>
    </div>

    <!-- 正常输入区 -->
    <ChatInput
      v-else
      :disabled="disabled || isFinished || isHistoryView"
      :is-finished="isFinished"
      :auto-timer-active="autoTimerActive"
      @send="$emit('send', $event)"
      @step="$emit('step')"
      @toggle-auto-timer="$emit('toggle-auto-timer')"
    />
  </div>
</template>
