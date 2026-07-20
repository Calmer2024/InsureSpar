<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardOverview } from '../../services/api'

defineProps<{
  data: DashboardOverview | null
}>()
</script>

<template>
  <div class="flex h-full min-h-0 flex-col items-start px-5 py-3 animate-fade-in">
    <div class="flex items-center gap-4 text-left">
      <div class="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-emerald-100 to-emerald-50 shadow-sm sm:h-24 sm:w-24">
        <img v-if="data?.user_info.avatar_url" :src="data.user_info.avatar_url" :alt="`${data.user_info.name}头像`" class="h-full w-full rounded-full object-cover" />
        <img v-else src="/insurespar_logged_out.png" alt="未登录用户头像" class="h-full w-full rounded-full object-cover" />
      </div>
      <div class="min-w-0">
        <h2 class="text-[22px] font-bold leading-tight tracking-tight text-[var(--color-text-primary)]">{{ data?.user_info.name || '加载中...' }}</h2>
        <div class="mt-1 flex flex-wrap items-center gap-2">
          <span class="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] text-emerald-600">{{ data?.user_info.rank || '暂无' }}</span>
          <span v-if="data?.user_info.join_date" class="text-[11px] text-[var(--color-text-muted)]">
            入职 {{ data.user_info.join_date }}
          </span>
        </div>
      </div>
    </div>

    <div class="mt-3 grid w-full max-w-4xl grid-cols-2 items-center gap-y-3 rounded-[24px] bg-[#f7faf8] px-5 py-4 sm:flex sm:min-h-[108px] sm:justify-between sm:px-6">
      <div class="text-left sm:w-16 sm:shrink-0">
        <Icon icon="lucide:messages-square" class="mb-1 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[26px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.total_sessions ?? '暂无' }}</div>
        <div class="mt-1 text-[11px] text-[var(--color-text-muted)]">累计对练</div>
      </div>
      <div class="text-center sm:w-16 sm:shrink-0">
        <Icon icon="lucide:circle-check" class="mx-auto mb-1 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[26px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.deal_closed_count ?? '暂无' }}</div>
        <div class="mt-1 text-[11px] text-[var(--color-text-muted)]">通关次数</div>
      </div>
      <div class="text-center sm:w-16 sm:shrink-0">
        <Icon icon="lucide:star" class="mx-auto mb-1 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[26px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.avg_score_all_time?.toFixed(1) ?? '暂无' }}</div>
        <div class="mt-1 text-[11px] text-[var(--color-text-muted)]">历史均分</div>
      </div>
      <div class="text-right sm:w-16 sm:shrink-0">
        <Icon icon="lucide:clock-3" class="mb-1 ml-auto h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[26px] leading-none text-[var(--color-accent)] tabular-nums">
          {{ data?.stats.total_duration_minutes ? Math.round(data.stats.total_duration_minutes / 60) + 'h' : '暂无' }}
        </div>
        <div class="mt-1 text-[11px] text-[var(--color-text-muted)]">总时长</div>
      </div>
    </div>
  </div>
</template>
