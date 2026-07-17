<script setup lang="ts">
import type {ChatMessage, Persona} from '../../types'
import {computed, nextTick, ref, watch} from 'vue'
import { Icon } from '@iconify/vue'
import { personaAvatar } from '../../utils/avatar'
import ChatBubble from './ChatBubble.vue'
import RoundDivider from './RoundDivider.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  messages: ChatMessage[]
  title: string
  subtitle: string
  disabled?: boolean
  isFinished?: boolean
  isHistoryView?: boolean
  autoTimerActive?: boolean
  activePersona?: Persona | null
}>()

defineEmits<{
  (e: 'send', message: string): void
  (e: 'step'): void
  (e: 'toggle-auto-timer'): void
  (e: 'resume-session'): void
}>()

const chatContainer = ref<HTMLElement>()

// 解析客户名和策略（基于现有的 "画像 × 策略" 格式）
const customerName = computed(() => props.title.split(' × ')[0] || '客户')
const strategyName = computed(() => props.title.split(' × ')[1] || '常规对话')

const groupedMessages = computed(() => {
  const groups: { turn: number; messages: ChatMessage[] }[] = []
  let currentTurn = -1
  for (const msg of props.messages) {
    if (msg.turn !== currentTurn) {
      currentTurn = msg.turn
      groups.push({turn: currentTurn, messages: []})
    }
    const lastGroup = groups[groups.length - 1]
    if (lastGroup) lastGroup.messages.push(msg)
  }
  return groups
})

watch(
    () => props.messages.length,
    async () => {
      await nextTick()
      if (chatContainer.value) {
        chatContainer.value.scrollTo({
          top: chatContainer.value.scrollHeight,
          behavior: 'smooth',
        })
      }
    }
)
</script>

<template>
  <div class="relative flex flex-col h-full min-w-0 bg-white overflow-hidden">

    <div class="relative z-20 shrink-0 border-b border-gray-100 bg-white/90 px-4 py-3 backdrop-blur-xl sm:px-6 sm:py-4 xl:px-8">

      <div class="relative group cursor-pointer">
        <div class="flex items-center gap-3">
          <div
              class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-xl shadow-sm border border-white overflow-hidden">
            <img v-if="personaAvatar(activePersona)" :src="personaAvatar(activePersona)"
                 :alt="customerName" class="w-full h-full object-cover"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"/>
            <div :style="{ display: personaAvatar(activePersona) ? 'none' : 'flex' }"
                 class="w-full h-full items-center justify-center text-gray-400">
              <Icon icon="lucide:user-round" class="h-4 w-4" />
            </div>
          </div>
          <div>
            <h2 class="text-[17px] font-extrabold text-gray-900 tracking-tight leading-none">{{ customerName }}</h2>
            <p class="text-[12px] text-gray-500 font-medium mt-1 line-clamp-1 max-w-[280px]">{{ subtitle }}</p>
          </div>
        </div>

        <div
            class="absolute left-0 top-full mt-3 w-[min(24rem,calc(100vw-3rem))] bg-white rounded-xl shadow-[0_20px_40px_rgba(0,0,0,0.08)] border border-gray-100 p-5 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 translate-y-2 group-hover:translate-y-0 z-50">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-2xl overflow-hidden">
              <img v-if="personaAvatar(activePersona)" :src="personaAvatar(activePersona)"
                   :alt="customerName" class="w-full h-full object-cover"
                   onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"/>
              <div :style="{ display: personaAvatar(activePersona) ? 'none' : 'flex' }"
                   class="w-full h-full items-center justify-center text-gray-400">
                <Icon icon="lucide:user-round" class="h-5 w-5" />
              </div>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 text-base">{{ customerName }}</h3>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-[10px] px-2 py-0.5 rounded-md bg-gray-100 text-gray-600 font-medium">模拟客户</span>
                <span v-if="activePersona?.difficulty"
                      class="text-[10px] px-2 py-0.5 rounded-md text-amber-600 bg-amber-50 font-medium uppercase border border-amber-100/50">
                  {{ activePersona.difficulty }}
                </span>
              </div>
            </div>
          </div>

          <div class="space-y-3 mt-1 text-sm">
            <div>
              <p class="text-[11px] font-medium text-gray-400 mb-0.5">基础设定</p>
              <p class="text-xs text-gray-700 leading-relaxed">{{ activePersona?.demographics || subtitle }}</p>
            </div>

            <!--            <div v-if="activePersona?.health_status" class="pt-2 border-t border-gray-50">-->
            <!--              <p class="text-[11px] font-medium text-gray-400 mb-0.5">健康状况</p>-->
            <!--              <p class="text-xs text-gray-700 leading-relaxed">{{ activePersona.health_status }}</p>-->
            <!--            </div>-->

            <div v-if="activePersona?.financial_status" class="pt-2 border-t border-gray-50">
              <p class="text-[11px] font-medium text-gray-400 mb-0.5">财务状况</p>
              <p class="text-xs text-gray-700 leading-relaxed">{{ activePersona.financial_status }}</p>
            </div>

            <div v-if="activePersona?.risk_preference">
              <p class="text-[11px] font-medium text-gray-400 mb-0.5">风险偏好</p>
              <p class="text-xs text-gray-700">{{ activePersona.risk_preference }}</p>
            </div>
            <div v-if="activePersona?.insurance_awareness">
              <p class="text-[11px] font-medium text-gray-400 mb-0.5">保险认知</p>
              <p class="text-xs text-gray-700 line-clamp-2">{{ activePersona.insurance_awareness }}</p>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-50 flex items-center justify-between">
            <span class="text-[11px] font-medium text-gray-400 uppercase">当前应用策略</span>
            <span class="text-[11px] font-bold text-[#4ADE80] bg-[#E6F3EC] px-2 py-1 rounded-md max-w-[150px] truncate">{{
                strategyName
              }}</span>
          </div>
        </div>
      </div>

    </div>

    <div ref="chatContainer" class="flex-1 min-h-0 overflow-y-auto px-4 py-6 sm:px-6 xl:px-8">

      <div v-if="messages.length === 0"
           class="h-full flex flex-col items-center justify-center text-center animate-fade-in pb-10">
        <div
            class="w-20 h-20 rounded-[2rem] bg-gray-50 shadow-sm border border-gray-100 flex items-center justify-center mb-6">
          <Icon icon="lucide:messages-square" class="w-10 h-10 text-gray-300" />
        </div>
        <h3 class="text-[16px] font-bold text-gray-800">对练已就绪</h3>
        <p class="text-xs text-gray-400 mt-2 max-w-[240px] leading-relaxed">系统已加载《{{ strategyName }}》策略<br>请输入话术或点击底部按钮推进。
        </p>
      </div>

      <template v-for="group in groupedMessages" :key="group.turn">
        <RoundDivider v-if="group.turn > 0" :turn="group.turn"/>
        <div class="space-y-1">
          <ChatBubble
              v-for="msg in group.messages"
              :key="msg.id"
              :message="msg"
              :active-persona="activePersona"
          />
        </div>
      </template>
    </div>

    <ChatInput
        :disabled="disabled || isFinished || isHistoryView"
        :is-finished="isFinished"
        :auto-timer-active="autoTimerActive"
        @send="$emit('send', $event)"
        @step="$emit('step')"
        @toggle-auto-timer="$emit('toggle-auto-timer')"
    />
  </div>
</template>
