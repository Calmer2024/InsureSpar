<script setup lang="ts">
defineProps<{
  score: number
  maxScore?: number
  label: string
  showValue?: boolean
}>()

// 进度条保留语义色，但使用更柔和现代的色彩
function scoreClass(score: number): string {
  if (score >= 7) return 'bg-[var(--color-score-high)]' // 健康绿
  if (score >= 4) return 'bg-[var(--color-score-mid)]'  // 警示黄
  return 'bg-[var(--color-score-low)]'                  // 危险红
}
</script>

<template>
  <div class="flex items-center gap-4">
    <span class="text-xs font-medium text-[var(--color-text-secondary)] w-14 shrink-0 truncate">
      {{ label }}
    </span>
    
    <div class="flex-1 h-2 bg-[var(--color-surface-muted)] rounded-full overflow-hidden shadow-inner border border-black/5">
      <div
        class="h-full rounded-full transition-all duration-1000 ease-out"
        :class="scoreClass(score)"
        :style="{ width: `${(score / (maxScore ?? 10)) * 100}%` }"
      />
    </div>
    
    <span
      v-if="showValue !== false"
      class="text-xs font-semibold w-10 text-right tabular-nums tracking-tight text-[var(--color-text-primary)]"
    >
      {{ score }}<span class="text-[var(--color-text-muted)] font-normal">/{{ maxScore ?? 10 }}</span>
    </span>
  </div>
</template>