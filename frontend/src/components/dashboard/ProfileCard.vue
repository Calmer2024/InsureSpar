<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardOverview } from '../../services/api'

defineProps<{
  data: DashboardOverview | null
}>()
</script>

<template>
  <div class="bg-white rounded-[var(--radius-xl)] shadow-[var(--shadow-card)] border border-[var(--color-border)] p-6 flex flex-col gap-5 animate-fade-in h-full">
    <!-- Profile -->
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-100 to-emerald-50 flex items-center justify-center shadow-sm border border-emerald-100">
        <Icon icon="lucide:user" class="w-8 h-8 text-emerald-500" />
      </div>
      <div class="flex-1 min-w-0">
        <h2 class="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{{ data?.user_info.name || '加载中...' }}</h2>
        <div class="flex items-center gap-2 mt-1">
          <span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-[11px] font-bold">{{ data?.user_info.rank || '—' }}</span>
          <span v-if="data?.user_info.join_date" class="text-[11px] text-[var(--color-text-muted)]">
            入职 {{ data.user_info.join_date }}
          </span>
        </div>
      </div>
    </div>

    <!-- Divider -->
    <div class="h-px bg-gray-100"></div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 gap-3">
      <div class="bg-[var(--color-surface)] rounded-xl p-4 text-center transition-all hover:shadow-sm">
        <div class="text-2xl font-extrabold text-emerald-500 tabular-nums leading-none">{{ data?.stats.total_sessions ?? '—' }}</div>
        <div class="text-[11px] text-[var(--color-text-muted)] font-medium mt-2">累计对练</div>
      </div>
      <div class="bg-[var(--color-surface)] rounded-xl p-4 text-center transition-all hover:shadow-sm">
        <div class="text-2xl font-extrabold text-emerald-500 tabular-nums leading-none">{{ data?.stats.deal_closed_count ?? '—' }}</div>
        <div class="text-[11px] text-[var(--color-text-muted)] font-medium mt-2">通关次数</div>
      </div>
      <div class="bg-[var(--color-surface)] rounded-xl p-4 text-center transition-all hover:shadow-sm">
        <div class="text-2xl font-extrabold text-emerald-500 tabular-nums leading-none">{{ data?.stats.avg_score_all_time?.toFixed(1) ?? '—' }}</div>
        <div class="text-[11px] text-[var(--color-text-muted)] font-medium mt-2">历史均分</div>
      </div>
      <div class="bg-[var(--color-surface)] rounded-xl p-4 text-center transition-all hover:shadow-sm">
        <div class="text-2xl font-extrabold text-emerald-500 tabular-nums leading-none">
          {{ data?.stats.total_duration_minutes ? Math.round(data.stats.total_duration_minutes / 60) + 'h' : '—' }}
        </div>
        <div class="text-[11px] text-[var(--color-text-muted)] font-medium mt-2">总时长</div>
      </div>
    </div>
  </div>
</template>
