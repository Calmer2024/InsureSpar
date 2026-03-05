<script setup lang="ts">
import { ref } from 'vue'
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
  <div v-if="isFinished" class="absolute bottom-6 left-8 right-8 bg-white/80 backdrop-blur-xl border border-white/60 shadow-lg rounded-2xl p-5 flex flex-col items-center justify-center z-10 animate-fade-in-up">
    <span class="text-sm text-gray-800 font-bold mb-1">本轮对练已结束</span>
    <span class="text-xs text-gray-500">请在右侧查看考官详细评估报告</span>
  </div>

  <div v-else class="absolute bottom-6 left-8 right-8 flex items-end gap-3 z-10">
    
    <ToolboxPanel
      :visible="showToolbox"
      @close="showToolbox = false"
    />

    <div class="relative shrink-0 group mb-1 animate-fade-in">
      <button
        :disabled="disabled"
        class="w-[46px] h-[46px] rounded-full flex items-center justify-center transition-all duration-300 shadow-[0_8px_20px_rgba(0,0,0,0.15)]"
        :class="showToolbox ? 'bg-gray-100 text-gray-800 rotate-45' : 'bg-[#1A1A1A] text-white hover:scale-105 hover:bg-black'"
        @click="showToolbox = !showToolbox"
      >
        <svg class="w-5 h-5 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
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

      <div class="flex items-center justify-between mt-2 px-1">
        <div class="flex items-center gap-2">
          <span class="text-[11px] text-gray-400 flex items-center gap-1.5 ml-2">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
            支持手动输入或 AI 辅助推进
          </span>
        </div>

        <div class="flex items-center gap-2.5">
          
          <button 
            :disabled="disabled && !autoTimerActive"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-200 border active:scale-95 disabled:opacity-50 disabled:active:scale-100"
            :class="autoTimerActive ? 'bg-[#E6F3EC] text-[#1E7B44] border-[#4ADE80]/30 shadow-inner' : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50 hover:text-gray-700 shadow-sm'"
            @click="$emit('toggle-auto-timer')"
          >
            <span class="relative flex h-2 w-2">
              <span v-if="autoTimerActive" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4ADE80] opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" :class="autoTimerActive ? 'bg-[#4ADE80]' : 'bg-gray-400'"></span>
            </span>
            {{ autoTimerActive ? '自动推演中' : '连续推演' }}
          </button>

          <button
            :disabled="disabled"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-200 border shadow-sm active:scale-95 disabled:opacity-40 disabled:active:scale-100 bg-white text-gray-500 border-gray-200 hover:border-gray-300 hover:text-gray-700 hover:bg-gray-50"
            @click="$emit('step')"
            title="单次 AI 推进"
          >
            <svg class="w-3.5 h-3.5 text-[#4ADE80]" fill="currentColor" viewBox="0 0 20 20">
              <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
            </svg>
            AI 推进
          </button>
          
          <button
            :disabled="disabled || !inputText.trim()"
            class="w-9 h-9 ml-1 rounded-full bg-[#1A1A1A] text-white flex items-center justify-center transition-all disabled:opacity-30 disabled:scale-100 active:scale-95 hover:bg-black shadow-md"
            @click="handleSend($emit)"
          >
            <svg class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>