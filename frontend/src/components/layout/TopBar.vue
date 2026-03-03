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
}>()
</script>

<template>
  <header class="h-14 bg-surface-card border-b border-border flex items-center justify-between px-6 shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
        <span class="text-white text-sm font-bold">IS</span>
      </div>
      <span class="text-base font-bold text-text-primary tracking-tight">InsureSpar</span>
      <span class="text-xs text-text-muted font-medium ml-1">对练平台</span>
    </div>

    <!-- 中间 -->
    <div class="flex items-center gap-3">
      <button
        class="px-4 py-1.5 rounded-lg bg-gradient-to-r from-primary-500 to-primary-600 text-xs font-bold text-white hover:opacity-90 active:scale-[0.97] transition-all shadow-sm"
        @click="$emit('new-session')"
      >
        ＋ 新对练
      </button>
    </div>

    <!-- 右侧状态 -->
    <div class="flex items-center gap-5 text-xs">
      <div class="flex items-center gap-1.5">
        <StatusDot :status="status" />
        <span class="text-text-secondary truncate max-w-[140px]">{{ statusText }}</span>
      </div>
      <div v-if="turnCount > 0" class="flex items-center gap-1 text-text-secondary">
        <span>回合</span>
        <span class="font-bold text-text-primary">{{ turnCount }}</span>
      </div>
      <div v-if="sessionId" class="text-text-secondary truncate max-w-[150px]">
        {{ stageLabel }}
      </div>
      <div v-if="sessionId" class="text-text-muted font-mono text-[10px]">
        {{ sessionId.substring(0, 8) }}
      </div>
    </div>
  </header>
</template>
