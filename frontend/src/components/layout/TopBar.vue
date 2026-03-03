<script setup lang="ts">
import type { AppMode, AppStatus } from '../../types'
import StatusDot from '../common/StatusDot.vue'

defineProps<{
  mode: AppMode
  status: AppStatus
  statusText: string
  turnCount: number
  stageLabel: string
  sessionId: string | null
}>()

defineEmits<{
  (e: 'switch-mode', mode: AppMode): void
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

    <!-- 中间控制区 -->
    <div class="flex items-center gap-6">
      <!-- 模式切换 -->
      <div class="flex bg-surface-muted rounded-lg p-0.5">
        <button
          class="px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200"
          :class="mode === 'manual'
            ? 'bg-surface-card text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'"
          @click="$emit('switch-mode', 'manual')"
        >
          🧑 手动对练
        </button>
        <button
          class="px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200"
          :class="mode === 'auto'
            ? 'bg-surface-card text-text-primary shadow-sm'
            : 'text-text-muted hover:text-text-secondary'"
          @click="$emit('switch-mode', 'auto')"
        >
          🤖 自动对战
        </button>
      </div>
    </div>

    <!-- 右侧状态区 -->
    <div class="flex items-center gap-5 text-xs">
      <div class="flex items-center gap-1.5">
        <StatusDot :status="status" />
        <span class="text-text-secondary">{{ statusText }}</span>
      </div>
      <div class="flex items-center gap-1 text-text-secondary">
        <span>🔄</span>
        <span>回合</span>
        <span class="font-bold text-text-primary ml-0.5">{{ turnCount }}</span>
      </div>
      <div class="text-text-secondary">📍 {{ stageLabel }}</div>
      <div v-if="sessionId" class="text-text-muted font-mono text-[10px]">
        {{ sessionId.substring(0, 8) }}...
      </div>
    </div>
  </header>
</template>
