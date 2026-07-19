<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardOverview } from '../../services/api'

defineProps<{
  data: DashboardOverview | null
}>()
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-5 p-5 animate-fade-in">
    <!-- Profile -->
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-100 to-emerald-50 flex items-center justify-center shadow-sm border border-emerald-100">
        <img v-if="data?.user_info.avatar_url" :src="data.user_info.avatar_url" :alt="`${data.user_info.name}头像`" class="h-full w-full rounded-2xl object-cover" />
        <img v-else src="/insurespar_logged_out.png" alt="未登录用户头像" class="h-full w-full rounded-2xl object-cover" />
      </div>
      <div class="flex-1 min-w-0">
        <h2 class="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{{ data?.user_info.name || '加载中...' }}</h2>
        <div class="flex items-center gap-2 mt-1">
          <span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-[11px] font-bold">{{ data?.user_info.rank || '暂无' }}</span>
          <span v-if="data?.user_info.join_date" class="text-[11px] text-[var(--color-text-muted)]">
            入职 {{ data.user_info.join_date }}
          </span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-x-6 gap-y-5 pt-4">
      <div>
        <Icon icon="lucide:messages-square" class="mb-2 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[28px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.total_sessions ?? '暂无' }}</div>
        <div class="mt-2 text-[11px] text-[var(--color-text-muted)]">累计对练</div>
      </div>
      <div>
        <Icon icon="lucide:circle-check" class="mb-2 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[28px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.deal_closed_count ?? '暂无' }}</div>
        <div class="mt-2 text-[11px] text-[var(--color-text-muted)]">通关次数</div>
      </div>
      <div>
        <Icon icon="lucide:star" class="mb-2 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[28px] leading-none text-[var(--color-accent)] tabular-nums">{{ data?.stats.avg_score_all_time?.toFixed(1) ?? '暂无' }}</div>
        <div class="mt-2 text-[11px] text-[var(--color-text-muted)]">历史均分</div>
      </div>
      <div>
        <Icon icon="lucide:clock-3" class="mb-2 h-4 w-4 text-[var(--color-accent-dark)]" />
        <div class="metric-primary text-[28px] leading-none text-[var(--color-accent)] tabular-nums">
          {{ data?.stats.total_duration_minutes ? Math.round(data.stats.total_duration_minutes / 60) + 'h' : '暂无' }}
        </div>
        <div class="mt-2 text-[11px] text-[var(--color-text-muted)]">总时长</div>
      </div>
    </div>
  </div>
</template>
