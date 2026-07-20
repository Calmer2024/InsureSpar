<script setup lang="ts">
import { Icon } from '@iconify/vue'
import type { DashboardCapabilities } from '../../services/api'
import mentorReviewIcon from '../../assets/dashboard/ai-mentor-review.png'

defineProps<{
  data: DashboardCapabilities | null
}>()
</script>

<template>
  <div class="relative flex h-full min-h-0 flex-col overflow-hidden p-5 animate-fade-in">
    <img
      :src="mentorReviewIcon"
      alt=""
      aria-hidden="true"
      class="pointer-events-none absolute right-1 top-0 h-[134px] w-[134px] select-none object-contain sm:h-[154px] sm:w-[154px]"
    />

    <div class="relative z-10 flex items-center gap-2 pr-28 sm:pr-32">
      <span class="grid h-8 w-8 place-items-center rounded-xl bg-[var(--color-accent-soft)]">
        <Icon icon="lucide:bot" class="h-4 w-4 text-[var(--color-accent-dark)]" />
      </span>
      <h3 class="text-[17px] font-bold text-[var(--color-text-primary)]">AI 导师总评</h3>
    </div>
    <p class="relative z-10 mb-4 pr-28 text-[11px] text-[var(--color-text-muted)] sm:pr-32">基于近期训练表现生成</p>

    <div v-if="data" class="relative z-10 flex min-h-0 flex-1 items-center">
      <p class="text-[13px] leading-[1.75] text-[var(--color-text-secondary)]">
        {{ data.ai_general_review }}
      </p>
    </div>

    <div v-else class="flex flex-1 items-center justify-center py-8 text-sm text-[var(--color-text-muted)]">
      加载中...
    </div>
  </div>
</template>
