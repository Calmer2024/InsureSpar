<script setup lang="ts">
import type { ChatMessage, Persona } from '../../types'
import { computed, ref } from 'vue'

const props = defineProps<{
  message: ChatMessage
  activePersona?: Persona | null
}>()



const truncLen = 80
const isTruncated = computed(() => props.message.content.length > truncLen && props.message.role === 'system')
const expanded = ref(false)
const displayContent = computed(() => {
  if (props.message.role !== 'system') return props.message.content
  if (expanded.value || props.message.content.length <= truncLen) return props.message.content
  return props.message.content.substring(0, truncLen) + '...'
})
</script>

<template>
  <div v-if="message.role === 'system'" class="flex justify-center animate-fade-in my-4">
    <div
      class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[11px] font-medium leading-snug bg-white border border-gray-100 shadow-sm text-gray-500 cursor-default"
      :class="{
        'bg-[#FFF4B5]/50 text-[#8C7A14] border-[#FFF4B5]': message.logType === 'stage_update',
        'bg-red-50 text-red-600 border-red-100': message.logType === 'force_guard',
      }"
      @click="isTruncated && (expanded = !expanded)"
    >
      <span class="truncate transition-all duration-200" :class="{'whitespace-normal': expanded}">{{ displayContent }}</span>
    </div>
  </div>

  <div v-else-if="message.role === 'sales'" class="flex flex-row-reverse gap-4 w-full mb-6 group animate-fade-in-up">
    <div class="shrink-0 mt-1">
      <div class="w-9 h-9 rounded-full overflow-hidden shadow-sm border border-white">
        <img src="/logo.png" alt="InsureSpar" class="w-full h-full object-cover" />
      </div>
    </div>

    <div class="flex-1 min-w-0 max-w-[85%] flex flex-col items-end">
      <div class="text-[12px] font-medium text-gray-400 mb-1.5 mr-1">保险代理人</div>
      <div class="rounded-[20px] rounded-tr-sm p-5 text-[14px] leading-[1.7] shadow-sm transition-all duration-300 bg-[#F0F7F4] text-gray-800 text-left">
        <span v-if="message.content">{{ message.content }}</span>
        
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1.5 py-1 align-middle">
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>

        <div v-if="message.content && !message.isStreaming" class="flex items-center justify-between mt-4 pt-3 border-t border-[#E1EFE7]/60">
          <div class="flex items-center gap-3 text-gray-400">
            <button class="hover:text-[#4ADE80] transition-colors"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.514" /></svg></button>
            <button class="hover:text-red-400 transition-colors"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.514" /></svg></button>
          </div>
          <div class="flex items-center gap-4 text-gray-400 text-[12px] font-medium">
            <button class="flex items-center gap-1.5 hover:text-gray-700 transition-colors">
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg> Copy
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="message.role === 'customer'" class="flex gap-4 w-full mb-6 group animate-fade-in-up">
    <div class="shrink-0 mt-1">
      <div class="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center shadow-sm border border-white text-lg overflow-hidden">
        <img v-if="activePersona?.persona_id" :src="`http://127.0.0.1:8000/assets/avatars/${activePersona.persona_id}.png`" alt="Customer" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
        <div :style="{ display: activePersona?.persona_id ? 'none' : 'flex' }" class="w-full h-full items-center justify-center">🧑🏻</div>
      </div>
    </div>

    <div class="flex-1 min-w-0 max-w-[85%] flex flex-col items-start">
      <div class="text-[12px] font-medium text-gray-400 mb-1.5 ml-1">{{ activePersona?.name || '客户' }}</div>
      <div class="rounded-[20px] rounded-tl-sm p-5 text-[14px] leading-[1.7] bg-gray-50 text-gray-800 transition-all duration-300">
        {{ message.content }}
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1.5 py-1 align-middle">
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
    </div>
  </div>
</template>