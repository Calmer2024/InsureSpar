<script setup lang="ts">
defineProps<{
  status: 'idle' | 'ready' | 'processing' | 'error' | 'finished'
}>()
</script>

<template>
  <span class="relative flex h-2.5 w-2.5 shrink-0 items-center justify-center">
    <span
      v-if="status === 'ready' || status === 'processing'"
      class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
      :class="{
        'bg-emerald-400': status === 'ready',
        'bg-amber-400': status === 'processing'
      }"
    />
    
    <span
      class="relative inline-flex rounded-full h-2 w-2"
      :class="{
        'bg-zinc-300': status === 'idle',            // 灰色：闲置
        'bg-emerald-500': status === 'ready',        // 绿色：就绪 (等待用户输入)
        'bg-amber-500': status === 'processing',     // 橙色：处理中 (AI 思考中)
        'bg-rose-500': status === 'error',           // 红色：错误
        'bg-zinc-800': status === 'finished',        // 极深灰：结束 (对应新的 SaaS 黑白灰风格)
      }"
    />
  </span>
</template>