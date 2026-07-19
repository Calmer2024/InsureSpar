<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import ToolboxPanel from '../tools/ToolboxPanel.vue'

defineProps<{
  disabled?: boolean
  placeholder?: string
  isFinished?: boolean
  autoTimerActive?: boolean
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
}>()

const inputText = ref('')
const showToolbox = ref(false)

function handleSend(emit: (e: 'send', msg: string) => void) {
  const msg = inputText.value.trim()
  if (!msg) return
  emit('send', msg)
  inputText.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

const textareaRef = ref<HTMLTextAreaElement | null>(null)

function autoResize(e: Event) {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = target.scrollHeight + 'px'
}

function handleKeydown(e: KeyboardEvent, emit: (e: 'send', msg: string) => void) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend(emit)
  }
}
</script>

<template>
  <div v-if="isFinished" class="relative z-10 m-3 mt-0 flex shrink-0 flex-col items-center justify-center rounded-xl border border-gray-100 bg-white/90 p-4 shadow-lg backdrop-blur-xl animate-fade-in-up sm:m-5 sm:mt-0">
    <span class="text-sm text-gray-800 font-bold mb-1">本轮对练已结束</span>
    <span class="text-xs text-gray-500">请在右侧查看考官详细评估报告</span>
  </div>

  <div v-else class="relative z-10 flex shrink-0 items-end gap-2 bg-white/90 p-3 backdrop-blur-xl sm:gap-3 sm:p-5">
    
    <ToolboxPanel
      :visible="showToolbox"
      @close="showToolbox = false"
    />

    <div class="flex-1 bg-white/80 backdrop-blur-2xl border border-white shadow-[0_12px_40px_rgba(0,0,0,0.06)] rounded-[24px] p-2.5 flex flex-col transition-all focus-within:bg-white focus-within:shadow-[0_12px_50px_rgba(0,0,0,0.08)] animate-fade-in-up">
      
      <textarea
        ref="textareaRef"
        v-model="inputText"
        :placeholder="placeholder || '输入你的销售话术... (Shift+Enter 换行)'"
        :disabled="disabled"
        rows="1"
        class="w-full bg-transparent px-4 py-3 text-[14px] text-gray-800 placeholder-gray-400 outline-none disabled:opacity-50 resize-none overflow-y-auto min-h-[44px] max-h-[150px]"
        @input="autoResize"
        @keydown="handleKeydown($event, $emit)"
      ></textarea>

      <div class="flex flex-wrap items-center justify-between gap-2 mt-2 px-1">
        <div class="flex items-center">
          <button
            :disabled="disabled"
            class="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-surface)] text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-accent-soft)] hover:text-[var(--color-accent-dark)] disabled:opacity-40"
            :class="showToolbox ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent-dark)]' : ''"
            @click="showToolbox = !showToolbox"
            :aria-label="showToolbox ? '关闭工具箱' : '打开工具箱'"
            :title="showToolbox ? '关闭工具箱' : '打开工具箱'"
          >
            <Icon :icon="showToolbox ? 'lucide:x' : 'lucide:tool-case'" class="h-[18px] w-[18px]" />
          </button>
        </div>

        <div class="ml-auto flex min-w-0 items-center gap-1.5 sm:gap-2.5">
          
          <button 
            :disabled="disabled && !autoTimerActive"
            class="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-200 border active:scale-95 disabled:opacity-50 disabled:active:scale-100 whitespace-nowrap"
            :class="autoTimerActive ? 'bg-[#E6F3EC] text-[#1E7B44] border-[#4ADE80]/30 shadow-inner' : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50 hover:text-gray-700 shadow-sm'"
            @click="$emit('toggle-auto-timer')"
            :title="autoTimerActive ? '停止连续推演' : '开始连续推演'"
          >
            <Icon :icon="autoTimerActive ? 'lucide:pause' : 'lucide:repeat-2'" class="h-3.5 w-3.5" />
            {{ autoTimerActive ? '自动推演中' : '连续推演' }}
          </button>

          <button
            :disabled="disabled"
            class="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-200 border shadow-sm active:scale-95 disabled:opacity-40 disabled:active:scale-100 bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-700 hover:bg-gray-50 whitespace-nowrap"
            @click="$emit('step')"
            title="单次 AI 推进"
          >
            <Icon icon="lucide:sparkles" class="w-3.5 h-3.5 text-[#1E7B44]" />
            AI 推进
          </button>
          
          <button
            :disabled="disabled"
            class="ml-1 grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[#111111] text-white transition-colors hover:bg-[#262626] disabled:cursor-not-allowed disabled:bg-[#111111] disabled:text-white"
            @click="handleSend($emit)"
            title="发送消息"
            aria-label="发送消息"
          >
            <Icon icon="lucide:arrow-right" class="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
