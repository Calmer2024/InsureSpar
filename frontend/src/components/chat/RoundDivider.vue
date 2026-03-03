<script setup lang="ts">
defineProps<{
  turn: number
}>()
</script>

<template>
  <div class="flex items-center gap-3 py-3 px-4">
    <div class="flex-1 h-px bg-border" />
    <span class="text-[11px] font-semibold text-text-muted tracking-wider uppercase flex items-center gap-1.5">
      <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-100 text-primary-600 text-[10px] font-bold">
        {{ turn }}
      </span>
      第 {{ turn }} 轮
    </span>
    <div class="flex-1 h-px bg-border" />
  </div>
</template>
