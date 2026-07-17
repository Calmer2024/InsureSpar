<script setup lang="ts">
import { computed, ref } from 'vue'
import { Icon } from '@iconify/vue'
import type { ChatMessage, Persona } from '../../types'
import MarkdownText from '../common/MarkdownText.vue'
import RichText from '../common/RichText.vue'
import { personaAvatar } from '../../utils/avatar'

const props = defineProps<{
  message: ChatMessage
  activePersona?: Persona | null
}>()

const feedback = ref<'helpful' | 'improve' | null>(null)
const copied = ref(false)

const systemMeta = computed(() => {
  switch (props.message.logType) {
    case 'tool_call':
      return {
        icon: 'lucide:database-search',
        label: '训练策略',
        summary: '正在为本轮对话准备相关信息',
        foldLabel: '查看内部策略',
      }
    case 'tool_result':
      return {
        icon: 'lucide:circle-check',
        label: '训练策略',
        summary: '本轮参考信息已准备完成',
        foldLabel: '查看调试信息',
      }
    case 'force_guard':
      return {
        icon: 'lucide:badge-alert',
        label: '训练提示',
        summary: props.message.content.includes('失败') || props.message.content.includes('错误')
          ? '本轮处理遇到问题，请稍后重试'
          : '先回应客户的真实顾虑，再自然推进下一步',
        foldLabel: '查看内部策略',
      }
    case 'stage_update':
      return {
        icon: 'lucide:route',
        label: '对话进展',
        summary: props.message.content,
        foldLabel: '',
      }
    default:
      return {
        icon: 'lucide:info',
        label: '系统动态',
        summary: props.message.content,
        foldLabel: '',
      }
  }
})

const hasInternalDetail = computed(() => Boolean(
  systemMeta.value.foldLabel && props.message.content !== systemMeta.value.summary,
))

function setFeedback(value: 'helpful' | 'improve') {
  feedback.value = feedback.value === value ? null : value
}

async function copyMessage() {
  try {
    await navigator.clipboard.writeText(props.message.content)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = props.message.content
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    textarea.remove()
  }
  copied.value = true
  window.setTimeout(() => { copied.value = false }, 1600)
}
</script>

<template>
  <div v-if="message.role === 'system'" class="system-event animate-fade-in">
    <div class="system-event__marker" aria-hidden="true">
      <Icon :icon="systemMeta.icon" class="h-3.5 w-3.5" />
    </div>
    <div class="min-w-0 flex-1 py-0.5">
      <div class="flex items-baseline gap-2 text-[12px] leading-5">
        <span class="shrink-0 font-medium text-zinc-500">{{ systemMeta.label }}</span>
        <RichText :text="systemMeta.summary" class="text-zinc-600" />
      </div>
      <details v-if="hasInternalDetail" class="group/details mt-1 text-[11px] text-zinc-400">
        <summary class="inline-flex cursor-pointer list-none items-center gap-1 rounded px-1 py-0.5 hover:bg-zinc-100 hover:text-zinc-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/30">
          <Icon icon="lucide:chevron-right" class="h-3 w-3 transition-transform group-open/details:rotate-90" />
          {{ systemMeta.foldLabel }}
        </summary>
        <div class="mt-1 border-l border-zinc-200 pl-3 font-mono leading-5 text-zinc-500 break-words">
          <span v-if="message.toolName">工具：{{ message.toolName }}<br /></span>
          {{ message.content }}
        </div>
      </details>
    </div>
  </div>

  <div v-else-if="message.role === 'sales'" class="group flex w-full flex-row-reverse gap-4 mb-6 animate-fade-in-up">
    <div class="shrink-0 mt-1">
      <div class="w-9 h-9 rounded-full overflow-hidden shadow-sm border border-white">
        <img src="/insurespar_logo.png" alt="InsureSpar" class="w-full h-full object-cover" />
      </div>
    </div>

    <div class="flex min-w-0 max-w-[85%] flex-1 flex-col items-end">
      <div class="mb-1.5 mr-1 text-[12px] font-medium text-gray-400">保险代理人</div>
      <div class="rounded-[20px] rounded-tr-sm p-5 text-[14px] leading-[1.7] shadow-sm bg-[#F0F7F4] text-gray-800 text-left">
        <MarkdownText v-if="message.content" :text="message.content" />
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1.5 py-1 align-middle" aria-label="正在输入">
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-2 h-2 rounded-full bg-[#4ADE80]/80" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
      <div v-if="message.content && !message.isStreaming" class="message-actions" role="toolbar" aria-label="消息操作">
        <button type="button" :class="{ 'is-active': feedback === 'helpful' }" title="这条回复有帮助" aria-label="这条回复有帮助" @click="setFeedback('helpful')">
          <Icon icon="lucide:thumbs-up" />
        </button>
        <button type="button" :class="{ 'is-active is-negative': feedback === 'improve' }" title="这条回复需要改进" aria-label="这条回复需要改进" @click="setFeedback('improve')">
          <Icon icon="lucide:thumbs-down" />
        </button>
        <button type="button" :title="copied ? '已复制' : '复制消息'" :aria-label="copied ? '已复制' : '复制消息'" @click="copyMessage">
          <Icon :icon="copied ? 'lucide:check' : 'lucide:copy'" />
        </button>
      </div>
    </div>
  </div>

  <div v-else-if="message.role === 'customer'" class="group flex w-full gap-4 mb-6 animate-fade-in-up">
    <div class="shrink-0 mt-1">
      <div class="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center shadow-sm border border-white overflow-hidden">
        <img v-if="personaAvatar(activePersona)" :src="personaAvatar(activePersona)" alt="客户头像" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
        <div :style="{ display: personaAvatar(activePersona) ? 'none' : 'flex' }" class="w-full h-full items-center justify-center text-gray-400">
          <Icon icon="lucide:user-round" class="h-4 w-4" />
        </div>
      </div>
    </div>

    <div class="flex min-w-0 max-w-[85%] flex-1 flex-col items-start">
      <div class="mb-1.5 ml-1 text-[12px] font-medium text-gray-400">{{ activePersona?.name || '客户' }}</div>
      <div class="rounded-[20px] rounded-tl-sm p-5 text-[14px] leading-[1.7] bg-gray-50 text-gray-800">
        <MarkdownText v-if="message.content" :text="message.content" />
        <span v-if="message.isStreaming && !message.content" class="inline-flex gap-1.5 py-1 align-middle" aria-label="正在输入">
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite" />
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite 0.2s" />
          <span class="w-2 h-2 rounded-full bg-gray-400" style="animation: typing-bounce 1.4s infinite 0.4s" />
        </span>
      </div>
      <div v-if="message.content && !message.isStreaming" class="message-actions" role="toolbar" aria-label="消息操作">
        <button type="button" :class="{ 'is-active': feedback === 'helpful' }" title="这条回复有帮助" aria-label="这条回复有帮助" @click="setFeedback('helpful')">
          <Icon icon="lucide:thumbs-up" />
        </button>
        <button type="button" :class="{ 'is-active is-negative': feedback === 'improve' }" title="这条回复需要改进" aria-label="这条回复需要改进" @click="setFeedback('improve')">
          <Icon icon="lucide:thumbs-down" />
        </button>
        <button type="button" :title="copied ? '已复制' : '复制消息'" :aria-label="copied ? '已复制' : '复制消息'" @click="copyMessage">
          <Icon :icon="copied ? 'lucide:check' : 'lucide:copy'" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.system-event {
  position: relative;
  display: flex;
  width: min(100%, 720px);
  gap: 0.625rem;
  margin: 0.25rem auto 0.875rem;
  padding-left: 0.125rem;
}

.system-event::before {
  content: '';
  position: absolute;
  top: 1.35rem;
  bottom: -0.9rem;
  left: 0.7rem;
  width: 1px;
  background: #e4e4e7;
}

.system-event__marker {
  position: relative;
  z-index: 1;
  display: grid;
  width: 1.5rem;
  height: 1.5rem;
  flex: 0 0 1.5rem;
  place-items: center;
  border: 1px solid #e4e4e7;
  border-radius: 50%;
  background: #fff;
  color: #71717a;
}

.message-actions {
  display: flex;
  min-height: 1.75rem;
  align-items: center;
  gap: 0.125rem;
  padding-top: 0.25rem;
  color: #a1a1aa;
  opacity: 0;
  transform: translateY(-2px);
  transition: opacity 150ms ease, transform 150ms ease;
  pointer-events: none;
}

.group:hover .message-actions,
.group:focus-within .message-actions {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.message-actions button {
  display: grid;
  width: 1.75rem;
  height: 1.75rem;
  place-items: center;
  border-radius: 0.375rem;
  transition: color 150ms ease, background 150ms ease;
}

.message-actions button:hover,
.message-actions button:focus-visible,
.message-actions button.is-active {
  background: #f4f4f5;
  color: #047857;
  outline: none;
}

.message-actions button.is-negative {
  color: #dc2626;
}

.message-actions :deep(svg) {
  width: 0.95rem;
  height: 0.95rem;
}

@media (hover: none) {
  .message-actions {
    opacity: 1;
    transform: none;
    pointer-events: auto;
  }
}
</style>
