<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DashboardGrowth } from '../../services/api'

use([CanvasRenderer, LineChart, TooltipComponent, LegendComponent, GridComponent])

const props = defineProps<{
  data: DashboardGrowth | null
}>()

const SERIES_CONFIG: Record<string, { label: string; color: string }> = {
  total: { label: '综合评分', color: '#4ADE80' },
  professionalism: { label: '专业性', color: '#3B82F6' },
  compliance: { label: '合规性', color: '#F59E0B' },
  strategy: { label: '策略性', color: '#8B5CF6' },
}

const option = computed(() => {
  if (!props.data) return {}
  const { x_axis, series } = props.data

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#E4E4E7',
      borderWidth: 1,
      textStyle: { color: '#09090B', fontSize: 12 },
    },
    legend: {
      data: Object.entries(SERIES_CONFIG)
        .filter(([key]) => key in series)
        .map(([, cfg]) => cfg.label),
      bottom: 0,
      textStyle: { color: '#71717A', fontSize: 11 },
      itemWidth: 16,
      itemHeight: 3,
    },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: x_axis,
      axisLine: { lineStyle: { color: '#E4E4E7' } },
      axisLabel: { color: '#A1A1AA', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      max: 10,
      min: 0,
      splitLine: { lineStyle: { color: '#F4F4F5' } },
      axisLabel: { color: '#A1A1AA', fontSize: 11 },
    },
    series: Object.entries(series)
      .filter(([key]) => key in SERIES_CONFIG)
      .map(([key, values]) => {
        const cfg = SERIES_CONFIG[key]!
        return {
          name: cfg.label,
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: cfg.color, width: key === 'total' ? 3 : 2 },
          itemStyle: { color: cfg.color },
          areaStyle: key === 'total' ? {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${cfg.color}40` },
                { offset: 1, color: `${cfg.color}00` },
              ],
            },
          } : undefined,
          data: values,
        }
      }),
  }
})
</script>

<template>
  <div class="bg-white rounded-[var(--radius-xl)] shadow-[var(--shadow-card)] border border-[var(--color-border)] p-6 flex flex-col animate-fade-in h-full">
    <h3 class="text-[15px] font-bold text-[var(--color-text-primary)] mb-1">能力成长曲线</h3>
    <p class="text-[11px] text-[var(--color-text-muted)] mb-4">点击图例可切换维度</p>

    <div class="flex-1 min-h-0">
      <VChart
        v-if="data"
        :option="option"
        autoresize
        style="width: 100%; height: 300px;"
      />
      <div v-else class="h-[300px] flex items-center justify-center text-[var(--color-text-muted)] text-sm">加载中...</div>
    </div>
  </div>
</template>
