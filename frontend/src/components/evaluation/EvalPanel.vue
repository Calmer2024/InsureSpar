<script setup lang="ts">
import type { Evaluation, FinalReport } from '../../types'
import EvalCard from './EvalCard.vue'
import FinalReportInline from './FinalReportInline.vue'

defineProps<{
  evaluations: Evaluation[]
  finalReport?: FinalReport | null
  reportLoading?: boolean
  isFinished?: boolean
}>()
</script>

<template>
  <div class="flex flex-col h-full bg-surface">
    <!-- 面板标题 -->
    <div class="px-5 py-3 border-b border-border bg-surface-card shrink-0">
      <h2 class="text-sm font-semibold text-text-primary flex items-center gap-1.5">
        <span class="w-6 h-6 rounded-lg bg-amber-50 flex items-center justify-center text-xs">👓</span>
        考官评分
      </h2>
      <p class="text-xs text-text-muted mt-0.5">每轮实时考官反馈</p>
    </div>

    <!-- 内容 -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      <!-- 终极报告（内联，置顶） -->
      <div v-if="isFinished || reportLoading" class="pb-3 border-b border-border mb-3">
        <FinalReportInline :report="finalReport" :loading="reportLoading" />
      </div>

      <!-- 空状态 -->
      <div v-if="evaluations.length === 0 && !isFinished" class="h-full flex flex-col items-center justify-center">
        <div class="w-12 h-12 rounded-xl bg-surface-muted flex items-center justify-center mb-3">
          <span class="text-2xl">⏳</span>
        </div>
        <p class="text-xs text-text-muted text-center leading-relaxed">
          等待考官评分…<br />
          <span class="text-[10px]">异步运行，约 3~5 秒出分</span>
        </p>
      </div>

      <!-- 评分卡片（倒序） -->
      <EvalCard
        v-for="ev in [...evaluations].reverse()"
        :key="ev.turn"
        :evaluation="ev"
      />
    </div>
  </div>
</template>
