<script setup lang="ts">
defineProps<{
  turn: number
}>()
</script>

<template>
  <div class="flex items-center gap-4 py-8 px-4 opacity-60">
    <div class="flex-1 h-px bg-gray-200" />
    <div class="flex items-center justify-center px-4 py-1.5 rounded-full bg-gray-50">
      <span class="text-[10px] font-bold text-gray-400 tracking-widest uppercase">
        Round {{ turn }}
      </span>
    </div>
    <div class="flex-1 h-px bg-gray-200" />
  </div>
</template>