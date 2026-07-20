<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardCapabilities } from '../../services/api'

defineProps<{
  data: DashboardCapabilities | null
}>()
</script>

<template>
  <div class="flex h-full min-h-0 flex-col overflow-visible p-5 animate-fade-in">
    <div class="flex items-center gap-2">
      <span class="grid h-8 w-8 place-items-center rounded-xl bg-[var(--color-accent-soft)]"><Icon icon="lucide:triangle-alert" class="h-4 w-4 text-[var(--color-accent-dark)]" /></span>
      <h3 class="text-[17px] font-bold text-[var(--color-text-primary)]">高频失分项</h3>
    </div>
    <p class="mb-4 text-[11px] text-[var(--color-text-muted)]">弱点诊断与专项建议</p>

    <div class="flex min-h-0 flex-1 flex-col justify-center gap-4 pb-2">
      <h4 class="text-[13px] font-bold text-[var(--color-text-primary)]">Top {{ data?.weaknesses.length || 0 }}</h4>

      <div
        v-for="(item, i) in (data?.weaknesses || [])"
        :key="i"
        class="group flex items-start gap-3 py-1"
      >
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#fff2ef]">
          <span class="text-xs text-[#c76b5d] tabular-nums">{{ i + 1 }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="mb-1 flex flex-wrap items-center gap-x-1.5 gap-y-1">
            <span class="text-[13px] font-bold text-[var(--color-text-primary)]">{{ item.dimension }}</span>
            <span class="text-[10px] text-[#c76b5d]">
              失分 {{ item.frequency }} 次
            </span>
            <button class="soft-action ml-0.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100">
              专项突破
            </button>
          </div>
          <p class="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{{ item.advice }}</p>
        </div>
      </div>

      <div v-if="!data" class="flex-1 flex items-center justify-center text-[var(--color-text-muted)] text-sm py-8">
        加载中...
      </div>
    </div>
  </div>
</template>
