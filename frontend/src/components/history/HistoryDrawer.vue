<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { HistorySession, HistoryDetail } from '../../services/api'
import { fetchHistorySessions, fetchHistoryDetail } from '../../services/api'
import type { ChatMessage, Evaluation, FinalReport } from '../../types'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'view-session', data: {
    messages: ChatMessage[]
    evaluations: Evaluation[]
    finalReport: FinalReport | null
    info: HistorySession
  }): void
}>()

const sessions = ref<HistorySession[]>([])
const loading = ref(false)
const detailLoading = ref(false)

onMounted(loadSessions)

async function loadSessions() {
  loading.value = true
  try {
    sessions.value = await fetchHistorySessions()
  } catch (e) {
    console.error('加载历史失败', e)
  } finally {
    loading.value = false
  }
}

async function viewSession(s: HistorySession) {
  detailLoading.value = true
  try {
    const detail = await fetchHistoryDetail(s.session_id)

    // 转换 conversation_logs → ChatMessage[]
    const messages: ChatMessage[] = detail.conversation_logs
      .filter(log => log.role === 'sales' || log.role === 'customer')
      .map((log, i) => ({
        id: `hist-${log.id}-${i}`,
        role: log.role as 'sales' | 'customer',
        content: log.content,
        turn: log.turn,
      }))

    // 转换 evaluations → Evaluation[]
    const evaluations: Evaluation[] = detail.evaluations.map(ev => ({
      turn: ev.turn,
      professionalism_score: ev.scores.professionalism,
      compliance_score: ev.scores.compliance,
      strategy_score: ev.scores.strategy,
      professionalism_comment: ev.comments.professionalism,
      compliance_comment: ev.comments.compliance,
      strategy_comment: ev.comments.strategy,
      overall_advice: ev.overall_advice,
    }))

    // 转换 final_report
    let finalReport: FinalReport | null = null
    if (detail.final_report) {
      const fr = detail.final_report
      let radarData = null
      if (fr.radar_data) {
        try {
          radarData = typeof fr.radar_data === 'string' ? JSON.parse(fr.radar_data) : fr.radar_data
        } catch { /* ignore */ }
      }
      finalReport = {
        avg_scores: fr.avg_scores,
        review: fr.review_content || '',
        radar: radarData || { labels: [], scores: [] },
        persona_name: s.persona_id,
        strategy_id: s.strategy_id || undefined,
        final_stage: s.final_stage || undefined,
        turn_count: s.turn_count,
      }
    }

    emit('view-session', {
      messages,
      evaluations,
      finalReport,
      info: detail.session_info,
    })
  } catch (e) {
    console.error('加载详情失败', e)
  } finally {
    detailLoading.value = false
  }
}

function stageIcon(stage: string | null): string {
  if (!stage) return '💬'
  if (stage.includes('SIGN')) return '✅'
  if (stage.includes('REJECT')) return '❌'
  if (stage.includes('PENDING')) return '📋'
  if (stage.includes('FOLLOW')) return '📞'
  if (stage.includes('OBJECTION')) return '⚡'
  return '💬'
}

function timeAgo(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex"
        @click.self="$emit('close')"
      >
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/20" @click="$emit('close')" />

        <!-- 抽屉 -->
        <div class="relative ml-auto w-[400px] max-w-[85vw] h-full bg-surface-card shadow-2xl flex flex-col animate-slide-in-right">
          <!-- 头部 -->
          <div class="px-5 py-4 border-b border-border flex items-center justify-between shrink-0">
            <h2 class="text-sm font-bold text-text-primary">📚 历史记录</h2>
            <button
              class="px-2 py-1 rounded-md text-xs text-text-muted hover:text-danger hover:bg-red-50 transition"
              @click="$emit('close')"
            >✕</button>
          </div>

          <!-- 列表 -->
          <div class="flex-1 overflow-y-auto">
            <!-- 加载 -->
            <div v-if="loading" class="flex items-center justify-center py-12">
              <div class="w-6 h-6 border-2 border-border border-t-primary-500 rounded-full animate-spin" />
            </div>

            <!-- 空状态 -->
            <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
              <span class="text-3xl mb-3">📭</span>
              <p class="text-xs text-text-muted">暂无历史记录</p>
            </div>

            <!-- 会话列表 -->
            <div v-else class="divide-y divide-border">
              <button
                v-for="s in sessions"
                :key="s.session_id"
                class="w-full text-left px-5 py-3.5 hover:bg-surface-hover transition-colors"
                :class="{ 'opacity-50 pointer-events-none': detailLoading }"
                @click="viewSession(s)"
              >
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm">{{ stageIcon(s.final_stage) }}</span>
                  <span class="text-xs font-semibold text-text-primary">{{ s.persona_id }}</span>
                  <span v-if="s.strategy_id" class="text-[10px] px-1.5 py-0.5 rounded bg-primary-50 text-primary-600">{{ s.strategy_id }}</span>
                  <span class="ml-auto text-[10px] text-text-muted">{{ timeAgo(s.start_time) }}</span>
                </div>
                <div class="flex items-center gap-3 text-[11px] text-text-secondary">
                  <span>{{ s.turn_count }} 轮</span>
                  <span v-if="s.final_stage" class="truncate">{{ s.final_stage }}</span>
                  <span
                    class="ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium"
                    :class="s.is_finished ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
                  >
                    {{ s.is_finished ? '已结束' : '进行中' }}
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active { transition: all 0.25s ease; }
.drawer-enter-from,
.drawer-leave-to { opacity: 0; }
.drawer-enter-from .relative,
.drawer-leave-to .relative { transform: translateX(100%); }
</style>
