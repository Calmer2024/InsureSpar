<script setup lang="ts">
import type { FinalReport } from '../../types'
import ScoreBar from '../common/ScoreBar.vue'
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([RadarChart, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  report: FinalReport | null
  loading?: boolean
}>()

const showReview = ref(false)

function scoreColor(v: number): string {
  if (v >= 7) return 'text-score-high'
  if (v >= 4) return 'text-score-mid'
  return 'text-score-low'
}

const radarOption = computed(() => {
  if (!props.report?.radar) return {}
  const { labels, scores } = props.report.radar
  return {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: labels.map((name: string) => ({ name, max: 10 })),
      shape: 'polygon',
      splitNumber: 5,
      radius: '65%',
      axisName: { color: '#64748B', fontSize: 10, fontWeight: 600 },
      splitLine: { lineStyle: { color: '#E2E8F0' } },
      splitArea: {
        areaStyle: {
          color: ['rgba(16,185,129,0.02)', 'rgba(16,185,129,0.04)', 'rgba(16,185,129,0.06)', 'rgba(16,185,129,0.08)', 'rgba(16,185,129,0.10)'],
        },
      },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: scores,
        name: '能力评分',
        lineStyle: { color: '#10B981', width: 2 },
        areaStyle: { color: 'rgba(16,185,129,0.15)' },
        itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 2 },
        symbolSize: 5,
      }],
    }],
  }
})
</script>

<template>
  <!-- 加载中 -->
  <div v-if="loading" class="text-center py-8 animate-fade-in">
    <div class="w-8 h-8 border-2 border-border border-t-primary-500 rounded-full animate-spin mx-auto" />
    <p class="text-xs text-text-muted mt-3">AI 总监生成报告中…</p>
  </div>

  <!-- 报告内容 -->
  <div v-else-if="report" class="animate-fade-in space-y-3">
    <!-- 标题 -->
    <div class="flex items-center gap-2">
      <span class="text-xs font-bold text-primary-600">📊 终极评估</span>
      <span v-if="report.persona_name" class="text-[10px] text-text-muted">{{ report.persona_name }}</span>
    </div>

    <!-- 四维分数 -->
    <div class="grid grid-cols-2 gap-2">
      <div
        v-for="item in [
          { label: '综合', value: report.avg_scores?.total },
          { label: '专业性', value: report.avg_scores?.professionalism },
          { label: '合规性', value: report.avg_scores?.compliance },
          { label: '策略性', value: report.avg_scores?.strategy },
        ]"
        :key="item.label"
        class="bg-surface rounded-lg p-2.5 text-center border border-border"
      >
        <div class="text-lg font-bold" :class="scoreColor(item.value ?? 0)">{{ item.value ?? '-' }}</div>
        <div class="text-[10px] text-text-muted">{{ item.label }}</div>
      </div>
    </div>

    <!-- 雷达图 -->
    <div v-if="report.radar?.labels?.length" class="bg-surface rounded-lg border border-border p-2">
      <v-chart :option="radarOption" style="height: 200px; width: 100%;" autoresize />
    </div>

    <!-- 总监点评（可折叠） -->
    <div v-if="report.review" class="bg-surface rounded-lg border border-border overflow-hidden">
      <button
        class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-text-secondary hover:bg-surface-hover transition"
        @click="showReview = !showReview"
      >
        <span>📝 总监点评</span>
        <span class="text-[10px]">{{ showReview ? '▲' : '▼' }}</span>
      </button>
      <div v-if="showReview" class="px-3 pb-3 text-xs leading-relaxed text-text-primary whitespace-pre-wrap animate-fade-in">
        {{ report.review }}
      </div>
    </div>

    <!-- 逐轮明细（折叠） -->
    <details v-if="report.per_turn_scores?.length" class="bg-surface rounded-lg border border-border overflow-hidden">
      <summary class="px-3 py-2 text-xs font-semibold text-text-secondary cursor-pointer hover:bg-surface-hover transition">
        📋 各轮评分明细
      </summary>
      <div class="px-3 pb-3 space-y-1.5">
        <div
          v-for="t in report.per_turn_scores"
          :key="t.turn"
          class="flex items-center gap-2 text-[11px]"
        >
          <span class="px-1.5 py-0.5 rounded bg-primary-100 text-primary-700 font-bold shrink-0">R{{ t.turn }}</span>
          <span class="text-text-secondary">专{{ t.professionalism }} 合{{ t.compliance }} 策{{ t.strategy }}</span>
          <span v-if="t.advice" class="text-amber-600 truncate flex-1" :title="t.advice">{{ t.advice }}</span>
        </div>
      </div>
    </details>
  </div>
</template>
