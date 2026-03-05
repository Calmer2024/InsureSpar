<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DashboardCapabilities } from '../../services/api'

use([CanvasRenderer, RadarChart, TooltipComponent, TitleComponent])

const props = defineProps<{
  data: DashboardCapabilities | null
}>()

const option = computed(() => {
  if (!props.data) return {}
  const { labels, scores } = props.data.radar
  return {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: labels.map((name) => ({ name, max: 10 })),
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#71717A',
        fontSize: 11,
        fontWeight: 500,
      },
      splitLine: { lineStyle: { color: '#E4E4E7' } },
      splitArea: {
        areaStyle: {
          color: ['rgba(255,255,255,0)', 'rgba(244,244,245,0.3)'],
        },
      },
      axisLine: { lineStyle: { color: '#E4E4E7' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: scores,
            name: '综合能力',
            areaStyle: {
              color: 'rgba(74, 222, 128, 0.2)',
            },
            lineStyle: { color: '#4ADE80', width: 2 },
            itemStyle: { color: '#4ADE80' },
          },
        ],
      },
    ],
  }
})
</script>

<template>
  <div class="bg-white rounded-[var(--radius-xl)] shadow-[var(--shadow-card)] border border-[var(--color-border)] p-6 flex flex-col animate-fade-in">
    <h3 class="text-[15px] font-bold text-[var(--color-text-primary)] mb-1">综合能力模型</h3>
    <p class="text-[11px] text-[var(--color-text-muted)] mb-4">基于最近 10 次对练数据</p>

    <div class="flex-1 min-h-0 flex items-center justify-center">
      <VChart
        v-if="data"
        :option="option"
        autoresize
        style="width: 100%; height: 280px;"
      />
      <div v-else class="text-[var(--color-text-muted)] text-sm">加载中...</div>
    </div>
  </div>
</template>
