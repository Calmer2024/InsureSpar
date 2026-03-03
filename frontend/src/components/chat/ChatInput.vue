<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  disabled?: boolean
  placeholder?: string
  isFinished?: boolean
  autoTimerActive?: boolean
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
}>()

const inputText = ref('')

function handleSend(emit: (e: 'send', msg: string) => void) {
  const msg = inputText.value.trim()
  if (!msg) return
  emit('send', msg)
  inputText.value = ''
}
</script>

<template>
  <!-- 结束状态 -->
  <div v-if="isFinished" class="px-5 py-3 border-t border-border bg-surface-card flex items-center justify-center gap-3 shrink-0">
    <span class="text-xs text-text-muted">对话已结束</span>
  </div>

  <!-- 统一输入区：手动输入 + AI 推进 -->
  <div v-else class="px-5 py-3 border-t border-border bg-surface-card flex gap-3 items-center shrink-0">
    <!-- 文本输入 -->
    <input
      v-model="inputText"
      type="text"
      :placeholder="placeholder || '输入你的销售话术…'"
      :disabled="disabled"
      class="flex-1 bg-surface-muted border border-border-light rounded-xl px-4 py-2.5 text-sm text-text-primary outline-none transition-all duration-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 disabled:opacity-40"
      @keypress.enter="handleSend($emit)"
    />

    <!-- 发送按钮 -->
    <button
      :disabled="disabled || !inputText.trim()"
      class="px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.97] transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
      @click="handleSend($emit)"
    >
      发送
    </button>

    <!-- 分割线 -->
    <div class="w-px h-7 bg-border" />

    <!-- AI 推进按钮 -->
    <button
      :disabled="disabled"
      class="px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
      :class="autoTimerActive
        ? 'bg-primary-500 text-white hover:bg-primary-600'
        : 'border border-border text-text-secondary hover:border-primary-400 hover:text-primary-600 bg-surface-card'"
      @click="$emit('step')"
    >
      ▶ AI 推进
    </button>

    <!-- 自动连续推进 -->
    <button
      :disabled="disabled && !autoTimerActive"
      class="flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 border"
      :class="autoTimerActive
        ? 'bg-primary-500 text-white border-primary-500 shadow-sm shadow-primary-200'
        : 'border-border-light text-text-muted hover:border-primary-300 hover:text-primary-600 bg-surface-card'"
      @click="$emit('toggle-auto-timer')"
    >
      <span
        class="w-2 h-2 rounded-full transition-colors"
        :class="autoTimerActive ? 'bg-white animate-pulse-dot' : 'bg-text-muted'"
      />
      {{ autoTimerActive ? '推进中' : '连续' }}
    </button>
  </div>
</template>
