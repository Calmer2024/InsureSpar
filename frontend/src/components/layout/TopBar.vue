<script setup lang="ts">
import type { AppStatus } from '../../types'
import StatusDot from '../common/StatusDot.vue'

defineProps<{
  status: AppStatus
  statusText: string
  turnCount: number
  stageLabel: string
  sessionId: string | null
}>()

defineEmits<{
  (e: 'new-session'): void
  (e: 'show-history'): void
}>()
</script>

<template>
  <div class="w-full flex items-center justify-between h-10">
    
    <div class="flex items-center gap-3 shrink-0">
      <div class="w-9 h-9 rounded-xl overflow-hidden shadow-sm border border-zinc-200">
        <img src="/logo.png" alt="InsureSpar Logo" class="w-full h-full object-cover" />
      </div>
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <span class="text-lg font-bold text-[var(--color-text-primary)] tracking-tight leading-none">InsureSpar</span>
          <span class="px-1.5 py-0.5 rounded-md bg-[var(--color-surface-muted)] text-[9px] font-bold text-[var(--color-text-secondary)] tracking-widest uppercase">
            Beta
          </span>
        </div>
        <span class="text-[11px] text-[var(--color-text-muted)] font-medium mt-1 leading-none">保险销售对练系统</span>
      </div>
    </div>

    <div class="hidden md:flex flex-1 items-center justify-center gap-3 text-xs">
      
      <div class="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[var(--color-border)] shadow-sm transition-all duration-300">
        <StatusDot :status="status" />
        <span class="text-[var(--color-text-primary)] font-medium truncate max-w-[160px]">{{ statusText }}</span>
      </div>

      <div v-if="turnCount > 0" class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--color-surface)] border border-[var(--color-border-light)] text-[var(--color-text-secondary)] font-medium animate-fade-in">
        <span>回合</span>
        <span class="text-[var(--color-text-primary)] font-bold tabular-nums">{{ turnCount }}</span>
      </div>

      <div v-if="sessionId" class="flex items-center px-3 py-1.5 rounded-full bg-[var(--color-surface)] border border-[var(--color-border-light)] text-[var(--color-text-secondary)] font-medium truncate max-w-[140px] animate-fade-in">
        {{ stageLabel }}
      </div>

      <div v-if="sessionId" class="font-mono text-[10px] text-[var(--color-text-muted)] opacity-50 hover:opacity-100 transition-opacity cursor-default animate-fade-in ml-2">
        #{{ sessionId.substring(0, 8) }}
      </div>
    </div>

    <div class="flex items-center gap-3 shrink-0">
      <button
        class="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all shadow-sm active:scale-[0.98]"
        @click="$emit('show-history')"
      >
        <svg class="w-4 h-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        历史
      </button>

      <button
        class="cta-btn gap-1.5 px-5"
        @click="$emit('new-session')"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新对练
      </button>
    </div>

  </div>
</template>