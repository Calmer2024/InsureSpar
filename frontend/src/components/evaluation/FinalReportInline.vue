<script setup lang="ts">
import type { FinalReport } from '../../types'
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

const showReview = ref(true) // 默认展开总点评

// 分数颜色：使用更现代的色带
function scoreColor(v: number): string {
  if (v >= 7) return 'text-[var(--color-score-high)]'
  if (v >= 4) return 'text-[var(--color-score-mid)]'
  return 'text-[var(--color-score-low)]'
}

// 雷达图配置：高级黑白灰主题 (Shadcn 风格)
const radarOption = computed(() => {
  if (!props.report?.radar) return {}
  const { labels, scores } = props.report.radar
  return {
    tooltip: { 
      trigger: 'item',
      backgroundColor: '#ffffff',
      borderColor: '#E4E4E7',
      textStyle: { color: '#09090B', fontSize: 12 },
      padding: [8, 12],
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;'
    },
    radar: {
      indicator: labels.map((name: string) => ({ name, max: 10 })),
      shape: 'polygon',
      splitNumber: 4,
      radius: '60%',
      axisName: { color: '#71717A', fontSize: 11, fontWeight: 500 }, // zinc-500
      splitLine: { lineStyle: { color: '#E4E4E7' } }, // zinc-200
      splitArea: {
        areaStyle: {
          color: ['#FAFAFB', '#F4F4F5', '#FAFAFB', '#F4F4F5'], // 交替浅灰
        },
      },
      axisLine: { lineStyle: { color: '#E4E4E7' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: scores,
        name: '能力维度',
        lineStyle: { color: '#18181B', width: 2 }, // zinc-900
        areaStyle: { color: 'rgba(24, 24, 27, 0.08)' }, 
        itemStyle: { color: '#18181B', borderColor: '#ffffff', borderWidth: 2 },
        symbolSize: 6,
      }],
    }],
  }
})
</script>

<template>
  <div v-if="loading" class="bg-white border border-[var(--color-border)] rounded-2xl p-8 text-center animate-fade-in shadow-sm">
    <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-zinc-900 rounded-full animate-spin mx-auto mb-4" />
    <p class="text-sm font-medium text-[var(--color-text-primary)]">生成终极报告中</p>
    <p class="text-xs text-[var(--color-text-muted)] mt-1">正在汇总全盘表现...</p>
  </div>

  <div v-else-if="report" class="bg-white border border-zinc-200 rounded-2xl p-5 shadow-sm animate-fade-in space-y-5">
    
    <div class="flex flex-col border-b border-[var(--color-border-light)] pb-4">
      <h3 class="text-base font-bold text-[var(--color-text-primary)] tracking-tight">终极评估报告</h3>
      <span v-if="report.persona_name" class="text-xs text-[var(--color-text-secondary)] mt-1">
        对练对象：{{ report.persona_name }}
      </span>
    </div>

    <div class="grid grid-cols-4 gap-2">
      <div
        v-for="item in [
          { label: '综合', value: report.avg_scores?.total },
          { label: '专业', value: report.avg_scores?.professionalism },
          { label: '合规', value: report.avg_scores?.compliance },
          { label: '策略', value: report.avg_scores?.strategy },
        ]"
        :key="item.label"
        class="bg-[var(--color-surface)] rounded-xl p-3 text-center border border-[var(--color-border-light)]"
      >
        <div class="text-lg font-bold tabular-nums" :class="scoreColor(item.value ?? 0)">{{ item.value ?? '-' }}</div>
        <div class="text-[10px] text-[var(--color-text-secondary)] font-medium mt-0.5">{{ item.label }}</div>
      </div>
    </div>

    <div v-if="report.radar?.labels?.length" class="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border-light)] p-2">
      <v-chart :option="radarOption" style="height: 220px; width: 100%;" autoresize />
    </div>

    <div v-if="report.review" class="rounded-xl border border-[var(--color-border)] overflow-hidden">
      <button
        class="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-[var(--color-surface-hover)] transition-colors"
        @click="showReview = !showReview"
      >
        <span class="text-sm font-semibold text-[var(--color-text-primary)]">考官总评</span>
        <svg class="w-4 h-4 text-[var(--color-text-muted)] transition-transform duration-200" :class="{ 'rotate-180': showReview }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div v-if="showReview" class="px-4 pb-4 bg-white text-sm leading-relaxed text-[var(--color-text-secondary)] whitespace-pre-wrap border-t border-[var(--color-border-light)] pt-3">
        {{ report.review }}
      </div>
    </div>

    <details v-if="report.per_turn_scores?.length" class="group rounded-xl border border-[var(--color-border)] overflow-hidden bg-white">
      <summary class="flex items-center justify-between px-4 py-3 text-sm font-semibold text-[var(--color-text-primary)] cursor-pointer hover:bg-[var(--color-surface-hover)] transition-colors list-none [&::-webkit-details-marker]:hidden">
        各轮评分明细
        <svg class="w-4 h-4 text-[var(--color-text-muted)] transition-transform duration-200 group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </summary>
      <div class="px-3 pb-3 pt-1 border-t border-[var(--color-border-light)] space-y-2 max-h-[200px] overflow-y-auto">
        <div
          v-for="t in report.per_turn_scores"
          :key="t.turn"
          class="flex items-start gap-2 text-xs p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
        >
          <span class="px-1.5 py-0.5 rounded border border-zinc-200 bg-zinc-50 text-zinc-700 font-bold shrink-0 tabular-nums">R{{ t.turn }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-[var(--color-text-primary)] font-medium mb-0.5 flex gap-2">
              <span>专: {{ t.professionalism }}</span>
              <span>合: {{ t.compliance }}</span>
              <span>策: {{ t.strategy }}</span>
            </div>
            <div v-if="t.advice" class="text-[var(--color-text-secondary)] line-clamp-2" :title="t.advice">{{ t.advice }}</div>
          </div>
        </div>
      </div>
    </details>
  </div>
</template>