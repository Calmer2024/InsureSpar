<script setup lang="ts">
import type { ChatMessage } from '../../types'

defineProps<{
  message: ChatMessage
}>()

/** 系统日志图标映射 */
function logIcon(logType?: string): string {
  switch (logType) {
    case 'phase': return '⏳'
    case 'status': return '📡'
    case 'tool_call': return '🔍'
    case 'tool_result': return '✅'
    case 'stage_update': return '📍'
    case 'force_guard': return '🛡️'
    default: return '💬'
  }
}
</script>

<template>
  <!-- 销售消息 -->
  <div
    v-if="message.role === 'sales'"
    class="flex justify-end animate-fade-in"
  >
    <div class="max-w-[75%] flex flex-col items-end">
      <span class="text-[10px] font-semibold text-text-muted mb-1 mr-1 uppercase tracking-wide">
        🧑 {{ message.turn ? '销售' : '' }}
      </span>
      <div class="px-4 py-3 rounded-2xl rounded-br-md bg-gradient-to-br from-primary-500 to-primary-600 text-white text-sm leading-relaxed shadow-sm">
        {{ message.content }}
      </div>
    </div>
  </div>

  <!-- 客户消息 -->
  <div
    v-else-if="message.role === 'customer'"
    class="flex justify-start animate-fade-in"
  >
    <div class="max-w-[75%] flex flex-col items-start">
      <span class="text-[10px] font-semibold text-text-muted mb-1 ml-1 uppercase tracking-wide">
        👤 客户
      </span>
      <div class="px-4 py-3 rounded-2xl rounded-bl-md bg-surface-card border border-border text-sm leading-relaxed shadow-sm">
        {{ message.content }}
        <!-- 打字指示器 -->
        <span v-if="message.isStreaming" class="inline-flex gap-1 ml-2 align-middle">
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-1.5 h-1.5 rounded-full bg-text-muted" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>

  <!-- 系统日志（内联浅色展示） -->
  <div
    v-else-if="message.role === 'system'"
    class="flex justify-center animate-fade-in"
  >
    <div
      class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] leading-snug"
      :class="{
        'bg-primary-50 text-primary-600': message.logType === 'stage_update',
        'bg-amber-50 text-amber-600': message.logType === 'tool_call',
        'bg-emerald-50 text-emerald-600': message.logType === 'tool_result',
        'bg-red-50 text-red-500': message.logType === 'force_guard',
        'bg-surface-muted text-text-muted': !message.logType || message.logType === 'phase' || message.logType === 'status',
      }"
    >
      <span>{{ logIcon(message.logType) }}</span>
      <span>{{ message.content }}</span>
    </div>
  </div>
</template>
