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

  <div v-else class="relative z-10 flex shrink-0 items-end gap-2 border-t border-gray-100 bg-white/90 p-3 backdrop-blur-xl sm:gap-3 sm:p-5">
    
    <ToolboxPanel
      :visible="showToolbox"
      @close="showToolbox = false"
    />

    <div class="relative shrink-0 group mb-1 animate-fade-in">
      <button
        :disabled="disabled"
        class="w-[46px] h-[46px] rounded-full flex items-center justify-center transition-all duration-300 shadow-[0_8px_20px_rgba(0,0,0,0.15)]"
        :class="showToolbox ? 'bg-gray-100 text-gray-800' : 'bg-[#1A1A1A] text-white hover:scale-105 hover:bg-black'"
        @click="showToolbox = !showToolbox"
        :aria-label="showToolbox ? '关闭工具箱' : '打开工具箱'"
        :title="showToolbox ? '关闭工具箱' : '打开工具箱'"
      >
        <Icon :icon="showToolbox ? 'lucide:x' : 'lucide:tool-case'" class="w-5 h-5" />
      </button>
      <div class="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-[#1A1A1A] text-white text-[10px] font-medium rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
        {{ showToolbox ? '关闭工具箱' : '打开工具箱' }}
      </div>
    </div>

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
        <div class="hidden items-center gap-2 md:flex">
          <span class="text-[11px] text-gray-400 flex items-center gap-1.5 ml-2">
            <Icon icon="lucide:briefcase-business" class="w-3.5 h-3.5" />
            支持手动输入或 AI 辅助推进
          </span>
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
            :disabled="disabled || !inputText.trim()"
            class="w-9 h-9 ml-1 rounded-full bg-[#1A1A1A] text-white flex items-center justify-center transition-all disabled:opacity-30 disabled:scale-100 active:scale-95 hover:bg-black shadow-md"
            @click="handleSend($emit)"
            title="发送消息"
            aria-label="发送消息"
          >
            <Icon icon="lucide:send" class="w-4 h-4 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
