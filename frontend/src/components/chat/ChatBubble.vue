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
  <!-- 销售消息 -->
  <div
    v-if="message.role === 'sales'"
    class="flex justify-end animate-fade-in"
  >
    <div class="max-w-[75%] flex flex-col items-end">
      <span class="text-[10px] font-medium text-text-muted mb-1 mr-1">销售</span>
      <div class="px-4 py-3 rounded-2xl rounded-br-md bg-gradient-to-br from-primary-500 to-primary-600 text-white text-sm leading-relaxed shadow-sm">
        {{ message.content }}
        <!-- 打字指示器 -->
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1 ml-1 align-middle">
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-1.5 h-1.5 rounded-full bg-white/60" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>

  <!-- 客户消息 -->
  <div
    v-else-if="message.role === 'customer'"
    class="flex justify-start animate-fade-in"
  >
    <div class="max-w-[75%] flex flex-col items-start">
      <span class="text-[10px] font-medium text-text-muted mb-1 ml-1">客户</span>
      <div class="px-4 py-3 rounded-2xl rounded-bl-md bg-surface-card border border-border text-sm leading-relaxed shadow-sm">
        {{ message.content }}
        <!-- 打字指示器 -->
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1 ml-1 align-middle">
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>

  <!-- 系统日志（简洁内联） -->
  <div
    v-else-if="message.role === 'system'"
    class="flex justify-center animate-fade-in"
  >
    <div
      class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] leading-snug max-w-[85%] cursor-default"
      :class="{
        'bg-primary-50/80 text-primary-600': message.logType === 'stage_update',
        'bg-red-50/80 text-red-500': message.logType === 'force_guard',
        'bg-surface-muted text-text-muted': !message.logType || message.logType === 'phase' || message.logType === 'status',
        'bg-stone-100 text-stone-500': isToolMsg,
      }"
      @click="isTruncated && (expanded = !expanded)"
    >
      <span class="truncate">{{ displayContent }}</span>
      <button
        v-if="isTruncated"
        class="ml-1 shrink-0 text-[10px] underline opacity-60 hover:opacity-100"
      >
        {{ expanded ? '收起' : '展开' }}
      </button>
    </div>
  </div>
</template>
