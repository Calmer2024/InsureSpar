<script setup lang="ts">
import type { FinalReport } from '../../types'
import ScoreBar from '../common/ScoreBar.vue'
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
  if (v >= 7) return 'text-score-high'
  if (v >= 4) return 'text-score-mid'
  return 'text-score-low'
}

/** ECharts 雷达图配置 */
const radarOption = computed(() => {
  if (!props.report?.radar) return {}
  const { labels, scores } = props.report.radar
  return {
    tooltip: { trigger: 'item' },
    radar: {
      indicator: labels.map((name: string) => ({ name, max: 10 })),
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#64748B',
        fontSize: 12,
        fontWeight: 600,
      },
      splitLine: { lineStyle: { color: '#E2E8F0' } },
      splitArea: {
        areaStyle: {
          color: ['rgba(16, 185, 129, 0.02)', 'rgba(16, 185, 129, 0.04)', 'rgba(16, 185, 129, 0.06)', 'rgba(16, 185, 129, 0.08)', 'rgba(16, 185, 129, 0.10)'],
        },
      },
      axisLine: { lineStyle: { color: '#E2E8F0' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: scores,
            name: '能力评分',
            lineStyle: { color: '#10B981', width: 2 },
            areaStyle: { color: 'rgba(16, 185, 129, 0.15)' },
            itemStyle: { color: '#10B981', borderColor: '#fff', borderWidth: 2 },
            symbolSize: 6,
          },
        ],
      },
    ],
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div
          class="bg-surface-card rounded-2xl p-8 w-[720px] max-w-[94vw] max-h-[88vh] overflow-y-auto animate-fade-in-up"
          :style="{ boxShadow: 'var(--shadow-modal)' }"
        >
          <!-- 头部 -->
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-bold text-text-primary">📊 终极评估报告</h2>
            <button
              class="px-3 py-1.5 rounded-lg border border-border text-xs text-text-muted hover:text-danger hover:border-danger transition-colors"
              @click="$emit('close')"
            >
              ✕ 关闭
            </button>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="text-center py-16">
            <div class="w-10 h-10 border-3 border-border border-t-primary-500 rounded-full animate-spin mx-auto" />
            <p class="text-sm text-text-secondary mt-4">🧠 AI 总监正在生成综合评估...</p>
            <p class="text-xs text-text-muted mt-2">此过程通常需要 10～15 秒，请耐心等待</p>
          </div>

          <!-- 报告内容 -->
          <template v-else-if="report">
            <!-- Meta 标签 -->
            <div class="flex flex-wrap gap-2 mb-6">
              <span v-if="report.persona_name" class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🎭 {{ report.persona_name }}</span>
              <span v-if="report.final_stage" class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">📍 {{ report.final_stage }}</span>
              <span v-if="report.turn_count" class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🔄 共 {{ report.turn_count }} 轮</span>
              <span v-if="report.strategy_id" class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🎯 {{ report.strategy_id }}</span>
            </div>

            <!-- 综合评分 -->
            <div class="grid grid-cols-4 gap-3 mb-6">
              <div
                v-for="item in [
                  { label: '综合总分', value: report.avg_scores?.total },
                  { label: '专业性', value: report.avg_scores?.professionalism },
                  { label: '合规性', value: report.avg_scores?.compliance },
                  { label: '策略性', value: report.avg_scores?.strategy },
                ]"
                :key="item.label"
                class="bg-surface rounded-xl p-4 text-center border border-border"
              >
                <div class="text-2xl font-bold" :class="scoreColor(item.value ?? 0)">{{ item.value ?? '-' }}</div>
                <div class="text-[11px] text-text-muted mt-1">{{ item.label }}</div>
              </div>
            </div>

            <!-- 雷达图 (ECharts) -->
            <div v-if="report.radar && report.radar.labels?.length" class="bg-surface rounded-xl p-5 border border-border mb-6">
              <h3 class="text-sm font-semibold text-text-primary mb-2">🎯 六维能力雷达图</h3>
              <v-chart :option="radarOption" style="height: 320px; width: 100%;" autoresize />
            </div>

            <!-- 总监点评 -->
            <div v-if="report.review" class="bg-surface rounded-xl p-5 border border-border mb-6">
              <h3 class="text-sm font-semibold text-primary-600 mb-3">📝 总监综合点评</h3>
              <div class="text-sm leading-loose text-text-primary whitespace-pre-wrap">
                {{ report.review }}
              </div>
            </div>

            <!-- 逐轮评分明细 -->
            <div v-if="report.per_turn_scores?.length">
              <h3 class="text-sm font-semibold text-text-primary mb-3">📋 各轮评分明细</h3>
              <div class="space-y-2">
                <div
                  v-for="t in report.per_turn_scores"
                  :key="t.turn"
                  class="flex items-center gap-3 p-3 rounded-xl bg-surface border border-border"
                >
                  <span class="px-2.5 py-0.5 rounded-full bg-primary-100 text-primary-700 text-[11px] font-bold shrink-0">
                    第 {{ t.turn }} 轮
                  </span>
                  <div class="flex-1 flex gap-4 text-xs text-text-secondary">
                    <span>专业 <b class="text-text-primary ml-0.5">{{ t.professionalism }}</b></span>
                    <span>合规 <b class="text-text-primary ml-0.5">{{ t.compliance }}</b></span>
                    <span>策略 <b class="text-text-primary ml-0.5">{{ t.strategy }}</b></span>
                  </div>
                  <span class="text-xs text-amber-600 max-w-[180px] truncate" :title="t.advice">
                    💡 {{ t.advice || '-' }}
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
.modal-leave-active {
  transition: all 0.3s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
