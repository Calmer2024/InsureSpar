<script setup lang="ts">
import type { Evaluation, FinalReport } from '../../types'
import EvalCard from './EvalCard.vue'
import FinalReportInline from './FinalReportInline.vue'
import { Icon } from '@iconify/vue'

defineProps<{
  evaluations: Evaluation[]
  finalReport: FinalReport | null
  reportLoading?: boolean
  isFinished?: boolean
}>()

defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <div class="flex h-full flex-col bg-white">
    <header class="flex min-h-[84px] shrink-0 items-center justify-between bg-white px-5 pb-3 pt-6">
      <div class="flex items-center gap-2.5">
        <span class="grid h-8 w-8 place-items-center rounded-xl bg-[var(--color-accent-soft)] text-[var(--color-accent-dark)]">
          <Icon icon="lucide:list-checks" class="h-4 w-4" />
        </span>
        <span class="text-[15px] font-semibold text-[var(--color-text-primary)]">实时评估</span>
      </div>
      <button
        type="button"
        aria-label="关闭实时反馈"
        title="关闭实时反馈"
        class="grid h-8 w-8 place-items-center rounded-full text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]"
        @click="$emit('close')"
      >
        <Icon icon="lucide:x" class="h-4 w-4" />
      </button>
    </header>
    <div class="flex-1 overflow-y-auto bg-white px-5 py-5 space-y-4">
      <div v-if="isFinished || reportLoading" class="mb-2">
        <FinalReportInline :report="finalReport" :loading="reportLoading" />
      </div>

      <div v-if="evaluations.length === 0 && !isFinished" class="flex h-full flex-col items-center justify-center text-center animate-fade-in">
        <div class="mb-5 grid h-20 w-20 place-items-center overflow-hidden rounded-[2rem] bg-[var(--color-accent-soft)]">
          <img src="/insurespar_logo.png" alt="InsureSpar" class="h-14 w-14 object-contain" />
        </div>
        <div class="mb-3 grid h-9 w-9 place-items-center rounded-xl bg-[var(--color-accent-soft)] text-[var(--color-accent-dark)]">
          <Icon icon="lucide:list-checks" class="h-5 w-5" />
        </div>
        <p class="text-sm font-medium text-[var(--color-text-primary)]">实时评估</p>
        <p class="mt-1 text-sm font-medium text-[var(--color-text-primary)]">等待首轮交锋</p>
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
