<script setup lang="ts">
defineProps<{
  disabled?: boolean
  placeholder?: string
  mode?: 'manual' | 'auto'
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
}>()

import { ref } from 'vue'

const inputText = ref('')

function handleSend(emit: (e: 'send', msg: string) => void) {
  const msg = inputText.value.trim()
  if (!msg) return
  emit('send', msg)
  inputText.value = ''
}
</script>

<template>
  <!-- 手动模式输入区 -->
  <div v-if="mode !== 'auto'" class="px-5 py-3 border-t border-border bg-surface-card flex gap-3 items-center shrink-0">
    <input
      v-model="inputText"
      type="text"
      :placeholder="placeholder || '输入你的销售话术...'"
      :disabled="disabled"
      class="flex-1 bg-surface-muted border border-border-light rounded-xl px-4 py-2.5 text-sm text-text-primary outline-none transition-all duration-200 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 disabled:opacity-40"
      @keypress.enter="handleSend($emit)"
    />
    <button
      :disabled="disabled || !inputText.trim()"
      class="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.98] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
      @click="handleSend($emit)"
    >
      发送
    </button>
  </div>

  <!-- 自动模式控制区 -->
  <div v-else class="px-5 py-3 border-t border-border bg-surface-card flex items-center gap-3 shrink-0">
    <button
      :disabled="disabled"
      class="px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.98] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
      @click="$emit('step')"
    >
      ▶ 下一步
    </button>
    <button
      class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border text-xs text-text-secondary hover:border-primary-400 hover:text-primary-600 transition-all duration-150"
      @click="$emit('toggle-auto-timer')"
    >
      <span class="w-2 h-2 rounded-full bg-current" />
      自动推进
    </button>
    <span class="flex-1" />
    <button
      class="px-3 py-2 rounded-lg bg-surface-muted border border-border-light text-xs text-text-muted hover:text-text-secondary transition"
    >
      ⚙️ 重新配置
    </button>
  </div>
</template>
