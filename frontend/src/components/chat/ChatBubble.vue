<script setup lang="ts">
import type { ChatMessage } from '../../types'
import { computed, ref } from 'vue'

const props = defineProps<{
  message: ChatMessage
}>()

/** 是否为工具类型消息 */
const isToolMsg = computed(() =>
  props.message.logType === 'tool_call' || props.message.logType === 'tool_result'
)

/** 截断长文本 */
const truncLen = 80
const isTruncated = computed(() => props.message.content.length > truncLen && props.message.role === 'system')
const expanded = ref(false)
const displayContent = computed(() => {
  if (props.message.role !== 'system') return props.message.content
  if (expanded.value || props.message.content.length <= truncLen) return props.message.content
  return props.message.content.substring(0, truncLen) + '...'
})
</script>

<template>
  <div
    v-if="message.role === 'sales'"
    class="flex justify-end animate-fade-in mb-4" 
  >
    <div class="max-w-[80%] flex flex-col items-end">
      <span class="text-[11px] font-medium text-[var(--color-text-muted)] mb-1.5 mr-1">销售代理</span>
      <div class="px-4 py-3 rounded-2xl rounded-br-sm bg-gradient-to-br from-zinc-800 to-zinc-950 text-white text-sm leading-relaxed shadow-sm">
        {{ message.content }}
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1 ml-1 align-middle">
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>

  <div
    v-else-if="message.role === 'customer'"
    class="flex justify-start animate-fade-in mb-4"
  >
    <div class="max-w-[80%] flex flex-col items-start">
      <span class="text-[11px] font-medium text-[var(--color-text-muted)] mb-1.5 ml-1">模拟客户</span>
      <div class="px-4 py-3 rounded-2xl rounded-bl-sm bg-white border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] leading-relaxed shadow-sm">
        {{ message.content }}
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1 ml-1 align-middle">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)]" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)]" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)]" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>

  <div
    v-else-if="message.role === 'system'"
    class="flex justify-center animate-fade-in my-2"
  >
    <div
      class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] leading-snug max-w-[85%] cursor-default border"
      :class="{
        'bg-zinc-900 text-zinc-100 border-zinc-800 shadow-sm': message.logType === 'stage_update',
        'bg-red-50 text-red-600 border-red-100': message.logType === 'force_guard',
        'bg-[var(--color-surface-muted)] text-[var(--color-text-secondary)] border-transparent': !message.logType || message.logType === 'phase' || message.logType === 'status',
        'bg-white text-[var(--color-text-secondary)] border-[var(--color-border)] shadow-sm': isToolMsg,
      }"
      @click="isTruncated && (expanded = !expanded)"
    >
      <span class="truncate transition-all duration-200" :class="{'whitespace-normal': expanded}">{{ displayContent }}</span>
      <button
        v-if="isTruncated"
        class="ml-1 shrink-0 text-[10px] font-medium opacity-60 hover:opacity-100 transition-opacity"
      >
        {{ expanded ? '收起' : '展开' }}
      </button>
    </div>
  </div>
</template>