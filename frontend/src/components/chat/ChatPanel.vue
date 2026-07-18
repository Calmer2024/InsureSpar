<script setup lang="ts">
import type { ChatMessage, Persona } from '../../types'
import { computed, nextTick, ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
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
  activePersona?: Persona | null
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
  (e: 'resume-session'): void
}>()

const chatContainer = ref<HTMLElement>()
const strategyName = computed(() => props.title.split(' × ')[1] || '常规对话')

const groupedMessages = computed(() => {
  const groups: { turn: number; messages: ChatMessage[] }[] = []
  let currentTurn = -1
  for (const msg of props.messages) {
    if (msg.turn !== currentTurn) {
      currentTurn = msg.turn
      groups.push({ turn: currentTurn, messages: [] })
    }
    const lastGroup = groups[groups.length - 1]
    if (lastGroup) lastGroup.messages.push(msg)
  }
  return groups
})

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
  },
)
</script>

<template>
  <div class="relative flex h-full min-w-0 flex-col overflow-hidden bg-white">
    <div ref="chatContainer" class="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-6 xl:px-8">
      <div
        v-if="messages.length === 0"
        class="flex h-full flex-col items-center justify-center pb-10 text-center animate-fade-in"
      >
        <div class="mb-6 flex h-20 w-20 items-center justify-center rounded-[2rem] bg-[var(--color-accent-soft)] shadow-sm">
          <Icon icon="lucide:messages-square" class="h-10 w-10 text-[var(--color-accent)]" />
        </div>
        <h3 class="text-[16px] font-bold text-gray-800">对练已就绪</h3>
        <p class="mt-2 max-w-[240px] text-xs leading-relaxed text-gray-400">
          系统已加载《{{ strategyName }}》策略<br />请输入话术或点击底部按钮推进。
        </p>
      </div>

      <template v-for="group in groupedMessages" :key="group.turn">
        <RoundDivider v-if="group.turn > 0" :turn="group.turn" />
        <div class="space-y-1">
          <ChatBubble
            v-for="msg in group.messages"
            :key="msg.id"
            :message="msg"
            :active-persona="activePersona"
          />
        </div>
      </template>
    </div>

    <ChatInput
      :disabled="disabled || isFinished || isHistoryView"
      :is-finished="isFinished"
      :auto-timer-active="autoTimerActive"
      @send="$emit('send', $event)"
      @step="$emit('step')"
      @toggle-auto-timer="$emit('toggle-auto-timer')"
    />
  </div>
</template>
