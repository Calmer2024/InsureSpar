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
        class="w-[46px] h-[46px] rounded-full flex items-center justify-center text-xl transition-all duration-300 shadow-[0_8px_20px_rgba(0,0,0,0.15)]"
        :class="showToolbox ? 'bg-gray-100 text-gray-800 rotate-45' : 'bg-[#1A1A1A] text-white hover:scale-105 hover:bg-black'"
        @click="showToolbox = !showToolbox"
      >
        +
      </button>
      <div class="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-[#1A1A1A] text-white text-[10px] font-medium rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
        {{ showToolbox ? '关闭工具箱' : '打开工具箱' }}
      </div>
    </div>

    <div class="flex-1 bg-white/80 backdrop-blur-2xl border border-white shadow-[0_12px_40px_rgba(0,0,0,0.06)] rounded-[24px] p-2.5 flex flex-col transition-all focus-within:bg-white focus-within:shadow-[0_12px_50px_rgba(0,0,0,0.08)] animate-fade-in-up">
      
      <input
        v-model="inputText"
        type="text"
        :placeholder="placeholder || 'Ask or search anything...'"
        :disabled="disabled"
        class="w-full bg-transparent px-4 py-3 text-[14px] text-gray-800 placeholder-gray-400 outline-none disabled:opacity-50"
        @keypress.enter="handleSend($emit)"
        @focus="showToolbox = false"
      />

      <div class="flex items-center justify-between mt-2 px-1">
        <div class="flex items-center gap-2">
          <button 
            :disabled="disabled && !autoTimerActive"
            class="bg-[#F5F5F5] text-gray-600 rounded-full px-3.5 py-1.5 text-[12px] font-medium flex items-center gap-1.5 transition-colors"
            :class="autoTimerActive ? 'bg-[#EAF5F0] text-[#1E7B44]' : 'hover:bg-gray-200'"
            @click="$emit('toggle-auto-timer')"
          >
            <span class="w-2.5 h-2.5 rounded-full transition-colors" :class="autoTimerActive ? 'bg-[#4ADE80] animate-pulse' : 'bg-gray-400'" />
            连续推演
          </button>
          <span class="text-[12px] text-gray-400 px-1 select-none">|</span>
          <span class="text-[11px] text-gray-400 flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
            支持手动输入
          </span>
        </div>

        <div class="flex items-center gap-3">
          <button
            :disabled="disabled"
            class="text-gray-500 hover:text-gray-900 text-[12px] font-bold flex items-center gap-1.5 transition-colors disabled:opacity-40"
            @click="$emit('step')"
          >
            ✨ AI 推进
          </button>
          
          <button
            :disabled="disabled || !inputText.trim()"
            class="w-9 h-9 rounded-full bg-[#1A1A1A] text-white flex items-center justify-center transition-all disabled:opacity-30 disabled:scale-100 hover:scale-105 hover:bg-black shadow-md"
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