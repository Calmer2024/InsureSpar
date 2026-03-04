<script setup lang="ts">
import type { FinalReport } from '../../types'
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  visible: boolean
  report: FinalReport | null
  loading?: boolean
}>()

defineEmits<{
  (e: 'close'): void
}>()

function scoreColor(v: number): string {
  if (v >= 7) return 'text-[var(--color-score-high)]'
  if (v >= 4) return 'text-[var(--color-score-mid)]'
  return 'text-[var(--color-score-low)]'
}

/** ECharts 雷达图配置 (与 Inline 保持一致的高级黑灰) */
const radarOption = computed(() => {
  if (!props.report?.radar) return {}
  const { labels, scores } = props.report.radar
  return {
    tooltip: { 
      trigger: 'item',
      backgroundColor: '#ffffff',
      borderColor: '#E4E4E7',
      textStyle: { color: '#09090B', fontSize: 12 },
      padding: [8, 12]
    },
    radar: {
      indicator: labels.map((name: string) => ({ name, max: 10 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#71717A', fontSize: 11, fontWeight: 500 },
      splitLine: { lineStyle: { color: '#E4E4E7' } },
      splitArea: { areaStyle: { color: ['#FAFAFB', '#F4F4F5', '#FAFAFB', '#F4F4F5'] } },
      axisLine: { lineStyle: { color: '#E4E4E7' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: scores,
        name: '能力评分',
        lineStyle: { color: '#18181B', width: 2 },
        areaStyle: { color: 'rgba(24, 24, 27, 0.08)' },
        itemStyle: { color: '#18181B', borderColor: '#ffffff', borderWidth: 2 },
        symbolSize: 6,
      }],
    }],
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div
          class="modal-content bg-white rounded-2xl p-8 w-[720px] max-w-[94vw] max-h-[88vh] overflow-y-auto shadow-[var(--shadow-modal)] border border-[var(--color-border)]"
        >
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-bold text-[var(--color-text-primary)] tracking-tight">终极评估报告</h2>
            <button
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--color-border)] bg-white text-xs font-medium text-[var(--color-text-secondary)] hover:text-zinc-900 hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all"
              @click="$emit('close')"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              关闭
            </button>
          </div>

          <div v-if="loading" class="text-center py-16">
            <div class="w-10 h-10 border-2 border-[var(--color-border-light)] border-t-zinc-900 rounded-full animate-spin mx-auto" />
            <p class="text-sm font-medium text-[var(--color-text-primary)] mt-4">AI 总监正在生成综合评估...</p>
            <p class="text-xs text-[var(--color-text-muted)] mt-1">此过程通常需要 10～15 秒，请耐心等待</p>
          </div>

          <template v-else-if="report">
            <div class="flex flex-wrap gap-2 mb-6">
              <span v-if="report.persona_name" class="px-2.5 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border-light)] text-xs font-medium text-[var(--color-text-secondary)]">对练对象: {{ report.persona_name }}</span>
              <span v-if="report.final_stage" class="px-2.5 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border-light)] text-xs font-medium text-[var(--color-text-secondary)]">最终阶段: {{ report.final_stage }}</span>
              <span v-if="report.turn_count" class="px-2.5 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border-light)] text-xs font-medium text-[var(--color-text-secondary)]">回合数: {{ report.turn_count }}</span>
            </div>

            <div class="grid grid-cols-4 gap-3 mb-6">
              <div
                v-for="item in [
                  { label: '综合总分', value: report.avg_scores?.total },
                  { label: '专业性', value: report.avg_scores?.professionalism },
                  { label: '合规性', value: report.avg_scores?.compliance },
                  { label: '策略性', value: report.avg_scores?.strategy },
                ]"
                :key="item.label"
                class="bg-white rounded-xl p-4 text-center border border-[var(--color-border)] shadow-sm"
              >
                <div class="text-2xl font-bold tabular-nums" :class="scoreColor(item.value ?? 0)">{{ item.value ?? '-' }}</div>
                <div class="text-[11px] font-medium text-[var(--color-text-secondary)] mt-1">{{ item.label }}</div>
              </div>
            </div>

            <div v-if="report.radar && report.radar.labels?.length" class="bg-[var(--color-surface)] rounded-xl p-5 border border-[var(--color-border-light)] mb-6">
              <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-2">能力雷达图</h3>
              <v-chart :option="radarOption" style="height: 300px; width: 100%;" autoresize />
            </div>

            <div v-if="report.review" class="bg-white rounded-xl p-5 border border-[var(--color-border)] mb-6 shadow-sm">
              <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-3">考官总评</h3>
              <div class="text-sm leading-relaxed text-[var(--color-text-secondary)] whitespace-pre-wrap">
                {{ report.review }}
              </div>
            </div>

            <div v-if="report.per_turn_scores?.length">
              <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-3">各轮评分明细</h3>
              <div class="space-y-2">
                <div
                  v-for="t in report.per_turn_scores"
                  :key="t.turn"
                  class="flex items-center gap-3 p-3 rounded-xl bg-white border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors shadow-sm"
                >
                  <span class="px-2 py-0.5 rounded text-[11px] font-bold shrink-0 bg-zinc-100 text-zinc-700 border border-zinc-200">
                    R{{ t.turn }}
                  </span>
                  <div class="flex-1 flex gap-4 text-xs font-medium text-[var(--color-text-secondary)]">
                    <span>专业 <b class="text-[var(--color-text-primary)] font-semibold">{{ t.professionalism }}</b></span>
                    <span>合规 <b class="text-[var(--color-text-primary)] font-semibold">{{ t.compliance }}</b></span>
                    <span>策略 <b class="text-[var(--color-text-primary)] font-semibold">{{ t.strategy }}</b></span>
                  </div>
                  <span class="text-xs text-[var(--color-text-secondary)] max-w-[200px] truncate" :title="t.advice">
                    {{ t.advice || '-' }}
                  </span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active { transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-from .modal-content,
.modal-leave-to .modal-content { transform: scale(0.96) translateY(12px); }
</style>