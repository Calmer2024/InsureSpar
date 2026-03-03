<script setup lang="ts">
import type { ChatMessage, AppMode } from '../../types'
import { computed, nextTick, ref, watch } from 'vue'
import ChatBubble from './ChatBubble.vue'
import RoundDivider from './RoundDivider.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  messages: ChatMessage[]
  mode: AppMode
  title: string
  subtitle: string
  disabled?: boolean
  isFinished?: boolean
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
  (e: 'show-report'): void
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
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
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
        <p class="text-sm text-text-secondary">{{ mode === 'auto' ? '选择画像与策略，开始自动对战' : '选择客户画像开始对练' }}</p>
      </div>

      <!-- 按轮次渲染消息 -->
      <template v-for="group in groupedMessages" :key="group.turn">
        <RoundDivider :turn="group.turn" />
        <div class="space-y-2.5">
          <ChatBubble
            v-for="msg in group.messages"
            :key="msg.id"
            :message="msg"
          />
        </div>
      </template>

      <!-- 结束按钮 -->
      <div v-if="isFinished" class="flex justify-center pt-4">
        <button
          class="px-6 py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 shadow-sm"
          @click="$emit('show-report')"
        >
          📊 查看终极评估报告
        </button>
      </div>
    </div>

    <!-- 输入区 -->
    <ChatInput
      :mode="mode"
      :disabled="disabled || isFinished"
      @send="$emit('send', $event)"
      @step="$emit('step')"
      @toggle-auto-timer="$emit('toggle-auto-timer')"
    />
  </div>
</template>
