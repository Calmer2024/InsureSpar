<script setup lang="ts">
import { ref } from 'vue'
import ToolboxPanel from '../tools/ToolboxPanel.vue'

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
const showToolbox = ref(false)

function handleSend(emit: (e: 'send', msg: string) => void) {
  const msg = inputText.value.trim()
  if (!msg) return
  emit('send', msg)
  inputText.value = ''
}
</script>

<template>
  <div v-if="isFinished" class="px-6 py-4 border-t border-[var(--color-border)] bg-white flex items-center justify-center shrink-0">
    <span class="text-sm text-[var(--color-text-muted)] font-medium">对话已结束</span>
  </div>

  <div v-else class="relative shrink-0">
    <ToolboxPanel
      :visible="showToolbox"
      @close="showToolbox = false"
    />

    <div class="px-6 py-4 border-t border-[var(--color-border)] bg-white flex gap-3 items-center">
      <button
        :disabled="disabled"
        class="w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-200 border"
        :class="showToolbox
          ? 'bg-zinc-900 text-white border-zinc-900 rotate-45 shadow-sm'
          : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)] bg-white'"
        @click="showToolbox = !showToolbox"
        title="工具箱"
      >
        <svg v-if="showToolbox" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <svg v-else class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.573-1.066z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>

      <input
        v-model="inputText"
        type="text"
        :placeholder="placeholder || '输入你的销售话术…'"
        :disabled="disabled"
        class="flex-1 bg-[var(--color-surface)] border border-[var(--color-border-light)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-text-primary)] outline-none transition-all duration-200 focus:bg-white focus:border-zinc-300 focus:ring-2 focus:ring-zinc-900/10 disabled:opacity-50"
        @keypress.enter="handleSend($emit)"
        @focus="showToolbox = false"
      />

      <button
        :disabled="disabled || !inputText.trim()"
        class="cta-btn disabled:opacity-40 disabled:cursor-not-allowed"
        @click="handleSend($emit)"
      >
        发送
      </button>

      <div class="w-px h-6 bg-[var(--color-border)] mx-1" />

      <button
        :disabled="disabled"
        class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed border"
        :class="autoTimerActive
          ? 'bg-zinc-900 text-white border-zinc-900 shadow-sm'
          : 'bg-white border-[var(--color-border)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] shadow-sm'"
        @click="$emit('step')"
      >
        AI 推进
      </button>

      <button
        :disabled="disabled && !autoTimerActive"
        class="flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 border"
        :class="autoTimerActive
          ? 'bg-zinc-100 text-zinc-900 border-zinc-200 shadow-inner'
          : 'bg-white border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)]'"
        @click="$emit('toggle-auto-timer')"
      >
        <span
          class="w-2 h-2 rounded-full transition-colors"
          :class="autoTimerActive ? 'bg-zinc-900 animate-pulse-dot' : 'bg-[var(--color-text-muted)]'"
        />
        {{ autoTimerActive ? '推进中' : '连续' }}
      </button>
    </div>
  </div>
</template>