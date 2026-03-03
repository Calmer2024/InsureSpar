<script setup lang="ts">
import type { Evaluation } from '../../types'
import ScoreBar from '../common/ScoreBar.vue'

defineProps<{
  evaluation: Evaluation
}>()

import { ref } from 'vue'
const expanded = ref(false)
</script>

<template>
  <div
    class="bg-surface-card border border-border rounded-xl p-4 animate-slide-in-right transition-shadow duration-200 hover:shadow-[var(--shadow-card-hover)]"
    :style="{ boxShadow: 'var(--shadow-card)' }"
  >
    <!-- 轮次标签 + 平均分 -->
    <div class="flex items-center justify-between mb-3">
      <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-primary-100 text-primary-700 text-[11px] font-bold">
        第 {{ evaluation.turn }} 轮
      </span>
      <span class="text-[11px] text-text-muted">
        均分
        <span class="font-bold text-text-primary ml-0.5">
          {{ ((evaluation.professionalism_score + evaluation.compliance_score + evaluation.strategy_score) / 3).toFixed(1) }}
        </span>
      </span>
    </div>

    <!-- 三维得分条 -->
    <div class="space-y-2">
      <ScoreBar label="专业性" :score="evaluation.professionalism_score" />
      <ScoreBar label="合规性" :score="evaluation.compliance_score" />
      <ScoreBar label="策略性" :score="evaluation.strategy_score" />
    </div>

    <!-- 综合建议 -->
    <div class="mt-3 px-3 py-2 rounded-lg bg-amber-50 text-xs text-amber-700 leading-relaxed">
      💡 {{ evaluation.overall_advice }}
    </div>

    <!-- 展开详细点评 -->
    <button
      class="mt-2 text-[11px] text-text-muted hover:text-primary-600 transition-colors"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起详细 ▲' : '展开详细 ▼' }}
    </button>

    <div v-if="expanded" class="mt-2 space-y-1.5 text-xs text-text-secondary leading-relaxed animate-fade-in">
      <div><span class="font-semibold text-primary-600">💊 专业：</span>{{ evaluation.professionalism_comment }}</div>
      <div><span class="font-semibold text-info">⚖️ 合规：</span>{{ evaluation.compliance_comment }}</div>
      <div><span class="font-semibold text-warning">🎯 策略：</span>{{ evaluation.strategy_comment }}</div>
    </div>
  </div>
</template>
