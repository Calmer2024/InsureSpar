<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue' // 1. 引入 Iconify 的 Vue 组件
import { parseEmojiText, type Segment } from '../../utils/emojiIcons'

const props = defineProps<{
  text: string
}>()

const segments = computed<Segment[]>(() => parseEmojiText(props.text))
</script>

<template>
  <span class="inline-flex items-center gap-0.5 align-middle">
    <template v-for="(seg, i) in segments" :key="i">
      <span v-if="seg.type === 'text'">{{ seg.value }}</span>
      
      <Icon
        v-else
        :icon="seg.iconName"
        class="inline-block w-3.5 h-3.5 shrink-0"
      />
    </template>
  </span>
</template>