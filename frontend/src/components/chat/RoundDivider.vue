<script setup lang="ts">
defineProps<{
  turn: number
}>()
</script>

<template>
  <div class="flex justify-center px-4 py-6 opacity-60">
    <div class="flex items-center justify-center rounded-full bg-gray-50 px-4 py-1.5">
      <span class="text-[10px] font-bold text-gray-400 tracking-widest uppercase">
        Round {{ turn }}
      </span>
    </div>
  </div>
</template>
