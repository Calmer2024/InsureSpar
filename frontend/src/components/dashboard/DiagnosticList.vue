<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardCapabilities } from '../../services/api'

defineProps<{
  data: DashboardCapabilities | null
}>()
</script>

<template>
  <div class="flex h-full flex-col px-1 py-2 animate-fade-in">
    <h3 class="text-[15px] font-bold text-[var(--color-text-primary)] mb-1">AI 导师总评</h3>
    <p class="text-[11px] text-[var(--color-text-muted)] mb-4">弱点诊断与专项建议</p>

    <div v-if="data" class="mb-6">
      <div class="flex items-start gap-2.5">
        <span class="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--color-accent-soft)]">
          <Icon icon="lucide:bot" class="h-4 w-4 text-[var(--color-accent)]" />
        </span>
        <p class="pt-1 text-[13px] leading-relaxed text-[var(--color-text-secondary)]">{{ data.ai_general_review }}</p>
      </div>
    </div>

    <div class="flex flex-1 flex-col gap-4">
      <h4 class="text-[13px] font-bold text-[var(--color-text-primary)]">高频失分项 Top {{ data?.weaknesses.length || 0 }}</h4>

      <div
        v-for="(item, i) in (data?.weaknesses || [])"
        :key="i"
        class="group flex items-start gap-3 py-1"
      >
        <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#fff2ef]">
          <span class="text-xs text-[#c76b5d] tabular-nums">{{ i + 1 }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[13px] font-bold text-[var(--color-text-primary)]">{{ item.dimension }}</span>
            <span class="text-[10px] text-[#c76b5d]">
              失分 {{ item.frequency }} 次
            </span>
          </div>
          <p class="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{{ item.advice }}</p>
        </div>
        <button class="soft-action shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100">
          专项突破
        </button>
      </div>

      <div v-if="!data" class="flex-1 flex items-center justify-center text-[var(--color-text-muted)] text-sm py-8">
        加载中...
      </div>
    </div>
  </div>
</template>
