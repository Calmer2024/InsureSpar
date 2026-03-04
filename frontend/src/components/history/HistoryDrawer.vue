<script setup lang="ts">
import { ref, watch } from 'vue'
import type { HistorySession, HistoryDetail } from '../../services/api'
import { fetchHistorySessions, fetchHistoryDetail } from '../../services/api'
import type { ChatMessage, Evaluation, FinalReport } from '../../types'

const props = defineProps<{
  visible: boolean
  currentSessionId?: string | null
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

watch(() => props.visible, (val) => {
  if (val) {
    loadSessions()
  }
}, { immediate: true })

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
        per_turn_scores: fr.per_turn_scores || [],
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

// 时间格式化辅助函数
function timeAgo(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return `${Math.floor(diff / 86400)} 天前`
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex justify-end"
      >
        <div class="absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity" @click="$emit('close')" />

        <div class="relative w-[420px] max-w-[85vw] h-full bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.05)] flex flex-col z-10">
          
          <div class="px-6 py-5 border-b border-[var(--color-border)] flex items-center justify-between shrink-0 bg-white">
            <h2 class="text-base font-semibold text-[var(--color-text-primary)] tracking-tight">历史记录</h2>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:text-zinc-900 hover:bg-[var(--color-surface)] transition-colors"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto bg-[var(--color-surface)]">
            
            <div v-if="loading" class="flex flex-col items-center justify-center py-20 text-center">
              <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-zinc-900 rounded-full animate-spin mb-4" />
              <p class="text-sm font-medium text-[var(--color-text-primary)]">正在加载历史</p>
            </div>

            <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
              <div class="w-16 h-16 rounded-2xl bg-white border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-5">
                <svg class="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <p class="text-sm font-medium text-[var(--color-text-primary)]">暂无历史记录</p>
              <p class="text-xs text-[var(--color-text-secondary)] mt-1">完成的对练将在这里显示</p>
            </div>

            <div v-else class="p-4 space-y-3">
              <div
                v-for="s in sessions"
                :key="s.session_id"
                class="group w-full text-left rounded-xl p-4 transition-all duration-200 cursor-pointer border relative overflow-hidden"
                :class="[
                  detailLoading ? 'opacity-50 pointer-events-none scale-[0.98]' : 'hover:border-[#4ADE80]/30 hover:shadow-sm',
                  s.session_id === currentSessionId ? 'border-[#4ADE80] bg-[#4ADE80]/5 shadow-sm' : 'bg-white border-[var(--color-border)]'
                ]"
                @click="viewSession(s)"
              >
                <!-- 当前会话大头贴标识 -->
                <div v-if="s.session_id === currentSessionId" class="absolute top-0 right-0 bg-[#4ADE80] text-white text-[10px] font-bold px-2 py-0.5 rounded-bl-lg tracking-wider shadow-sm z-10">
                  CURRENT
                </div>
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-md flex items-center justify-center border"
                         :class="s.is_finished ? 'bg-zinc-50 border-zinc-200 text-zinc-700' : 'bg-white border-zinc-200 text-zinc-400'">
                      <svg v-if="s.is_finished" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <span class="text-xs font-medium" :class="s.is_finished ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)]'">
                      {{ s.final_stage || '未结束' }}
                    </span>
                  </div>
                  <span class="text-[10px] font-medium text-[var(--color-text-muted)]">{{ timeAgo(s.start_time) }}</span>
                </div>

                <div class="mb-3">
                  <div class="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
                    {{ s.persona_id }}
                  </div>
                  <div v-if="s.strategy_id" class="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                    使用策略: {{ s.strategy_id }}
                  </div>
                </div>

                <div class="flex items-center justify-between pt-3 border-t border-[var(--color-border-light)]">
                  <span class="text-[11px] font-medium text-[var(--color-text-secondary)] bg-[var(--color-surface)] px-2 py-1 rounded-md">
                    {{ s.turn_count }} 轮交锋
                  </span>
                  <span
                    class="text-[10px] font-bold px-2 py-1 rounded-md border"
                    :class="s.is_finished ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white text-[var(--color-text-secondary)] border-[var(--color-border)]'"
                  >
                    {{ s.is_finished ? '查看报告' : '继续对练' }}
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.drawer-enter-from,
.drawer-leave-to { opacity: 0; }
.drawer-enter-from .relative,
.drawer-leave-to .relative { transform: translateX(100%); }
</style>