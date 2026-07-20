<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
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
  <div class="flex h-full min-h-0 flex-col p-5 animate-fade-in">
    <div class="flex items-center gap-2">
      <span class="grid h-8 w-8 place-items-center rounded-xl bg-[var(--color-accent-soft)] text-[var(--color-accent-dark)]"><Icon icon="lucide:radar" class="h-4 w-4" /></span>
      <h3 class="text-[17px] font-bold text-[var(--color-text-primary)]">综合能力模型</h3>
    </div>
    <p class="text-[11px] text-[var(--color-text-muted)] mb-4">基于最近 10 次对练数据</p>

    <div class="flex-1 min-h-0 flex items-center justify-center">
      <VChart
        v-if="data"
        :option="option"
        autoresize
        style="width: 100%; height: 100%; min-height: 120px;"
      />
      <div v-else class="text-[var(--color-text-muted)] text-sm">加载中...</div>
    </div>
  </div>
</template>
