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
  <div class="flex flex-col h-full min-w-0 bg-white">
    <div class="px-6 py-4 border-b border-[var(--color-border)] bg-white shrink-0 flex flex-col justify-center">
      <h2 class="text-base font-semibold text-[var(--color-text-primary)] tracking-tight">{{ title }}</h2>
      <p class="text-xs text-[var(--color-text-secondary)] mt-1">{{ subtitle }}</p>
    </div>

    <div ref="chatContainer" class="flex-1 overflow-y-auto px-6 py-6">
      <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center animate-fade-in">
        <div class="w-16 h-16 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-light)] flex items-center justify-center mb-5 shadow-sm">
          <svg class="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h3 class="text-sm font-medium text-[var(--color-text-primary)]">选择客户画像与策略</h3>
        <p class="text-xs text-[var(--color-text-secondary)] mt-2 max-w-[200px]">配置完成后即可开始对练，支持手动输入和 AI 自动推进</p>
      </div>

      <template v-for="group in groupedMessages" :key="group.turn">
        <RoundDivider v-if="group.turn > 0" :turn="group.turn" />
        <div class="space-y-1">
          <ChatBubble
            v-for="msg in group.messages"
            :key="msg.id"
            :message="msg"
          />
        </div>
      </template>
    </div>

    <div v-if="isHistoryView && !isFinished" class="px-6 py-5 border-t border-[var(--color-border)] bg-[var(--color-surface-hover)] flex flex-col items-center justify-center shrink-0">
      <p class="text-xs text-[var(--color-text-secondary)] mb-4">本次对练未正常结束，你可以随时从此处恢复对话</p>
      <button class="cta-btn" @click="$emit('resume-session')">
        恢复继续对练
      </button>
    </div>

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