<script setup lang="ts">
import type { AppStatus } from '../../types'
import StatusDot from '../common/StatusDot.vue'
import RichText from '../common/RichText.vue'
import { Icon } from '@iconify/vue'

defineProps<{
  status: AppStatus
  statusText: string
  turnCount: number
  stageLabel: string
  sessionId: string | null
  showBackButton?: boolean
}>()

defineEmits<{
  (e: 'new-session'): void
  (e: 'show-history'): void
  (e: 'show-dashboard'): void
  (e: 'back'): void
}>()
</script>

<template>
  <div class="w-full flex min-h-10 items-center justify-between gap-3">
    
    <div class="flex min-w-0 items-center gap-2 sm:gap-3 shrink-0">
      <div class="w-9 h-9 rounded-xl overflow-hidden shadow-sm border border-zinc-200">
        <img src="/insurespar_logo.png" alt="InsureSpar Logo" class="w-full h-full object-cover" />
      </div>
      <div class="hidden flex-col sm:flex">
        <div class="flex items-center gap-2">
          <span class="text-lg font-bold text-[var(--color-text-primary)] tracking-tight leading-none" style="font-family: 'Felix Titling', serif;">InsureSpar</span>
          <span class="px-1.5 py-0.5 rounded-md bg-[var(--color-surface-muted)] text-[9px] font-bold text-[var(--color-text-secondary)] tracking-widest uppercase">
            Beta
          </span>
        </div>
        <span class="text-[11px] text-[var(--color-text-muted)] font-medium mt-1 leading-none">保险销售对练系统</span>
      </div>
    </div>

    <div class="hidden md:flex flex-1 items-center justify-center gap-3 text-xs">
      
      <div class="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[var(--color-border)] shadow-sm transition-all duration-300">
        <StatusDot :status="status" />
        <RichText :text="statusText" class="text-[var(--color-text-primary)] font-medium truncate max-w-[160px]" />
      </div>

      <div v-if="turnCount > 0" class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--color-surface)] border border-[var(--color-border-light)] text-[var(--color-text-secondary)] font-medium animate-fade-in">
        <span>回合</span>
        <span class="text-[var(--color-text-primary)] font-bold tabular-nums">{{ turnCount }}</span>
      </div>

      <details v-if="sessionId" class="group/session relative animate-fade-in">
        <summary class="flex cursor-pointer list-none items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-white px-3 py-1.5 font-medium text-[var(--color-text-secondary)] shadow-sm transition-colors hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/30">
          <Icon icon="lucide:info" class="h-3.5 w-3.5" />
          会话信息
          <Icon icon="lucide:chevron-down" class="h-3 w-3 transition-transform group-open/session:rotate-180" />
        </summary>
        <div class="absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-lg border border-[var(--color-border)] bg-white p-3 shadow-lg">
          <div class="flex items-start gap-2.5">
            <Icon icon="lucide:route" class="mt-0.5 h-3.5 w-3.5 shrink-0 text-zinc-400" />
            <div class="min-w-0">
              <p class="text-[11px] text-zinc-400">当前训练阶段</p>
              <RichText :text="stageLabel" class="mt-0.5 block truncate text-xs font-medium text-zinc-700" />
            </div>
          </div>
          <details class="group/hash mt-2 border-t border-zinc-100 pt-2">
            <summary class="flex cursor-pointer list-none items-center gap-2 text-[11px] text-zinc-400 hover:text-zinc-600">
              <Icon icon="lucide:hash" class="h-3.5 w-3.5" />
              查看会话 Hash
              <Icon icon="lucide:chevron-right" class="ml-auto h-3 w-3 transition-transform group-open/hash:rotate-90" />
            </summary>
            <code class="mt-2 block break-all rounded-md bg-zinc-50 px-2 py-1.5 text-[10px] text-zinc-500">{{ sessionId }}</code>
          </details>
        </div>
      </details>
    </div>

    <div class="flex items-center gap-1.5 sm:gap-2 xl:gap-3 shrink-0">
      <button
        v-if="showBackButton"
        aria-label="返回对练"
        title="返回对练"
        class="flex items-center gap-1.5 px-3 xl:px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all shadow-sm active:scale-[0.98]"
        @click="$emit('back')"
      >
        <Icon icon="lucide:arrow-left" class="w-4 h-4 opacity-70" />
        <span class="hidden xl:inline">返回对练</span>
      </button>

      <button
        aria-label="打开个人中心"
        title="个人中心"
        class="flex items-center gap-1.5 px-3 xl:px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all shadow-sm active:scale-[0.98]"
        @click="$emit('show-dashboard')"
      >
        <Icon icon="lucide:circle-user-round" class="w-4 h-4 opacity-70" />
        <span class="hidden xl:inline">个人中心</span>
      </button>

      <button
        aria-label="打开历史记录"
        title="历史记录"
        class="flex items-center gap-1.5 px-3 xl:px-4 py-2 rounded-xl border border-[var(--color-border)] bg-white text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all shadow-sm active:scale-[0.98]"
        @click="$emit('show-history')"
      >
        <Icon icon="lucide:history" class="w-4 h-4 opacity-70" />
        <span class="hidden lg:inline">历史</span>
      </button>

      <button
        aria-label="创建新对练"
        title="新对练"
        class="cta-btn gap-1.5 px-3 sm:px-4 xl:px-5"
        @click="$emit('new-session')"
      >
        <Icon icon="lucide:message-square-plus" class="w-4 h-4" />
        <span class="hidden sm:inline">新对练</span>
      </button>
    </div>

  </div>
</template>
