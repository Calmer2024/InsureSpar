<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Icon } from '@iconify/vue'
import type { DashboardOverview, HistorySession } from '../../services/api'
import { fetchDashboardOverview, fetchHistorySessions } from '../../services/api'

defineEmits<{
  (e: 'start-practice'): void
  (e: 'navigate-dashboard'): void
  (e: 'show-history'): void
}>()

const overview = ref<DashboardOverview | null>(null)
const recentSessions = ref<HistorySession[]>([])
const loading = ref(true)
const loadError = ref(false)

onMounted(async () => {
  try {
    const [summary, sessions] = await Promise.all([
      fetchDashboardOverview(),
      fetchHistorySessions(0, 4).catch(() => []),
    ])
    overview.value = summary
    recentSessions.value = sessions
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
})

function formatDate(value: string | null) {
  if (!value) return '时间未记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function stageText(stage: string | null) {
  const labels: Record<string, string> = {
    INTRODUCTION: '破冰沟通',
    OBJECTION: '异议处理',
    DECISION_SIGN: '意向确认',
    DECISION_PENDING: '持续跟进',
    DECISION_FOLLOW_UP: '跟进完成',
    DECISION_REJECT: '客户拒绝',
  }
  return stage ? labels[stage] || stage : '训练进行中'
}

function personaText(personaId: string) {
  const labels: Record<string, string> = {
    hard_boss: '高压决策者',
    young_mother: '年轻家庭客户',
    tech_savvy: '理性科技从业者',
    eager_youth: '积极型年轻客户',
    rebate_seeker: '价格敏感客户',
    hidden_risk_client: '隐性风险客户',
  }
  return labels[personaId] || personaId.split('_').join(' ')
}
</script>

<template>
  <div class="flex min-h-full w-full flex-col gap-3 lg:h-full lg:min-h-0">
    <section class="home-panel-top flex shrink-0 flex-col bg-white px-4 pb-6 pt-6 sm:px-6 sm:pb-7 sm:pt-7 lg:basis-[calc(70%_-_6px)] xl:px-8 xl:pb-7 xl:pt-[30px]">
      <header class="flex h-14 items-center justify-between gap-4">
        <h1 class="truncate text-[25px] font-bold leading-[1.35] text-[var(--color-text-primary)] sm:text-[28px]">
          欢迎回来，{{ overview?.user_info.name || '销售顾问' }}
        </h1>
        <div class="flex shrink-0 items-center gap-3">
          <button
            type="button"
            aria-label="通知"
            title="通知"
            class="grid h-9 w-9 place-items-center rounded-full bg-[#f7f9f8] text-[var(--color-text-secondary)] transition-colors hover:bg-[#eef4f0] hover:text-[var(--color-text-primary)]"
          >
            <Icon icon="lucide:bell" class="h-[17px] w-[17px]" />
          </button>
          <button
            type="button"
            class="flex items-center gap-2 rounded-full px-1.5 py-1 transition-colors hover:bg-[#f7faf8]"
            @click="$emit('navigate-dashboard')"
          >
            <span class="grid h-9 w-9 place-items-center overflow-hidden rounded-full border-2 border-white bg-[#dff5e8] shadow-[0_1px_5px_rgba(47,111,75,0.12)]">
              <img
                :src="overview?.user_info.avatar_url || '/insurespar_logged_out.png'"
                :alt="overview?.user_info.avatar_url ? `${overview.user_info.name}头像` : '未登录用户头像'"
                class="h-full w-full object-cover"
              />
            </span>
            <span class="hidden text-sm text-[var(--color-text-primary)] sm:inline">
              {{ overview?.user_info.name || '销售顾问' }}
            </span>
          </button>
        </div>
      </header>

      <div v-if="loading" class="mt-6 grid flex-1 gap-3 lg:min-h-[320px] lg:grid-cols-[0.84fr_1.5fr]" aria-label="正在加载工作台">
        <div class="min-h-[320px] animate-pulse rounded-xl bg-[#f6f8f7]" />
        <div class="grid grid-cols-2 grid-rows-2 gap-3">
          <div v-for="index in 4" :key="index" class="min-h-[154px] animate-pulse rounded-xl bg-[#f6f8f7]" />
        </div>
      </div>

      <div v-else-if="loadError" class="mt-6 flex min-h-[320px] flex-1 flex-col items-center justify-center rounded-xl border border-[var(--color-border)] bg-white px-6 text-center">
        <Icon icon="lucide:cloud-off" class="h-8 w-8 text-[var(--color-text-muted)]" />
        <p class="ui-title mt-3 text-sm">暂时无法加载工作台数据</p>
        <button type="button" class="soft-action mt-4" @click="$emit('start-practice')">开始对练</button>
      </div>

      <div v-else class="mt-6 grid flex-1 gap-3 lg:min-h-[320px] lg:grid-cols-[0.84fr_1.5fr]">
        <article class="reference-card flex min-h-[320px] flex-col p-6">
          <div class="flex items-center justify-between">
            <h2 class="text-[17px] font-semibold leading-[1.4]">训练概览</h2>
            <span class="text-[11px] text-[var(--color-text-muted)]">最近 30 天</span>
          </div>

          <div class="mt-2 grid min-h-[96px] min-w-0 grid-cols-[0.75fr_1.25fr] items-center gap-3">
            <div class="min-w-0">
              <div class="flex items-end gap-1.5">
                <strong class="metric-primary text-[34px] leading-none tabular-nums">{{ overview?.stats.total_sessions ?? 0 }}</strong>
                <span class="pb-0.5 text-xs text-[var(--color-text-muted)]">次</span>
              </div>
              <p class="mt-2 text-[11px] text-[var(--color-text-muted)]">累计完成训练</p>
            </div>

            <svg class="h-[82px] min-w-0 w-full" viewBox="0 0 260 86" role="img" aria-label="近期开启训练次数呈上升趋势">
              <defs>
                <linearGradient id="trainingArea" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stop-color="#66c08c" stop-opacity="0.36" />
                  <stop offset="100%" stop-color="#66c08c" stop-opacity="0.02" />
                </linearGradient>
              </defs>
              <path d="M4 66 C36 64,58 64,84 65 S128 62,148 52 S192 42,256 24 L256 82 L4 82 Z" fill="url(#trainingArea)" />
              <path d="M4 66 C36 64,58 64,84 65 S128 62,148 52 S192 42,256 24" fill="none" stroke="#55b77d" stroke-linecap="round" stroke-width="2.5" />
            </svg>
          </div>

          <div class="mt-3 grid min-w-0 grid-cols-3 gap-3 border-t border-[#edf1ef] pt-4">
            <div class="min-w-0">
              <p class="text-[11px] text-[var(--color-text-muted)]">历史均分</p>
              <p class="metric-secondary mt-1 text-[18px] leading-[1.35] tabular-nums">{{ overview?.stats.avg_score_all_time?.toFixed(1) ?? '0.0' }}</p>
            </div>
            <div class="min-w-0">
              <p class="text-[11px] text-[var(--color-text-muted)]">通关次数</p>
              <p class="metric-secondary mt-1 text-[18px] leading-[1.35] tabular-nums">{{ overview?.stats.deal_closed_count ?? 0 }}</p>
            </div>
            <div class="min-w-0">
              <p class="text-[11px] text-[var(--color-text-muted)]">训练时长</p>
              <p class="metric-secondary mt-1 text-[18px] leading-[1.35] tabular-nums">{{ Math.round((overview?.stats.total_duration_minutes ?? 0) / 60) }}h</p>
            </div>
          </div>

          <div class="relative mt-auto h-[165px] shrink-0 pt-3">
            <img
              src="/icons/home-overview.png"
              alt="AI 保险销售训练概览"
              class="absolute bottom-0 left-0 h-[165px] w-[220px] object-contain object-left-bottom"
            />
            <button type="button" class="home-card-action absolute bottom-0 right-0" @click="$emit('navigate-dashboard')">查看数据</button>
          </div>
        </article>

        <div class="grid gap-3 sm:grid-cols-2 sm:grid-rows-2">
          <button type="button" class="reference-card reference-card-mint group flex min-h-[154px] flex-col p-5 text-left" @click="$emit('start-practice')">
            <div class="flex items-center gap-3.5">
              <img src="/icons/practice.png" alt="" aria-hidden="true" class="h-[58px] w-[58px] shrink-0 object-contain" />
              <span class="feature-card-title text-[21px] leading-[1.3]">实战对练</span>
            </div>
            <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">选择客户画像，模拟真实销售沟通</p>
            <span class="home-card-action mt-auto self-end">开始训练</span>
          </button>

          <button type="button" class="reference-card reference-card-yellow group flex min-h-[154px] flex-col p-5 text-left" @click="$emit('navigate-dashboard')">
            <div class="flex items-center gap-3.5">
              <img src="/icons/capability.png" alt="" aria-hidden="true" class="h-[58px] w-[58px] shrink-0 object-contain" />
              <span class="feature-card-title text-[21px] leading-[1.3]">能力中心</span>
            </div>
            <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">查看能力画像、成长趋势与训练建议</p>
            <span class="home-card-action mt-auto self-end">查看能力</span>
          </button>

          <button type="button" class="reference-card reference-card-blue group flex min-h-[154px] flex-col p-5 text-left" @click="$emit('show-history')">
            <div class="flex items-center gap-3.5">
              <img src="/icons/history.png" alt="" aria-hidden="true" class="h-[58px] w-[58px] shrink-0 object-contain" />
              <span class="feature-card-title text-[21px] leading-[1.3]">历史复盘</span>
            </div>
            <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">回看完整对话与每轮评估反馈</p>
            <span class="home-card-action mt-auto self-end">查看记录</span>
          </button>

          <button type="button" class="reference-card reference-card-pink group flex min-h-[154px] flex-col p-5 text-left" @click="$emit('start-practice')">
            <div class="flex items-center gap-3.5">
              <img src="/icons/specialized.png" alt="" aria-hidden="true" class="h-[58px] w-[58px] shrink-0 object-contain" />
              <span class="feature-card-title text-[21px] leading-[1.3]">专项训练</span>
            </div>
            <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">强化破冰、异议处理与促单能力</p>
            <span class="home-card-action mt-auto self-end">开始训练</span>
          </button>
        </div>
      </div>
    </section>

    <section class="home-panel-bottom flex min-h-[160px] flex-1 flex-col overflow-hidden border-t border-[#e7efe9] bg-white">
      <div class="flex h-[52px] shrink-0 items-center justify-between px-4 sm:px-6 xl:px-8">
        <h2 class="text-[16px] font-semibold">最近训练</h2>
        <button type="button" class="soft-action flex items-center gap-1.5" @click="$emit('show-history')">
          查看全部
          <Icon icon="lucide:chevron-right" class="h-3.5 w-3.5" />
        </button>
      </div>

      <div v-if="recentSessions.length" class="overflow-x-auto">
        <table class="w-full min-w-[680px] text-left text-sm">
          <thead class="bg-[#fafcfb] text-[11px] font-medium text-[var(--color-text-muted)]">
            <tr>
              <th class="px-8 py-3 font-medium">训练场景</th>
              <th class="px-4 py-3 font-medium">当前阶段</th>
              <th class="px-4 py-3 font-medium">轮次</th>
              <th class="px-4 py-3 font-medium">训练时间</th>
              <th class="px-8 py-3 text-right font-medium">状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="session in recentSessions" :key="session.session_id" class="border-t border-[#f0f3f1] text-[var(--color-text-secondary)]">
              <td class="px-8 py-3.5 font-medium text-[var(--color-text-primary)]">{{ personaText(session.persona_id) }}</td>
              <td class="px-4 py-3.5">{{ stageText(session.final_stage) }}</td>
              <td class="px-4 py-3.5 tabular-nums">{{ session.turn_count }} 轮</td>
              <td class="px-4 py-3.5">{{ formatDate(session.start_time) }}</td>
              <td class="px-8 py-3.5 text-right">
                <span class="inline-flex rounded-full px-2.5 py-1 text-[11px]" :class="session.is_finished ? 'bg-[#e9f7ef] text-[#39845b]' : 'bg-[#f2f4f3] text-[#6d7771]'">
                  {{ session.is_finished ? '已完成' : '进行中' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="flex flex-1 flex-col items-center justify-center px-6 py-8 text-center">
        <Icon icon="lucide:inbox" class="h-7 w-7 text-[var(--color-text-muted)]" />
        <p class="mt-2 text-sm font-medium">还没有训练记录</p>
      </div>
    </section>
  </div>
</template>
