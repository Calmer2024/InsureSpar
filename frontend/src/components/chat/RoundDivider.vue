<script setup lang="ts">
defineProps<{
  turn: number
}>()
</script>

<template>
  <div class="flex items-center gap-4 py-6 px-2 opacity-80">
    <div class="flex-1 h-px bg-[var(--color-border-light)]" />
    <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)]">
      <span class="inline-flex items-center justify-center w-4 h-4 rounded-full bg-zinc-200 text-zinc-700 text-[9px] font-bold">
        {{ turn }}
      </span>
      <span class="text-[11px] font-medium text-[var(--color-text-secondary)] tracking-wide">
        第 {{ turn }} 轮
      </span>
    </div>
    <div class="flex-1 h-px bg-[var(--color-border-light)]" />
  </div>
</template>