<script setup lang="ts">
defineProps<{
  status: 'idle' | 'ready' | 'processing' | 'error' | 'finished'
}>()
</script>

<template>
  <span
    class="inline-block w-2 h-2 rounded-full"
    :class="{
      'bg-text-muted': status === 'idle',
      'bg-primary-500 animate-pulse-dot': status === 'ready',
      'bg-warning animate-pulse-dot': status === 'processing',
      'bg-danger': status === 'error',
      'bg-primary-600': status === 'finished',
    }"
  />
</template>
