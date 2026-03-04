<script setup lang="ts">
import type { Evaluation, FinalReport } from '../../types'
import EvalCard from './EvalCard.vue'
import FinalReportInline from './FinalReportInline.vue'

defineProps<{
  evaluations: Evaluation[]
  finalReport: FinalReport | null
  reportLoading?: boolean
  isFinished?: boolean
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-white">
    <div class="px-6 py-4 border-b border-[var(--color-border)] bg-white shrink-0 flex flex-col justify-center">
      <h2 class="text-base font-semibold text-[var(--color-text-primary)] tracking-tight flex items-center gap-2">
        <div class="w-6 h-6 rounded-md bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
          <svg class="w-3.5 h-3.5 text-[var(--color-text-primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
        </div>
        实时评估
      </h2>
      <p class="text-xs text-[var(--color-text-secondary)] mt-1">AI 考官将根据每轮话术给出反馈</p>
    </div>

    <div class="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-[var(--color-surface)]">
      <div v-if="isFinished || reportLoading" class="mb-2">
        <FinalReportInline :report="finalReport" :loading="reportLoading" />
      </div>

      <div v-if="evaluations.length === 0 && !isFinished" class="h-full flex flex-col items-center justify-center animate-fade-in">
        <div class="w-14 h-14 rounded-2xl bg-white border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-4">
          <svg class="w-6 h-6 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-sm font-medium text-[var(--color-text-primary)]">等待首轮交锋</p>
        <p class="text-xs text-[var(--color-text-secondary)] text-center mt-1.5">
          发送消息后<br />考官评估结果将在此显示
        </p>
      </div>

      <div class="space-y-4">
        <EvalCard
          v-for="ev in [...evaluations].reverse()"
          :key="ev.turn"
          :evaluation="ev"
        />
      </div>
    </div>
  </div>
</template>