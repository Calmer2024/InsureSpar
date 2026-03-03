<script setup lang="ts">
defineProps<{
  score: number
  maxScore?: number
  label: string
  showValue?: boolean
}>()

function scoreClass(score: number): string {
  if (score >= 7) return 'bg-score-high'
  if (score >= 4) return 'bg-score-mid'
  return 'bg-score-low'
}

function scoreTextClass(score: number): string {
  if (score >= 7) return 'text-score-high'
  if (score >= 4) return 'text-score-mid'
  return 'text-score-low'
}
</script>

<template>
  <div class="flex items-center gap-3">
    <span class="text-xs text-text-secondary w-12 shrink-0">{{ label }}</span>
    <div class="flex-1 h-1.5 bg-surface-muted rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="scoreClass(score)"
        :style="{ width: `${(score / (maxScore ?? 10)) * 100}%` }"
      />
    </div>
    <span
      v-if="showValue !== false"
      class="text-xs font-semibold w-10 text-right"
      :class="scoreTextClass(score)"
    >
      {{ score }}/{{ maxScore ?? 10 }}
    </span>
  </div>
</template>
