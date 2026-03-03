<script setup lang="ts">
import type { FinalReport } from '../../types'
import ScoreBar from '../common/ScoreBar.vue'

defineProps<{
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
          </div>

          <!-- 报告内容 -->
          <template v-else-if="report">
            <!-- Meta 标签 -->
            <div class="flex flex-wrap gap-2 mb-6">
              <span class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🎭 {{ report.persona_name }}</span>
              <span class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">📍 {{ report.final_stage }}</span>
              <span class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🔄 共 {{ report.turn_count }} 轮</span>
              <span v-if="report.strategy_id" class="px-3 py-1 rounded-lg bg-surface-muted border border-border-light text-xs text-text-secondary">🎯 {{ report.strategy_id }}</span>
            </div>

            <!-- 综合评分 -->
            <div class="grid grid-cols-4 gap-3 mb-6">
              <div
                v-for="item in [
                  { label: '综合总分', value: report.avg_scores.total },
                  { label: '专业性', value: report.avg_scores.professionalism },
                  { label: '合规性', value: report.avg_scores.compliance },
                  { label: '策略性', value: report.avg_scores.strategy },
                ]"
                :key="item.label"
                class="bg-surface rounded-xl p-4 text-center border border-border"
              >
                <div class="text-2xl font-bold" :class="scoreColor(item.value)">{{ item.value ?? '-' }}</div>
                <div class="text-[11px] text-text-muted mt-1">{{ item.label }}</div>
              </div>
            </div>

            <!-- 雷达图占位 -->
            <div class="bg-surface rounded-xl p-5 border border-border mb-6">
              <h3 class="text-sm font-semibold text-text-primary mb-4">🎯 六维能力雷达图</h3>
              <div class="flex items-center justify-center h-52 text-text-muted text-xs">
                <!-- 静态 UI 阶段的雷达图占位 -->
                <div class="text-center">
                  <div class="grid grid-cols-3 gap-x-6 gap-y-3 text-xs">
                    <div v-for="(label, i) in report.radar.labels" :key="label" class="text-center">
                      <div class="text-lg font-bold" :class="scoreColor(report.radar.scores[i])">
                        {{ report.radar.scores[i] }}
                      </div>
                      <div class="text-text-muted mt-0.5">{{ label }}</div>
                    </div>
                  </div>
                  <p class="text-[10px] text-text-muted mt-4">📈 雷达图将在集成 Chart.js 后展示</p>
                </div>
              </div>
            </div>

            <!-- 总监点评 -->
            <div class="bg-surface rounded-xl p-5 border border-border mb-6">
              <h3 class="text-sm font-semibold text-primary-600 mb-3">📝 总监综合点评</h3>
              <div class="text-sm leading-loose text-text-primary whitespace-pre-wrap">
                {{ report.review }}
              </div>
            </div>

            <!-- 逐轮评分明细 -->
            <div>
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
                    💡 {{ t.advice }}
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
