<script setup lang="ts">
import { ref, watch } from 'vue'
import { Icon } from '@iconify/vue'
import type { HistorySession } from '../../services/api'
import { fetchHistorySessions, fetchHistoryDetail } from '../../services/api'
import type { ChatMessage, Evaluation, FinalReport, Persona, Strategy } from '../../types'
import { personaAvatar } from '../../utils/avatar'

const props = defineProps<{
  visible: boolean
  currentSessionId?: string | null
  personas: Persona[]
  strategies: Strategy[]
}>()

const STAGE_LABELS: Record<string, string> = {
  'INTRODUCTION': '破冰介绍',
  'OBJECTION': '异议处理',
  'DECISION_SIGN': '签单成功',
  'DECISION_PENDING': '同意核保',
  'DECISION_FOLLOW_UP': '需要跟进',
  'DECISION_REJECT': '客户拒绝',
  'DECISION_ABANDON': '放弃投保'
}

function getPersona(id: string) {
  return props.personas.find(p => p.persona_id === id)
}

function getStrategy(id: string | null) {
  if (!id) return null
  return props.strategies.find(s => s.strategy_id === id)
}

function getStageLabel(stage: string | null) {
  if (!stage) return '未结束'
  return STAGE_LABELS[stage] || stage
}

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
        class="fixed inset-0 z-50 flex justify-end pointer-events-none"
      >
        <div class="absolute inset-0 bg-transparent transition-opacity pointer-events-auto" @click="$emit('close')" />

        <div class="relative w-[420px] max-w-[85vw] h-full bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.05)] flex flex-col z-10 pointer-events-auto">
          
          <div class="px-6 py-5 border-b border-[var(--color-border)] flex items-center justify-between shrink-0 bg-white">
            <h2 class="text-base font-semibold text-[var(--color-text-primary)] tracking-tight">历史记录</h2>
            <button
              aria-label="关闭历史记录"
              title="关闭历史记录"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:text-zinc-900 hover:bg-[var(--color-surface)] transition-colors"
              @click="$emit('close')"
            >
              <Icon icon="lucide:x" class="w-5 h-5" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto bg-[var(--color-surface)]">
            
            <div v-if="loading" class="flex flex-col items-center justify-center py-20 text-center">
              <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-zinc-900 rounded-full animate-spin mb-4" />
              <p class="text-sm font-medium text-[var(--color-text-primary)]">正在加载历史</p>
            </div>

            <div v-else-if="sessions.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
              <div class="w-16 h-16 rounded-2xl bg-white border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-5">
                <Icon icon="lucide:history" class="w-8 h-8 text-[var(--color-text-muted)]" />
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
                <div v-if="s.session_id === currentSessionId" class="absolute top-0 right-0 bg-[#4ADE80] text-white text-[10px] font-bold px-2 py-0.5 rounded-bl-lg tracking-wider shadow-sm z-10">
                  CURRENT
                </div>
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded-md flex items-center justify-center border"
                         :class="s.is_finished ? 'bg-zinc-50 border-zinc-200 text-zinc-700' : 'bg-white border-zinc-200 text-zinc-400'">
                      <Icon :icon="s.is_finished ? 'lucide:check' : 'lucide:clock-3'" class="w-3.5 h-3.5" />
                    </div>
                    <span class="text-xs font-medium" :class="s.is_finished ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)]'">
                      {{ getStageLabel(s.final_stage) }}
                    </span>
                  </div>
                  <span class="text-[10px] font-medium text-[var(--color-text-muted)]">{{ timeAgo(s.start_time) }}</span>
                </div>

                <div class="mb-3">
                  <div class="flex items-center gap-2 mb-1">
                    <img v-if="getPersona(s.persona_id)" :src="personaAvatar(getPersona(s.persona_id))" :alt="`${getPersona(s.persona_id)?.name}头像`" class="h-8 w-8 shrink-0 rounded-lg object-cover" />
                    <div class="text-sm font-semibold text-[var(--color-text-primary)]">
                       {{ getPersona(s.persona_id)?.name || s.persona_id }}
                    </div>
                    <span v-for="tag in (getPersona(s.persona_id)?.tags || [])" :key="tag" class="text-[10px] px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-600 font-medium">
                      {{ tag }}
                    </span>
                  </div>
                  <div v-if="s.strategy_id" class="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                    使用策略: {{ getStrategy(s.strategy_id)?.name || s.strategy_id }}
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
/* 外层容器控制整体的挂载淡入/淡出 */
.drawer-enter-active,
.drawer-leave-active { 
  transition: opacity 0.3s cubic-bezier(0.16, 1, 0.3, 1); 
}

/* 内部抽屉面板控制平滑位移 */
.drawer-enter-active .relative,
.drawer-leave-active .relative {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 初始和离开状态：外层透明，内层在右侧屏幕外 */
.drawer-enter-from,
.drawer-leave-to { 
  opacity: 0; 
}
.drawer-enter-from .relative,
.drawer-leave-to .relative { 
  transform: translateX(100%); 
}
</style>
