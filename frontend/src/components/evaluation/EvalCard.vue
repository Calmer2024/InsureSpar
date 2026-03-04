<script setup lang="ts">
import type { Evaluation } from '../../types'
import ScoreBar from '../common/ScoreBar.vue'
import { ref } from 'vue'

defineProps<{
  evaluation: Evaluation
}>()

const expanded = ref(false)
</script>

<template>
  <div class="bg-white border border-[var(--color-border)] rounded-2xl p-5 animate-fade-in-up transition-all duration-300 hover:shadow-[var(--shadow-card)]">
    
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border-light)] text-[var(--color-text-primary)] text-[11px] font-bold tracking-wide">
          第 {{ evaluation.turn }} 轮
        </span>
      </div>
      <div class="flex items-baseline gap-1.5 text-[11px] text-[var(--color-text-secondary)] font-medium">
        均分
        <span class="text-lg font-bold text-[var(--color-text-primary)] tabular-nums tracking-tight">
          {{ ((evaluation.professionalism_score + evaluation.compliance_score + evaluation.strategy_score) / 3).toFixed(1) }}
        </span>
      </div>
    </div>

    <div class="space-y-3 mb-4">
      <ScoreBar label="专业性" :score="evaluation.professionalism_score" />
      <ScoreBar label="合规性" :score="evaluation.compliance_score" />
      <ScoreBar label="策略性" :score="evaluation.strategy_score" />
    </div>

    <div class="px-4 py-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-light)] text-xs text-[var(--color-text-primary)] leading-relaxed">
      <span class="font-semibold text-[var(--color-text-secondary)] mr-1">建议</span> 
      {{ evaluation.overall_advice }}
    </div>

    <button
      class="mt-3 w-full flex items-center justify-center gap-1.5 py-1.5 text-[11px] font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors rounded-lg hover:bg-[var(--color-surface)]"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起明细' : '查看维度明细' }}
      <svg class="w-3 h-3 transition-transform duration-200" :class="{ 'rotate-180': expanded }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <div v-if="expanded" class="mt-2 space-y-3 px-1 text-xs text-[var(--color-text-secondary)] leading-relaxed animate-fade-in">
      <div class="pt-2 border-t border-[var(--color-border-light)]">
        <span class="font-bold text-[var(--color-text-primary)] block mb-0.5">专业深度</span>
        {{ evaluation.professionalism_comment }}
      </div>
      <div>
        <span class="font-bold text-[var(--color-text-primary)] block mb-0.5">合规红线</span>
        {{ evaluation.compliance_comment }}
      </div>
      <div>
        <span class="font-bold text-[var(--color-text-primary)] block mb-0.5">推进策略</span>
        {{ evaluation.strategy_comment }}
      </div>
    </div>
  </div>
</template>