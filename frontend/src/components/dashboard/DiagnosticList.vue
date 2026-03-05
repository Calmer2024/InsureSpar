<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardCapabilities } from '../../services/api'

defineProps<{
  data: DashboardCapabilities | null
}>()
</script>

<template>
  <div class="bg-white rounded-[var(--radius-xl)] shadow-[var(--shadow-card)] border border-[var(--color-border)] p-6 flex flex-col animate-fade-in">
    <h3 class="text-[15px] font-bold text-[var(--color-text-primary)] mb-1">AI 导师总评</h3>
    <p class="text-[11px] text-[var(--color-text-muted)] mb-4">弱点诊断与专项建议</p>

    <!-- AI General Review -->
    <div v-if="data" class="bg-emerald-50/60 rounded-xl p-4 mb-5 border border-emerald-100/60">
      <div class="flex items-start gap-2.5">
        <Icon icon="lucide:bot" class="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
        <p class="text-[13px] text-gray-700 leading-relaxed">{{ data.ai_general_review }}</p>
      </div>
    </div>

    <!-- Weakness list -->
    <div class="flex-1 flex flex-col gap-3">
      <h4 class="text-[12px] font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">高频失分项 Top {{ data?.weaknesses.length || 0 }}</h4>

      <div
        v-for="(item, i) in (data?.weaknesses || [])"
        :key="i"
        class="flex items-start gap-3 p-3.5 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-light)] transition-all hover:shadow-sm group"
      >
        <div class="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
          <span class="text-red-400 text-sm font-bold tabular-nums">{{ i + 1 }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[13px] font-bold text-[var(--color-text-primary)]">{{ item.dimension }}</span>
            <span class="px-1.5 py-0.5 rounded-md bg-red-50 text-red-400 text-[10px] font-bold">
              失分 {{ item.frequency }} 次
            </span>
          </div>
          <p class="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{{ item.advice }}</p>
        </div>
        <button class="shrink-0 px-3 py-1.5 rounded-lg bg-white border border-[var(--color-border)] text-[11px] font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-zinc-300 transition-all opacity-0 group-hover:opacity-100">
          专项突破
        </button>
      </div>

      <div v-if="!data" class="flex-1 flex items-center justify-center text-[var(--color-text-muted)] text-sm py-8">
        加载中...
      </div>
    </div>
  </div>
</template>
